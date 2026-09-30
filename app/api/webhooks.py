from fastapi import APIRouter, Request, HTTPException
from app.core.database import SessionLocal
from app.models.models import Creative, RekognitionResult
from app.services.scoring_engine import calculate_persona_scores

router = APIRouter()

@router.post("/lambda-callback")
async def lambda_callback(request: Request):
    data = await request.json()
    cid = data.get("creative_id")
    if not cid: raise HTTPException(400, "Missing creative_id")
    db = SessionLocal()
    try:
        c = db.query(Creative).filter(Creative.id==cid).first()
        if not c: raise HTTPException(404, "Not found")
        if data.get("status")=="COMPLETED":
            s = data.get("scores",{})
            db.add(RekognitionResult(creative_id=cid,attention_score=s.get("attention_score"),brand_score=s.get("brand_score"),combined_score=s.get("combined_score"),risk_level=s.get("risk_level"),top_labels=s.get("top_labels",[]),top_emotions=s.get("top_emotions",[]),detected_text=s.get("detected_text",[]),raw_analysis=s))
            db.flush()
            calculate_persona_scores(db, cid, c.user_id, s)
            c.analysis_status="completed"
        else:
            c.analysis_status="failed"
        db.commit()
        return {"status":"ok"}
    finally:
        db.close()

@router.post("/stripe")
async def stripe_webhook(request: Request):
    return {"status":"ok"}
