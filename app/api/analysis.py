from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import uuid, os
from app.core.database import get_db
from app.core.config import settings
from app.models.models import User, Creative, RekognitionResult, PersonaResult, KampaScore, Persona
from app.api.auth import get_current_user
from app.services.aws_service import aws_service
from app.services.scoring_engine import calculate_persona_scores

router = APIRouter()

@router.post("/analyze/upload")
async def upload_and_analyze(file:UploadFile=File(...), title:str=Form(""), user:User=Depends(get_current_user), db:Session=Depends(get_db)):
    if user.analyses_used >= user.analyses_limit:
        raise HTTPException(403, f"Limit reached ({user.analyses_limit}). Upgrade your plan.")
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported: {ext}")
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_MB*1024*1024:
        raise HTTPException(400, f"Too large (max {settings.MAX_UPLOAD_MB}MB)")
    media_type = "video" if ext in [".mp4",".mov",".mxf",".avi"] else "image"
    s3_key = f"iffiu/{user.id}/{uuid.uuid4().hex}{ext}"
    bucket = settings.KAMPA_UPLOAD_BUCKET
    aws_service.upload_to_s3(contents, s3_key, file.content_type or "application/octet-stream")
    creative = Creative(user_id=user.id,title=title or file.filename,filename=file.filename,media_type=media_type,s3_key=s3_key,s3_bucket=bucket,file_size_bytes=len(contents),analysis_status="processing")
    db.add(creative); db.commit(); db.refresh(creative)
    try:
        result = aws_service.analyze_image(bucket,s3_key) if media_type=="image" else aws_service.analyze_video_direct(bucket,s3_key)
        rekog = RekognitionResult(creative_id=creative.id,attention_score=result.get("attention_score"),brand_score=result.get("brand_score"),combined_score=result.get("combined_score"),risk_level=result.get("risk_level"),face_count=result.get("face_count",0),face_frame_count=result.get("face_frame_count",0),total_frames=result.get("total_frames",0),dominant_emotion=result.get("dominant_emotion"),emotion_confidence=result.get("emotion_confidence"),top_labels=result.get("top_labels",[]),top_emotions=result.get("top_emotions",[]),detected_text=result.get("detected_text",[]),raw_analysis=result)
        db.add(rekog); db.flush()
        calculate_persona_scores(db, creative.id, user.id, result)
        creative.analysis_status="completed"; user.analyses_used+=1; db.commit()
        return {"success":True,"creative_id":creative.id,"status":"completed"}
    except Exception as e:
        creative.analysis_status="failed"; db.commit()
        raise HTTPException(500, str(e))

@router.get("/results/{creative_id}")
async def get_results(creative_id:int, user:User=Depends(get_current_user), db:Session=Depends(get_db)):
    creative = db.query(Creative).filter(Creative.id==creative_id, Creative.user_id==user.id).first()
    if not creative: raise HTTPException(404, "Not found")
    rekog = db.query(RekognitionResult).filter(RekognitionResult.creative_id==creative_id).order_by(RekognitionResult.created_at.desc()).first()
    ks = db.query(KampaScore).filter(KampaScore.creative_id==creative_id).first()
    prs = db.query(PersonaResult, Persona).join(Persona, PersonaResult.persona_id==Persona.id).filter(PersonaResult.creative_id==creative_id).order_by(PersonaResult.combined_score.desc()).all()
    return {
        "creative":{"id":creative.id,"title":creative.title,"media_type":creative.media_type,"status":creative.analysis_status},
        "rekognition":{"attention_score":rekog.attention_score,"brand_score":rekog.brand_score,"combined_score":rekog.combined_score,"risk_level":rekog.risk_level,"dominant_emotion":rekog.dominant_emotion,"top_labels":rekog.top_labels or [],"top_emotions":rekog.top_emotions or [],"detected_text":rekog.detected_text or []} if rekog else None,
        "overall":{"score":ks.overall_score,"risk_level":ks.risk_level,"trust_avg":ks.trust_avg,"clarity_avg":ks.clarity_avg,"emotion_avg":ks.emotion_avg,"action_avg":ks.action_avg} if ks else None,
        "personas":[{"name":p.name,"slug":p.slug,"emoji":p.avatar_emoji,"color":p.color_hex,"age_range":p.age_range,"trust":pr.trust_score,"clarity":pr.clarity_score,"emotion":pr.emotion_score,"action":pr.action_score,"combined":pr.combined_score,"reasoning":pr.reasoning,"tradition_score":p.tradition_score,"status_score":p.status_score} for pr,p in prs],
    }

@router.get("/creatives")
async def list_creatives(user:User=Depends(get_current_user), db:Session=Depends(get_db)):
    rows = db.query(Creative, KampaScore).outerjoin(KampaScore, Creative.id==KampaScore.creative_id).filter(Creative.user_id==user.id).order_by(Creative.created_at.desc()).all()
    return [{"id":c.id,"title":c.title,"media_type":c.media_type,"status":c.analysis_status,"created_at":str(c.created_at),"score":ks.overall_score if ks else None,"risk":ks.risk_level if ks else None} for c,ks in rows]
