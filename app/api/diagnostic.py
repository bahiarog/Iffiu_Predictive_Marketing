"""System Diagnostic"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.core.security import require_admin
from app.core.config import settings

router = APIRouter()

@router.get("/diagnostic")
async def diagnostic(user=Depends(require_admin), db: Session = Depends(get_db)):
    tables = {}
    for table in ["users", "creatives", "rekognition_results", "personas", "persona_results", "kampa_scores", "ab_tests"]:
        try:
            r = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            tables[table] = r
        except:
            tables[table] = "MISSING"

    return {
        "status": "ok",
        "tables": tables,
        "aws_configured": bool(settings.AWS_ACCESS_KEY_ID),
        "stripe_configured": bool(settings.STRIPE_SECRET_KEY),
        "smtp_configured": bool(settings.SMTP_HOST),
        "sqs_configured": bool(settings.SQS_QUEUE_URL),
    }
