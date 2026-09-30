"""
IFFIU Attention Heatmap Service
Generates predictive attention heatmaps using Rekognition bounding boxes.
On-demand: re-analyzes the image/frame with bounding box output,
then generates Gaussian attention map.
"""
import io
import json
import time
import logging
import math
from typing import Optional

import numpy as np
from PIL import Image, ImageFilter, ImageDraw

logger = logging.getLogger(__name__)

# ── Attention weights (from KAMPA Attention AI Guide) ──────────
W_FACE = 0.35       # Faces are strongest attention magnet
W_TEXT = 0.20        # Text draws deliberate reading attention
W_LABEL_PERSON = 0.15  # Person/body without face bbox
W_LABEL_OBJECT = 0.10  # Prominent objects
W_CENTER_BIAS = 0.20   # Center bias (proven in eye-tracking research)


def _get_session():
    """Get boto3 session from app settings."""
    import boto3
    from app.core.config import settings
    return boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )


def _download_from_s3(s3_key: str) -> bytes:
    """Download file from S3."""
    from app.core.config import settings
    s3 = _get_session().client("s3")
    resp = s3.get_object(Bucket=settings.S3_BUCKET, Key=s3_key)
    return resp["Body"].read()


def _upload_heatmap_to_s3(data: bytes, creative_id: int) -> str:
    """Upload heatmap PNG to S3, return key."""
    from app.core.config import settings
    s3 = _get_session().client("s3")
    key = f"iffiu/heatmaps/{creative_id}_{int(time.time())}.png"
    s3.put_object(
        Bucket=settings.S3_BUCKET, Key=key,
        Body=data, ContentType="image/png"
    )
    return key


def _get_presigned(key: str) -> str:
    from app.core.config import settings
    s3 = _get_session().client("s3")
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key},
        ExpiresIn=3600
    )


def _run_rekognition_with_boxes(s3_key: str) -> dict:
    """Run Rekognition on image and get bounding boxes."""
    from app.core.config import settings
    rek = _get_session().client("rekognition")
    image_spec = {"S3Object": {"Bucket": settings.S3_BUCKET, "Name": s3_key}}

    faces = rek.detect_faces(Image=image_spec, Attributes=["ALL"])
    labels = rek.detect_labels(Image=image_spec, MinConfidence=60, MaxLabels=30)
    text = rek.detect_text(Image=image_spec)

    return {
        "faces": faces.get("FaceDetails", []),
        "labels": labels.get("Labels", []),
        "text_detections": [t for t in text.get("TextDetections", []) if t["Type"] == "LINE"],
    }


def _extract_video_frame(video_bytes: bytes, second: int = 2) -> bytes:
    """Extract a single frame from video using ffmpeg."""
    import subprocess
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as vf:
        vf.write(video_bytes)
        vf_path = vf.name

    out_path = vf_path + ".jpg"
    try:
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(second), "-i", vf_path,
            "-frames:v", "1", "-q:v", "2", out_path
        ], capture_output=True, timeout=30)

        if os.path.exists(out_path):
            with open(out_path, "rb") as f:
                return f.read()
    finally:
        for p in [vf_path, out_path]:
            try:
                os.unlink(p)
            except:
                pass
    return None


def _get_video_duration(video_bytes: bytes) -> float:
    """Get video duration in seconds."""
    import subprocess
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as vf:
        vf.write(video_bytes)
        vf_path = vf.name
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", vf_path
        ], capture_output=True, text=True, timeout=15)
        return float(result.stdout.strip())
    except Exception:
        return 30.0  # default
    finally:
        try: os.unlink(vf_path)
        except: pass


def _extract_keyframes(video_bytes: bytes, num_frames: int = 8) -> list:
    """Extract evenly-spaced keyframes from video. Returns list of (second, jpeg_bytes)."""
    duration = _get_video_duration(video_bytes)
    if duration <= 0:
        duration = 30.0

    # Distribute frames evenly, skip first 0.5s and last 0.5s
    start = min(0.5, duration * 0.05)
    end = max(duration - 0.5, duration * 0.95)
    interval = (end - start) / max(num_frames - 1, 1)

    frames = []
    for i in range(num_frames):
        sec = round(start + i * interval, 1)
        if sec >= duration:
            sec = max(0, duration - 0.5)
        frame_data = _extract_video_frame(video_bytes, second=int(sec))
        if frame_data:
            frames.append((sec, frame_data))

    logger.info(f"[Heatmap] Extracted {len(frames)} keyframes from {duration:.1f}s video")
    return frames


def _analyze_single_frame(frame_bytes: bytes, creative_id: int, frame_idx: int) -> dict:
    """Run Rekognition + heatmap generation on a single frame. Returns analysis dict."""
    from app.core.config import settings
    import io

    img = Image.open(io.BytesIO(frame_bytes)).convert("RGB")
    img_w, img_h = img.size

    # Upload frame to S3 for Rekognition
    s3 = _get_session().client("s3")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    buf.seek(0)
    frame_key = f"iffiu/heatmaps/frame_{creative_id}_{frame_idx}_{int(time.time())}.jpg"
    s3.put_object(Bucket=settings.S3_BUCKET, Key=frame_key, Body=buf.getvalue(), ContentType="image/jpeg")

    # Run Rekognition
    rek_data = _run_rekognition_with_boxes(frame_key)

    # Build heatmap
    heatmap = np.zeros((img_h, img_w), dtype=np.float64)

    n_faces = len(rek_data["faces"])
    n_text = len(rek_data["text_detections"])
    brand_visible = False
    brand_keywords = ["ionos", "strato", "1&1", "gmx", "web.de"]

    # Center bias
    _add_gaussian_blob(heatmap, img_w // 2, img_h // 2,
                       max(img_w, img_h) // 3, W_CENTER_BIAS)

    # Faces
    for face in rek_data["faces"]:
        bb = face["BoundingBox"]
        cx = int((bb["Left"] + bb["Width"] / 2) * img_w)
        cy = int((bb["Top"] + bb["Height"] / 2) * img_h)
        size = int(max(bb["Width"] * img_w, bb["Height"] * img_h))
        sigma = max(size // 2, 30)
        _add_gaussian_blob(heatmap, cx, cy, sigma, W_FACE)

    # Text
    for td in rek_data["text_detections"]:
        bb = td["Geometry"]["BoundingBox"]
        cx = int((bb["Left"] + bb["Width"] / 2) * img_w)
        cy = int((bb["Top"] + bb["Height"] / 2) * img_h)
        size = int(max(bb["Width"] * img_w, bb["Height"] * img_h))
        sigma = max(size // 2, 20)
        _add_gaussian_blob(heatmap, cx, cy, sigma, W_TEXT)
        if any(b in td["DetectedText"].lower() for b in brand_keywords):
            brand_visible = True

    # Labels with bounding boxes
    person_labels = {"person", "people", "human", "man", "woman", "adult", "child"}
    for label in rek_data["labels"]:
        for instance in label.get("Instances", []):
            bb = instance.get("BoundingBox")
            if not bb:
                continue
            cx = int((bb["Left"] + bb["Width"] / 2) * img_w)
            cy = int((bb["Top"] + bb["Height"] / 2) * img_h)
            size = int(max(bb["Width"] * img_w, bb["Height"] * img_h))
            sigma = max(size // 3, 25)
            w = W_LABEL_PERSON if label["Name"].lower() in person_labels else W_LABEL_OBJECT
            _add_gaussian_blob(heatmap, cx, cy, sigma, w)

    # Normalize + colorize
    if heatmap.max() > 0:
        heatmap = heatmap / heatmap.max()

    from PIL import ImageFilter
    heatmap_img = Image.fromarray((heatmap * 255).astype(np.uint8), mode="L")
    heatmap_img = heatmap_img.filter(ImageFilter.GaussianBlur(radius=max(img_w, img_h) // 40))
    heatmap_np = np.array(heatmap_img).astype(np.float64) / 255.0

    overlay = _vectorized_jet(heatmap_np)
    overlay_img = Image.fromarray(overlay, mode="RGBA")
    base = img.convert("RGBA")
    composite = Image.alpha_composite(base, overlay_img)

    # Upload composite
    buf2 = io.BytesIO()
    composite.convert("RGB").save(buf2, format="PNG", optimize=True)
    buf2.seek(0)
    hm_key = _upload_heatmap_to_s3(buf2.getvalue(), creative_id)
    hm_url = _get_presigned(hm_key)

    # Attention score for this frame
    frame_score = 30
    frame_score += min(n_faces * 15, 30)
    if 1 <= n_text <= 4:
        frame_score += 15
    elif n_text > 4:
        frame_score += 5
    if brand_visible:
        frame_score += 10
    center_region = heatmap_np[img_h//4:3*img_h//4, img_w//4:3*img_w//4]
    if center_region.mean() > 0.3:
        frame_score += 10
    frame_score = min(frame_score, 100)

    # Dominant emotion from faces
    dom_emotion = None
    if rek_data["faces"]:
        emotions = rek_data["faces"][0].get("Emotions", [])
        if emotions:
            emotions_sorted = sorted(emotions, key=lambda e: e["Confidence"], reverse=True)
            dom_emotion = emotions_sorted[0]["Type"]

    return {
        "heatmap_url": hm_url,
        "attention_score": frame_score,
        "face_count": n_faces,
        "text_count": n_text,
        "brand_visible": brand_visible,
        "dominant_emotion": dom_emotion,
    }


def generate_video_heatmap(s3_key: str, creative_id: int, num_frames: int = 8) -> dict:
    """Generate attention heatmap gallery for a video with timeline."""
    logger.info(f"[Heatmap] Video analysis starting for creative {creative_id} ({num_frames} frames)")

    raw_data = _download_from_s3(s3_key)
    duration = _get_video_duration(raw_data)
    keyframes = _extract_keyframes(raw_data, num_frames=num_frames)

    if not keyframes:
        return {"error": "Could not extract frames from video"}

    frames_data = []
    total_attention = 0
    total_faces = 0
    total_text = 0
    brand_seen = False
    insights = []

    for idx, (sec, frame_bytes) in enumerate(keyframes):
        logger.info(f"[Heatmap] Analyzing frame {idx+1}/{len(keyframes)} at {sec}s")
        try:
            analysis = _analyze_single_frame(frame_bytes, creative_id, idx)
            analysis["second"] = sec
            analysis["frame_index"] = idx
            frames_data.append(analysis)

            total_attention += analysis["attention_score"]
            total_faces += analysis["face_count"]
            total_text += analysis["text_count"]
            if analysis["brand_visible"]:
                brand_seen = True
        except Exception as e:
            logger.error(f"[Heatmap] Frame {idx} failed: {e}")
            continue

    if not frames_data:
        return {"error": "All frame analyses failed"}

    n = len(frames_data)
    avg_attention = round(total_attention / n, 1)

    # Build timeline data
    timeline = []
    for f in frames_data:
        timeline.append({
            "second": f["second"],
            "attention": f["attention_score"],
            "faces": f["face_count"],
            "text": f["text_count"],
            "brand": f["brand_visible"],
            "emotion": f.get("dominant_emotion"),
        })

    # Generate insights
    # Peak attention
    peak = max(frames_data, key=lambda f: f["attention_score"])
    low = min(frames_data, key=lambda f: f["attention_score"])
    insights.append(f"Peak Attention bei Sekunde {peak['second']:.0f} (Score: {peak['attention_score']})")
    if low["attention_score"] < avg_attention - 10:
        insights.append(f"Schwachstelle bei Sekunde {low['second']:.0f} (Score: {low['attention_score']}) — prüfen")

    # Brand timing
    brand_frames = [f for f in frames_data if f["brand_visible"]]
    if brand_frames:
        first_brand = brand_frames[0]["second"]
        if first_brand > duration * 0.5:
            insights.append(f"Marke erscheint erst bei Sekunde {first_brand:.0f} — zu spät im Video")
        else:
            insights.append(f"Marke ab Sekunde {first_brand:.0f} sichtbar — gutes Brand Timing")
    else:
        insights.append("Kein Markenname im Video erkannt — Brand Visibility prüfen")

    # Face presence
    face_frames = [f for f in frames_data if f["face_count"] > 0]
    face_pct = round(len(face_frames) / n * 100)
    if face_pct >= 70:
        insights.append(f"Gesichter in {face_pct}% der Szenen — starke emotionale Verbindung")
    elif face_pct >= 30:
        insights.append(f"Gesichter in {face_pct}% der Szenen — moderate Präsenz")
    else:
        insights.append(f"Gesichter nur in {face_pct}% der Szenen — mehr Personen könnten helfen")

    # Attention consistency
    scores = [f["attention_score"] for f in frames_data]
    score_range = max(scores) - min(scores)
    if score_range <= 15:
        insights.append("Gleichmäßige Aufmerksamkeit über das gesamte Video")
    elif score_range >= 35:
        insights.append(f"Starke Schwankungen in der Aufmerksamkeit (Δ{score_range}) — Konsistenz prüfen")

    risk = "low" if avg_attention >= 60 else "medium" if avg_attention >= 35 else "high"

    logger.info(f"[Heatmap] Video done: {n} frames, avg={avg_attention}, risk={risk}")

    return {
        "success": True,
        "creative_id": creative_id,
        "mode": "video",
        "duration": round(duration, 1),
        "frames_analyzed": n,
        "frames": frames_data,
        "timeline": timeline,
        "attention_score": avg_attention,
        "risk_level": risk,
        "total_faces": total_faces,
        "total_text": total_text,
        "brand_visible": brand_seen,
        "insights": insights,
    }


def _add_gaussian_blob(heatmap: np.ndarray, cx: int, cy: int, sigma: int, weight: float):
    """Add a 2D Gaussian blob to the heatmap."""
    h, w = heatmap.shape
    y_range = np.arange(max(0, cy - 3*sigma), min(h, cy + 3*sigma))
    x_range = np.arange(max(0, cx - 3*sigma), min(w, cx + 3*sigma))
    if len(y_range) == 0 or len(x_range) == 0:
        return
    yy, xx = np.meshgrid(y_range, x_range, indexing="ij")
    gaussian = np.exp(-((xx - cx)**2 + (yy - cy)**2) / (2 * sigma**2))
    heatmap[
        max(0, cy - 3*sigma):min(h, cy + 3*sigma),
        max(0, cx - 3*sigma):min(w, cx + 3*sigma)
    ] += gaussian * weight


def generate_heatmap(s3_key: str, media_type: str, creative_id: int) -> dict:
    """
    Generate attention heatmap for a creative.
    For video: multi-frame gallery + timeline.
    For image: single heatmap.
    """
    logger.info(f"[Heatmap] Generating for creative {creative_id}, type={media_type}")

    # Video: use multi-frame pipeline
    if media_type == "video":
        return generate_video_heatmap(s3_key, creative_id, num_frames=8)

    # Image: single frame analysis
    raw_data = _download_from_s3(s3_key)
    img = Image.open(io.BytesIO(raw_data)).convert("RGB")

    img_w, img_h = img.size
    logger.info(f"[Heatmap] Image size: {img_w}x{img_h}")

    # ── 2. Run Rekognition on image ──────────────────────────
    rek_data = _run_rekognition_with_boxes(s3_key)

    # ── 3. Build attention heatmap ─────────────────────────────
    heatmap = np.zeros((img_h, img_w), dtype=np.float64)

    insights = []
    face_regions = []
    text_regions = []
    brand_in_view = False

    # Center bias
    _add_gaussian_blob(heatmap, img_w // 2, img_h // 2,
                       max(img_w, img_h) // 3, W_CENTER_BIAS)

    # Faces (strongest signal)
    for face in rek_data["faces"]:
        bb = face["BoundingBox"]
        cx = int((bb["Left"] + bb["Width"] / 2) * img_w)
        cy = int((bb["Top"] + bb["Height"] / 2) * img_h)
        size = int(max(bb["Width"] * img_w, bb["Height"] * img_h))
        sigma = max(size // 2, 30)
        _add_gaussian_blob(heatmap, cx, cy, sigma, W_FACE)
        face_regions.append({"x": cx, "y": cy, "w": int(bb["Width"] * img_w), "h": int(bb["Height"] * img_h)})

    n_faces = len(rek_data["faces"])
    if n_faces > 0:
        insights.append(f"{n_faces} Gesicht{'er' if n_faces > 1 else ''} erkannt — starkes Aufmerksamkeitssignal")
    else:
        insights.append("Keine Gesichter erkannt — emotionale Verbindung könnte fehlen")

    # Text regions
    brand_keywords = ["ionos", "strato", "1&1", "gmx", "web.de"]
    for td in rek_data["text_detections"]:
        bb = td["Geometry"]["BoundingBox"]
        cx = int((bb["Left"] + bb["Width"] / 2) * img_w)
        cy = int((bb["Top"] + bb["Height"] / 2) * img_h)
        size = int(max(bb["Width"] * img_w, bb["Height"] * img_h))
        sigma = max(size // 2, 20)
        _add_gaussian_blob(heatmap, cx, cy, sigma, W_TEXT)
        text_regions.append({"text": td["DetectedText"], "x": cx, "y": cy})

        if any(b in td["DetectedText"].lower() for b in brand_keywords):
            brand_in_view = True

    n_text = len(rek_data["text_detections"])
    if n_text == 0:
        insights.append("Kein Text erkannt — Botschaft könnte unklar sein")
    elif n_text > 6:
        insights.append(f"{n_text} Textelemente erkannt — möglicherweise zu überladen")
    else:
        insights.append(f"{n_text} Textelement{'e' if n_text > 1 else ''} erkannt — gute Lesbarkeit")

    if brand_in_view:
        insights.append("Markenname sichtbar — gute Brand Visibility")
    else:
        insights.append("Kein Markenname erkannt — Brand Visibility prüfen")

    # Labels with bounding boxes
    person_labels = {"person", "people", "human", "man", "woman", "adult", "child"}
    for label in rek_data["labels"]:
        for instance in label.get("Instances", []):
            bb = instance.get("BoundingBox")
            if not bb:
                continue
            cx = int((bb["Left"] + bb["Width"] / 2) * img_w)
            cy = int((bb["Top"] + bb["Height"] / 2) * img_h)
            size = int(max(bb["Width"] * img_w, bb["Height"] * img_h))
            sigma = max(size // 3, 25)
            w = W_LABEL_PERSON if label["Name"].lower() in person_labels else W_LABEL_OBJECT
            _add_gaussian_blob(heatmap, cx, cy, sigma, w)

    # ── 4. Normalize and colorize ─────────────────────────────
    if heatmap.max() > 0:
        heatmap = heatmap / heatmap.max()

    # Apply slight blur for smoother look
    heatmap_img = Image.fromarray((heatmap * 255).astype(np.uint8), mode="L")
    heatmap_img = heatmap_img.filter(ImageFilter.GaussianBlur(radius=max(img_w, img_h) // 40))
    heatmap_np = np.array(heatmap_img).astype(np.float64) / 255.0

    # Create RGBA heatmap overlay with vectorized jet colormap
    overlay = _vectorized_jet(heatmap_np)

    # ── 5. Composite ──────────────────────────────────────────
    overlay_img = Image.fromarray(overlay, mode="RGBA")
    base = img.convert("RGBA")
    composite = Image.alpha_composite(base, overlay_img)

    # ── 6. Save and upload ────────────────────────────────────
    buf = io.BytesIO()
    composite.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    heatmap_key = _upload_heatmap_to_s3(buf.getvalue(), creative_id)
    heatmap_url = _get_presigned(heatmap_key)

    # ── 7. Calculate attention score ──────────────────────────
    # Score based on: face presence, text clarity, brand visibility
    attention_score = 30  # base
    attention_score += min(n_faces * 15, 30)  # faces: up to 30
    if 1 <= n_text <= 4:
        attention_score += 15
    elif n_text > 4:
        attention_score += 5
    if brand_in_view:
        attention_score += 10
    # Center concentration bonus
    center_region = heatmap_np[img_h//4:3*img_h//4, img_w//4:3*img_w//4]
    if center_region.mean() > 0.3:
        attention_score += 10
    attention_score = min(attention_score, 100)

    risk = "low" if attention_score >= 65 else "medium" if attention_score >= 40 else "high"

    logger.info(f"[Heatmap] Done for creative {creative_id}: score={attention_score}")

    return {
        "success": True,
        "creative_id": creative_id,
        "heatmap_url": heatmap_url,
        "attention_score": attention_score,
        "risk_level": risk,
        "insights": insights,
        "face_count": n_faces,
        "text_count": n_text,
        "brand_visible": brand_in_view,
    }


def _vectorized_jet(heatmap_np: np.ndarray) -> np.ndarray:
    """Vectorized jet colormap: heatmap (H,W) float64 -> (H,W,4) uint8 RGBA."""
    h, w = heatmap_np.shape
    v = heatmap_np.clip(0, 1)

    r = np.zeros_like(v)
    g = np.zeros_like(v)
    b = np.zeros_like(v)

    # Blue to Cyan (0 - 0.25)
    m = v < 0.25
    r[m] = 0; g[m] = v[m] * 4 * 255; b[m] = 255

    # Cyan to Green (0.25 - 0.5)
    m = (v >= 0.25) & (v < 0.5)
    r[m] = 0; g[m] = 255; b[m] = (0.5 - v[m]) * 4 * 255

    # Green to Yellow (0.5 - 0.75)
    m = (v >= 0.5) & (v < 0.75)
    r[m] = (v[m] - 0.5) * 4 * 255; g[m] = 255; b[m] = 0

    # Yellow to Red (0.75 - 1.0)
    m = v >= 0.75
    r[m] = 255; g[m] = (1.0 - v[m]) * 4 * 255; b[m] = 0

    alpha = np.minimum(v * 180, 160).astype(np.uint8)
    alpha[v < 0.05] = 0

    overlay = np.stack([
        r.clip(0, 255).astype(np.uint8),
        g.clip(0, 255).astype(np.uint8),
        b.clip(0, 255).astype(np.uint8),
        alpha
    ], axis=-1)

    return overlay


def _jet_color(v: float):
    """Convert 0-1 value to jet-like RGB colormap (kept for reference)."""
    if v < 0.25:
        r, g, b = 0, int(v * 4 * 255), 255
    elif v < 0.5:
        r, g, b = 0, 255, int((0.5 - v) * 4 * 255)
    elif v < 0.75:
        r, g, b = int((v - 0.5) * 4 * 255), 255, 0
    else:
        r, g, b = 255, int((1.0 - v) * 4 * 255), 0
    return min(255, max(0, r)), min(255, max(0, g)), min(255, max(0, b))
