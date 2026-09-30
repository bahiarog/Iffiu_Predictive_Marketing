"""Analysis API — Trigger Rekognition + process results"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_paid_or_trial, get_current_user, require_admin
from app.services.aws_service import trigger_analysis, run_rekognition_image
from app.services.scoring_engine import run_scoring
from app.models.models import Creative, RekognitionResult, User
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/analyze/{creative_id}")
async def trigger_analyze(
    creative_id: int,
    user=Depends(require_paid_or_trial),
    db: Session = Depends(get_db),
):
    """Trigger AI analysis for a creative"""
    creative = db.query(Creative).filter(Creative.id == creative_id, Creative.user_id == user.id).first()
    if not creative:
        raise HTTPException(404, "Creative not found")
    if not creative.s3_key:
        raise HTTPException(400, "No file uploaded for this creative")

    creative.analysis_status = "processing"
    db.commit()

    try:
        if creative.media_type in ("image", "banner"):
            # Direct Rekognition for images
            rek_data = run_rekognition_image(creative.s3_key)
            _save_rekognition_result(db, creative, rek_data)
            scoring = run_scoring(db, creative.id, user.id)
            creative.analysis_status = "completed"
            # Increment usage
            user_obj = db.query(User).filter(User.id == user.id).first()
            if user_obj:
                user_obj.analyses_used = (user_obj.analyses_used or 0) + 1
            db.commit()
            return {"success": True, "creative_id": creative.id, "mode": "direct", "score": scoring}
        else:
            # Video: trigger Step Functions
            result = trigger_analysis(creative.id, creative.s3_key, creative.media_type)
            db.commit()
            return {"success": True, "creative_id": creative.id, "mode": "async", **result}
    except Exception as e:
        creative.analysis_status = "failed"
        db.commit()
        logger.error(f"Analysis failed for {creative_id}: {e}")
        raise HTTPException(500, f"Analysis failed: {str(e)}")

@router.post("/analyze/webhook")
async def analysis_webhook(data: dict, db: Session = Depends(get_db)):
    """Webhook called by Lambda/SQS with Rekognition results"""
    creative_id = data.get("creative_id")
    status = data.get("status", "").upper()

    if not creative_id:
        raise HTTPException(400, "Missing creative_id")

    creative = db.query(Creative).filter(Creative.id == creative_id).first()
    if not creative:
        raise HTTPException(404, "Creative not found")

    if status == "COMPLETED":
        _save_rekognition_result(db, creative, data)
        scoring = run_scoring(db, creative.id, creative.user_id)
        creative.analysis_status = "completed"
        # Increment usage
        user_obj = db.query(User).filter(User.id == creative.user_id).first()
        if user_obj:
            user_obj.analyses_used = (user_obj.analyses_used or 0) + 1
    elif status == "FAILED":
        creative.analysis_status = "failed"
    else:
        creative.analysis_status = "processing"

    db.commit()
    return {"success": True, "creative_id": creative_id, "status": status}

@router.get("/results/{creative_id}")
async def get_results(creative_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get analysis results for a creative"""
    creative = db.query(Creative).filter(Creative.id == creative_id, Creative.user_id == user.id).first()
    if not creative:
        raise HTTPException(404, "Creative not found")

    from app.models.models import KampaScore, PersonaResult, Persona
    ks = db.query(KampaScore).filter(KampaScore.creative_id == creative_id).first()
    if not ks:
        return {"success": True, "has_results": False, "status": creative.analysis_status}

    prs = db.query(PersonaResult, Persona).join(Persona).filter(PersonaResult.creative_id == creative_id).all()
    persona_data = []
    for pr, p in prs:
        persona_data.append({
            "persona_name": p.name, "persona_slug": p.slug, "avatar_url": p.avatar_url,
            "avatar_emoji": p.avatar_emoji, "age_range": p.age_range, "income_level": p.income_level,
            "trust_score": pr.trust_score, "clarity_score": pr.clarity_score,
            "emotion_score": pr.emotion_score, "action_score": pr.action_score,
            "combined_score": pr.combined_score, "risk_level": pr.risk_level,
        })

    rek = db.query(RekognitionResult).filter(RekognitionResult.creative_id == creative_id).first()

    return {
        "success": True, "has_results": True, "status": "completed",
        "overall_score": ks.overall_score, "risk_level": ks.risk_level,
        "dimensions": {"trust_avg": ks.trust_avg, "clarity_avg": ks.clarity_avg, "emotion_avg": ks.emotion_avg, "action_avg": ks.action_avg},
        "persona_count": ks.persona_count,
        "persona_results": persona_data,
        "rekognition": {
            "top_labels": rek.top_labels if rek else [],
            "detected_text": rek.detected_text if rek else [],
            "dominant_emotion": rek.dominant_emotion if rek else None,
            "heatmap_data": rek.heatmap_data if rek else None,
        } if rek else None,
    }

def _save_rekognition_result(db, creative, data):
    existing = db.query(RekognitionResult).filter(RekognitionResult.creative_id == creative.id).first()
    fields = dict(
        attention_score=data.get("attention_score"),
        brand_score=data.get("brand_score"),
        combined_score=data.get("combined_score"),
        risk_level=data.get("risk_level"),
        face_count=data.get("face_count", 0),
        face_frame_count=data.get("face_frame_count", 0),
        text_frame_count=data.get("text_frame_count", 0),
        total_frames=data.get("frames_analyzed", 0),
        dominant_emotion=data.get("dominant_emotion") or data.get("emotion_dominant"),
        emotion_confidence=data.get("emotion_confidence"),
        video_duration_sec=data.get("video_duration_sec"),
        top_labels=data.get("top_labels"),
        detected_text=data.get("detected_text"),
        face_details=data.get("face_details"),
        heatmap_data=data.get("heatmap_data"),
    )
    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
    else:
        existing = RekognitionResult(creative_id=creative.id, **fields)
        db.add(existing)


@router.get("/heatmap/{creative_id}")
async def get_heatmap(creative_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate and return attention heatmap for a creative."""
    creative = db.query(Creative).filter(Creative.id == creative_id, Creative.user_id == user.id).first()
    if not creative:
        raise HTTPException(404, "Creative not found")
    if not creative.s3_key:
        raise HTTPException(400, "No file for this creative")
    if creative.analysis_status != "completed":
        raise HTTPException(400, "Creative must be analyzed first")

    try:
        from app.services.heatmap_service import generate_heatmap
        result = generate_heatmap(creative.s3_key, creative.media_type, creative.id)
        if "error" in result:
            raise HTTPException(500, result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Heatmap failed for {creative_id}: {e}")
        raise HTTPException(500, f"Heatmap generation failed: {str(e)}")
