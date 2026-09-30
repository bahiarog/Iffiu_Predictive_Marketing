from fastapi import APIRouter, UploadFile, File
from pypdf import PdfReader
from moviepy.editor import TextClip, concatenate_videoclips
import tempfile

router = APIRouter()

@router.post("/video-from-pdf")
async def video_from_pdf(file: UploadFile = File(...)):

    # save temp pdf
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        pdf_path = tmp.name

    # extract text
    reader = PdfReader(pdf_path)
    text = ""

    for page in reader.pages:
        text += page.extract_text() + "\n"

    # split scenes
    scenes = text.split("\n")[:5]

    clips = []

    for scene in scenes:
        clip = TextClip(scene, fontsize=40, size=(1280,720))
        clip = clip.set_duration(3)
        clips.append(clip)

    video = concatenate_videoclips(clips)

    output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    video.write_videofile(output.name)

    return {"video_path": output.name}
