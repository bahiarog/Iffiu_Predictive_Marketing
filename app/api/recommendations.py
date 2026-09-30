"""Recommendations API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.rec_engine import generate_recommendations
from app.models.models import KampaScore, PersonaResult, Persona

router = APIRouter()

@router.get("/recommendations/{creative_id}")
async def get_recommendations(creative_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    ks = db.query(KampaScore).filter(KampaScore.creative_id == creative_id).first()
    if not ks:
        raise HTTPException(404, "No scores found. Run analysis first.")

    prs = db.query(PersonaResult, Persona).join(Persona).filter(PersonaResult.creative_id == creative_id).all()
    persona_data = [{"persona_name": p.name, "combined_score": pr.combined_score, "avatar_emoji": p.avatar_emoji} for pr, p in prs]

    dims = {"trust_avg": ks.trust_avg, "clarity_avg": ks.clarity_avg, "emotion_avg": ks.emotion_avg, "action_avg": ks.action_avg}
    recs = generate_recommendations(ks.overall_score, dims, persona_data)
    return {"success": True, **recs}
