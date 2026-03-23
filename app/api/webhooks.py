"""
IFFIU Webhooks — Lambda callbacks & Stripe payment events
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import Creative, RekognitionResult
from app.services.scoring_engine import calculate_persona_scores

router = APIRouter()


@router.post("/lambda-callback")
async def lambda_callback(request: Request):
    """Receive results from KAMPA predict Lambda (async video analysis)"""
    data = await request.json()
    
    creative_id = data.get("creative_id")
    if not creative_id:
        raise HTTPException(400, "Missing creative_id")
    
    db = SessionLocal()
    try:
        creative = db.query(Creative).filter(Creative.id == creative_id).first()
        if not creative:
            raise HTTPException(404, "Creative not found")
        
        if data.get("status") == "COMPLETED":
            scores = data.get("scores", {})
            rekog = RekognitionResult(
                creative_id=creative_id,
                attention_score=scores.get("attention_score"),
                brand_score=scores.get("brand_score"),
                combined_score=scores.get("combined_score"),
                risk_level=scores.get("risk_level"),
                face_count=scores.get("face_count", 0),
                face_frame_count=scores.get("face_frame_count", 0),
                total_frames=scores.get("total_frames", 0),
                dominant_emotion=scores.get("dominant_emotion"),
                emotion_confidence=scores.get("emotion_confidence"),
                top_labels=scores.get("top_labels", []),
                top_emotions=scores.get("top_emotions", []),
                detected_text=scores.get("detected_text", []),
                raw_analysis=scores,
            )
            db.add(rekog)
            db.flush()
            
            calculate_persona_scores(db, creative_id, creative.user_id, scores)
            creative.analysis_status = "completed"
        else:
            creative.analysis_status = "failed"
        
        db.commit()
        return {"status": "ok"}
    finally:
        db.close()


@router.post("/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe payment events"""
    # TODO: Implement Stripe webhook handling
    return {"status": "ok"}
