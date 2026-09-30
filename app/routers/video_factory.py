from fastapi import APIRouter, UploadFile
import uuid
import os

from app.services.video_factory.pipeline import process_pdf_video

router = APIRouter()

UPLOAD_DIR = "/tmp/iffiu_video"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/generate-video")
async def generate_video(file: UploadFile):

    job_id = str(uuid.uuid4())
    path = f"{UPLOAD_DIR}/{job_id}.pdf"

    with open(path, "wb") as f:
        f.write(await file.read())

    video = process_pdf_video(path)

    return {"job_id": job_id, "video": video}
