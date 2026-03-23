"""
IFFIU Analysis API — Upload creatives, trigger AI analysis, get results
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uuid
import os

from app.core.database import get_db
from app.core.config import settings
from app.models.models import User, Creative, RekognitionResult
from app.api.auth import get_current_user
from app.services.aws_service import aws_service
from app.services.scoring_engine import calculate_persona_scores

router = APIRouter()


@router.post("/analyze/upload")
async def upload_and_analyze(
    file: UploadFile = File(...),
    title: str = Form(""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a creative and trigger AI analysis"""
    
    # Check quota
    if user.analyses_used >= user.analyses_limit:
        raise HTTPException(
            status_code=403, 
            detail=f"Analysis limit reached ({user.analyses_limit}). Upgrade your plan."
        )
    
    # Validate file
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {ext}")
    
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large (max {settings.MAX_UPLOAD_MB}MB)")
    
    # Determine media type
    media_type = "video" if ext in [".mp4", ".mov", ".mxf", ".avi"] else "image"
    
    # Upload to S3
    s3_key = f"iffiu/{user.id}/{uuid.uuid4().hex}{ext}"
    bucket = settings.KAMPA_UPLOAD_BUCKET
    aws_service.upload_to_s3(contents, s3_key, file.content_type or "application/octet-stream")
    
    # Create creative record
    creative = Creative(
        user_id=user.id,
        title=title or file.filename,
        filename=file.filename,
        media_type=media_type,
        s3_key=s3_key,
        s3_bucket=bucket,
        file_size_bytes=len(contents),
        analysis_status="processing",
    )
    db.add(creative)
    db.commit()
    db.refresh(creative)
    
    # Run analysis
    try:
        if media_type == "image":
            result = aws_service.analyze_image(bucket, s3_key)
            _save_and_score(db, creative, user, result)
        else:
            result = aws_service.analyze_video_direct(bucket, s3_key)
            _save_and_score(db, creative, user, result)
        
        # Increment usage
        user.analyses_used += 1
        db.commit()
        
        return {"success": True, "creative_id": creative.id, "status": "completed"}
    
    except Exception as e:
        creative.analysis_status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{creative_id}")
async def get_results(
    creative_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get full analysis results for a creative"""
    creative = db.query(Creative).filter(
        Creative.id == creative_id, Creative.user_id == user.id
    ).first()
    
    if not creative:
        raise HTTPException(status_code=404, detail="Creative not found")
    
    # Get Rekognition results
    rekog = db.query(RekognitionResult).filter(
        RekognitionResult.creative_id == creative_id
    ).order_by(RekognitionResult.created_at.desc()).first()
    
    # Get persona scores
    from app.models.models import PersonaResult, KampaScore, Persona
    
    kampa_score = db.query(KampaScore).filter(
        KampaScore.creative_id == creative_id
    ).first()
    
    persona_results = db.query(PersonaResult, Persona).join(
        Persona, PersonaResult.persona_id == Persona.id
    ).filter(
        PersonaResult.creative_id == creative_id
    ).order_by(PersonaResult.combined_score.desc()).all()
    
    return {
        "creative": {
            "id": creative.id, "title": creative.title, "media_type": creative.media_type,
            "filename": creative.filename, "status": creative.analysis_status,
        },
        "rekognition": {
            "attention_score": rekog.attention_score if rekog else None,
            "brand_score": rekog.brand_score if rekog else None,
            "combined_score": rekog.combined_score if rekog else None,
            "risk_level": rekog.risk_level if rekog else None,
            "dominant_emotion": rekog.dominant_emotion if rekog else None,
            "top_labels": rekog.top_labels if rekog else [],
            "top_emotions": rekog.top_emotions if rekog else [],
            "detected_text": rekog.detected_text if rekog else [],
        } if rekog else None,
        "overall": {
            "score": kampa_score.overall_score if kampa_score else None,
            "risk_level": kampa_score.risk_level if kampa_score else None,
            "trust_avg": kampa_score.trust_avg if kampa_score else None,
            "clarity_avg": kampa_score.clarity_avg if kampa_score else None,
            "emotion_avg": kampa_score.emotion_avg if kampa_score else None,
            "action_avg": kampa_score.action_avg if kampa_score else None,
        } if kampa_score else None,
        "personas": [
            {
                "name": p.name, "slug": p.slug, "emoji": p.avatar_emoji,
                "color": p.color_hex, "age_range": p.age_range,
                "trust": pr.trust_score, "clarity": pr.clarity_score,
                "emotion": pr.emotion_score, "action": pr.action_score,
                "combined": pr.combined_score, "reasoning": pr.reasoning,
                "tradition_score": p.tradition_score, "status_score": p.status_score,
            }
            for pr, p in persona_results
        ],
    }


@router.get("/creatives")
async def list_creatives(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all user's creatives with scores"""
    from app.models.models import KampaScore
    
    creatives = db.query(Creative, KampaScore).outerjoin(
        KampaScore, Creative.id == KampaScore.creative_id
    ).filter(
        Creative.user_id == user.id
    ).order_by(Creative.created_at.desc()).all()
    
    return [
        {
            "id": c.id, "title": c.title, "media_type": c.media_type,
            "status": c.analysis_status, "created_at": str(c.created_at),
            "score": ks.overall_score if ks else None,
            "risk": ks.risk_level if ks else None,
        }
        for c, ks in creatives
    ]


def _save_and_score(db: Session, creative: Creative, user: User, result: dict):
    """Save Rekognition results and compute persona scores"""
    rekog = RekognitionResult(
        creative_id=creative.id,
        attention_score=result.get("attention_score"),
        brand_score=result.get("brand_score"),
        combined_score=result.get("combined_score"),
        risk_level=result.get("risk_level"),
        face_count=result.get("face_count", 0),
        face_frame_count=result.get("face_frame_count", 0),
        total_frames=result.get("total_frames", 0),
        dominant_emotion=result.get("dominant_emotion"),
        emotion_confidence=result.get("emotion_confidence"),
        top_labels=result.get("top_labels", []),
        top_emotions=result.get("top_emotions", []),
        detected_text=result.get("detected_text", []),
        raw_analysis=result,
    )
    db.add(rekog)
    db.flush()
    
    # Run persona scoring
    calculate_persona_scores(db, creative.id, user.id, result)
    
    creative.analysis_status = "completed"
    db.commit()
