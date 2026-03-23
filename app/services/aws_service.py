"""
IFFIU AWS Service — Connects to existing KAMPA Rekognition/Lambda infrastructure
Uses the same AWS account (754840114791) in eu-central-1
"""

import boto3
import json
import time
from typing import Optional
from app.core.config import settings


class AWSService:
    """Interface to KAMPA's existing AWS infrastructure"""
    
    def __init__(self):
        session_kwargs = {"region_name": settings.AWS_REGION}
        if settings.AWS_ACCESS_KEY_ID:
            session_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            session_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
        
        self.session = boto3.Session(**session_kwargs)
        self.rekognition = self.session.client("rekognition")
        self.s3 = self.session.client("s3")
        self.lambda_client = self.session.client("lambda")
    
    # ─── Direct Rekognition Analysis (for images) ────────────────────────
    
    def analyze_image(self, bucket: str, key: str) -> dict:
        """Analyze a single image with Rekognition (labels, faces, text, moderation)"""
        image_ref = {"S3Object": {"Bucket": bucket, "Name": key}}
        
        labels = self.rekognition.detect_labels(
            Image=image_ref, MaxLabels=30, MinConfidence=settings.REKOGNITION_MIN_CONFIDENCE
        )
        faces = self.rekognition.detect_faces(
            Image=image_ref, Attributes=["ALL"]
        )
        text = self.rekognition.detect_text(Image=image_ref)
        moderation = self.rekognition.detect_moderation_labels(
            Image=image_ref, MinConfidence=60
        )
        
        return {
            "labels": [{"name": l["Name"], "confidence": l["Confidence"]} for l in labels.get("Labels", [])],
            "faces": self._process_faces(faces.get("FaceDetails", [])),
            "text": [{"text": t["DetectedText"], "confidence": t["Confidence"]} 
                     for t in text.get("TextDetections", []) if t["Type"] == "LINE"],
            "moderation": [{"name": m["Name"], "confidence": m["Confidence"]} 
                          for m in moderation.get("ModerationLabels", [])],
            "face_count": len(faces.get("FaceDetails", [])),
        }
    
    # ─── Video Analysis via Lambda (reuses kampa-predict-analyze) ────────
    
    def analyze_video_via_lambda(self, bucket: str, video_key: str, 
                                  creative_id: int, callback_url: str) -> dict:
        """Invoke the existing KAMPA predict Lambda for video analysis"""
        payload = {
            "bucket": bucket,
            "video_key": video_key,
            "creative_id": creative_id,
            "plan_id": 0,  # Not used for IFFIU
            "creative_type": "video",
            "writeback_url": callback_url,  # IFFIU's own writeback endpoint
        }
        
        response = self.lambda_client.invoke(
            FunctionName=settings.KAMPA_LAMBDA_FUNCTION,
            InvocationType="Event",  # Async
            Payload=json.dumps(payload),
        )
        
        return {
            "status": "processing",
            "lambda_status": response["StatusCode"],
        }
    
    # ─── Direct Video Analysis (Rekognition Video APIs) ──────────────────
    
    def analyze_video_direct(self, bucket: str, video_key: str) -> dict:
        """Direct Rekognition video analysis — labels, faces, text"""
        video_ref = {"S3Object": {"Bucket": bucket, "Name": video_key}}
        
        # Start all jobs
        label_job = self.rekognition.start_label_detection(
            Video=video_ref, MinConfidence=settings.REKOGNITION_MIN_CONFIDENCE
        )
        face_job = self.rekognition.start_face_detection(
            Video=video_ref, FaceAttributes="ALL"
        )
        text_job = self.rekognition.start_text_detection(Video=video_ref)
        
        # Poll until complete
        label_results = self._poll_job(
            self.rekognition.get_label_detection, label_job["JobId"]
        )
        face_results = self._poll_job(
            self.rekognition.get_face_detection, face_job["JobId"]
        )
        text_results = self._poll_job(
            self.rekognition.get_text_detection, text_job["JobId"]
        )
        
        duration = label_results.get("VideoMetadata", {}).get("DurationMillis", 0) / 1000
        
        return self._compute_video_scores(label_results, face_results, text_results, duration)
    
    # ─── S3 Upload ───────────────────────────────────────────────────────
    
    def upload_to_s3(self, file_bytes: bytes, key: str, 
                     content_type: str = "application/octet-stream") -> str:
        """Upload file to IFFIU's S3 bucket"""
        bucket = settings.KAMPA_UPLOAD_BUCKET
        self.s3.put_object(Bucket=bucket, Key=key, Body=file_bytes, ContentType=content_type)
        return f"s3://{bucket}/{key}"
    
    def get_presigned_url(self, bucket: str, key: str, expires: int = 3600) -> str:
        return self.s3.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires
        )
    
    # ─── Internal Helpers ────────────────────────────────────────────────
    
    def _process_faces(self, face_details: list) -> list:
        faces = []
        for fd in face_details:
            emotions = {e["Type"]: e["Confidence"] for e in fd.get("Emotions", [])}
            dominant = max(emotions, key=emotions.get) if emotions else None
            faces.append({
                "age_low": fd.get("AgeRange", {}).get("Low"),
                "age_high": fd.get("AgeRange", {}).get("High"),
                "gender": fd.get("Gender", {}).get("Value"),
                "dominant_emotion": dominant,
                "emotions": emotions,
                "smile": fd.get("Smile", {}).get("Value", False),
                "confidence": fd.get("Confidence", 0),
            })
        return faces
    
    def _poll_job(self, get_fn, job_id: str, max_attempts: int = 24) -> dict:
        for _ in range(max_attempts):
            response = get_fn(JobId=job_id)
            status = response["JobStatus"]
            if status == "SUCCEEDED":
                return response
            elif status == "FAILED":
                raise Exception(f"Rekognition job failed: {response.get('StatusMessage')}")
            time.sleep(5)
        raise Exception(f"Rekognition job {job_id} timed out")
    
    def _compute_video_scores(self, label_results, face_results, text_results, duration):
        """Compute attention/brand/combined scores — same logic as KAMPA Lambda"""
        # Labels
        labels = label_results.get("Labels", [])
        unique_labels = {}
        for item in labels:
            name = item["Label"]["Name"]
            conf = item["Label"]["Confidence"]
            if name not in unique_labels or conf > unique_labels[name]:
                unique_labels[name] = conf
        top_labels = sorted(unique_labels.items(), key=lambda x: x[1], reverse=True)[:15]
        label_richness = min(len(unique_labels) / 20 * 100, 100)
        
        # Faces
        faces = face_results.get("Faces", [])
        face_timestamps = set()
        emotions_agg = {}
        for item in faces:
            face_timestamps.add(item["Timestamp"])
            for emo in item.get("Face", {}).get("Emotions", []):
                emotions_agg.setdefault(emo["Type"], []).append(emo["Confidence"])
        
        face_frame_count = len(face_timestamps)
        total_frames = max(int(duration * 25), 1)  # assume 25fps
        face_ratio = min(face_frame_count / total_frames * 100, 100) if total_frames else 0
        
        dominant_emotion = None
        emotion_conf = 0
        for emo_type, confs in emotions_agg.items():
            avg = sum(confs) / len(confs)
            if avg > emotion_conf:
                dominant_emotion = emo_type
                emotion_conf = avg
        
        top_emotions = [
            {"type": t, "confidence": round(sum(c)/len(c), 1)}
            for t, c in sorted(emotions_agg.items(), key=lambda x: sum(x[1])/len(x[1]), reverse=True)[:5]
        ]
        
        # Text
        text_items = text_results.get("TextDetections", [])
        detected_texts = list({item["TextDetection"]["DetectedText"] 
                              for item in text_items 
                              if item["TextDetection"]["Type"] == "LINE"})
        
        # Scores
        attention = min(face_ratio * 1.5 + (emotion_conf * 0.3 if dominant_emotion else 0), 100)
        brand = min(len(detected_texts) * 15 + label_richness * 0.3, 100)
        combined = round(attention * 0.5 + brand * 0.3 + label_richness * 0.2, 1)
        
        risk = "low" if combined >= 65 else "medium" if combined >= 40 else "high"
        
        return {
            "attention_score": round(attention, 1),
            "brand_score": round(brand, 1),
            "combined_score": round(combined, 1),
            "risk_level": risk,
            "face_count": len(set(f["Timestamp"] for f in faces)),
            "face_frame_count": face_frame_count,
            "total_frames": total_frames,
            "dominant_emotion": dominant_emotion,
            "emotion_confidence": round(emotion_conf, 1),
            "top_labels": [{"name": n, "confidence": round(c, 1)} for n, c in top_labels],
            "top_emotions": top_emotions,
            "detected_text": detected_texts,
            "duration_sec": round(duration, 2),
        }


# Singleton
aws_service = AWSService()
