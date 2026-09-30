"""A/B Testing API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import ABTest, KampaScore, Creative

router = APIRouter()

class ABTestRequest(BaseModel):
    name: str = ""
    creative_a_id: int
    creative_b_id: int

@router.post("/ab-test")
async def create_ab_test(req: ABTestRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    for cid in [req.creative_a_id, req.creative_b_id]:
        c = db.query(Creative).filter(Creative.id == cid, Creative.user_id == user.id).first()
        if not c:
            raise HTTPException(404, f"Creative {cid} not found")

    score_a = db.query(KampaScore).filter(KampaScore.creative_id == req.creative_a_id).first()
    score_b = db.query(KampaScore).filter(KampaScore.creative_id == req.creative_b_id).first()

    if not score_a or not score_b:
        raise HTTPException(400, "Both creatives must be analyzed first")

    winner = "A" if score_a.overall_score >= score_b.overall_score else "B"
    diff = abs(score_a.overall_score - score_b.overall_score)

    comparison = {
        "A": {"score": score_a.overall_score, "trust": score_a.trust_avg, "clarity": score_a.clarity_avg, "emotion": score_a.emotion_avg, "action": score_a.action_avg},
        "B": {"score": score_b.overall_score, "trust": score_b.trust_avg, "clarity": score_b.clarity_avg, "emotion": score_b.emotion_avg, "action": score_b.action_avg},
        "difference": round(diff, 1),
        "significant": diff > 5,
    }

    test = ABTest(
        user_id=user.id, name=req.name or f"Test {req.creative_a_id} vs {req.creative_b_id}",
        creative_a_id=req.creative_a_id, creative_b_id=req.creative_b_id,
        winner=winner, score_a=score_a.overall_score, score_b=score_b.overall_score,
        comparison_data=comparison,
    )
    db.add(test)
    db.commit()
    db.refresh(test)

    return {"success": True, "test_id": test.id, "winner": winner, "comparison": comparison}

@router.get("/ab-tests")
async def list_ab_tests(user=Depends(get_current_user), db: Session = Depends(get_db)):
    tests = db.query(ABTest).filter(ABTest.user_id == user.id).order_by(ABTest.created_at.desc()).all()
    return {"success": True, "tests": [{"id": t.id, "name": t.name, "winner": t.winner, "score_a": t.score_a, "score_b": t.score_b, "created_at": str(t.created_at)} for t in tests]}
