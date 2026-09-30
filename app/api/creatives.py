"""Creatives API"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from fastapi import HTTPException
from app.models.models import Creative, KampaScore
from app.services.aws_service import get_presigned_url

router = APIRouter()

@router.get("/creatives")
async def list_creatives(user=Depends(get_current_user), db: Session = Depends(get_db)):
    creatives = db.query(Creative).filter(Creative.user_id == user.id).order_by(Creative.created_at.desc()).all()
    result = []
    for c in creatives:
        ks = db.query(KampaScore).filter(KampaScore.creative_id == c.id).first()
        result.append({
            "id": c.id,
            "title": c.title,
            "filename": c.filename,
            "media_type": c.media_type,
            "analysis_status": c.analysis_status,
            "created_at": str(c.created_at),
            "overall_score": ks.overall_score if ks else None,
            "risk_level": ks.risk_level if ks else None,
            "s3_key": c.s3_key,
        })
    return {"success": True, "creatives": result}


@router.get("/preview/{creative_id}")
async def get_preview(creative_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get a presigned S3 URL for creative preview (valid 1 hour)."""
    creative = db.query(Creative).filter(Creative.id == creative_id, Creative.user_id == user.id).first()
    if not creative:
        raise HTTPException(404, "Creative not found")
    if not creative.s3_key:
        raise HTTPException(404, "No file for this creative")
    url = get_presigned_url(creative.s3_key, expires=3600)
    return {
        "success": True,
        "creative_id": creative.id,
        "media_type": creative.media_type,
        "filename": creative.filename,
        "preview_url": url,
    }


@router.delete("/creatives/{creative_id}")
async def delete_creative(creative_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a creative and its associated data."""
    creative = db.query(Creative).filter(Creative.id == creative_id, Creative.user_id == user.id).first()
    if not creative:
        raise HTTPException(404, "Creative not found")

    # Delete associated data
    from app.models.models import RekognitionResult, PersonaResult, KampaScore
    db.query(PersonaResult).filter(PersonaResult.creative_id == creative_id).delete()
    db.query(KampaScore).filter(KampaScore.creative_id == creative_id).delete()
    db.query(RekognitionResult).filter(RekognitionResult.creative_id == creative_id).delete()

    # Delete S3 file
    if creative.s3_key:
        try:
            from app.services.aws_service import _get_session
            from app.core.config import settings
            s3 = _get_session().client("s3")
            s3.delete_object(Bucket=settings.S3_BUCKET, Key=creative.s3_key)
        except Exception:
            pass  # Don't fail if S3 delete fails

    db.delete(creative)
    db.commit()
    return {"success": True, "deleted": creative_id}
