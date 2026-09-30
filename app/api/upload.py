"""Upload API — S3 upload with paywall"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_paid_or_trial
from app.services.aws_service import upload_to_s3
from app.models.models import Creative
import time

router = APIRouter()

@router.post("/upload")
async def upload_creative(
    file: UploadFile = File(...),
    title: str = Form(""),
    media_type: str = Form("video"),
    user=Depends(require_paid_or_trial),
    db: Session = Depends(get_db),
):
    """Upload creative to S3 (protected + paywall)"""
    contents = await file.read()
    max_bytes = 500 * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(400, f"File too large (max 500MB)")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "bin"
    ts = int(time.time())
    s3_key = f"iffiu/{user.id}/{ts}_{file.filename}"

    upload_to_s3(contents, s3_key, file.content_type or "application/octet-stream")

    creative = Creative(
        user_id=user.id,
        title=title or file.filename,
        filename=file.filename,
        media_type=media_type,
        s3_key=s3_key,
        s3_bucket="kampa-qc-assets",
        file_size_bytes=len(contents),
        analysis_status="uploaded",
    )
    db.add(creative)
    db.commit()
    db.refresh(creative)

    return {"success": True, "creative_id": creative.id, "s3_key": s3_key, "filename": file.filename}
