"""SQS Consumer — polls for Rekognition results"""
import time
import json
import logging
from app.core.database import SessionLocal
from app.services.aws_service import poll_sqs_messages
from app.services.scoring_engine import run_scoring
from app.models.models import Creative, RekognitionResult, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sqs_consumer")

def process_message(data: dict):
    db = SessionLocal()
    try:
        creative_id = data.get("creative_id")
        status = data.get("status", "").upper()
        logger.info(f"Processing creative {creative_id}: {status}")

        creative = db.query(Creative).filter(Creative.id == creative_id).first()
        if not creative:
            logger.error(f"Creative {creative_id} not found")
            return

        if status == "COMPLETED":
            # Save Rekognition result
            existing = db.query(RekognitionResult).filter(RekognitionResult.creative_id == creative_id).first()
            fields = {
                "attention_score": data.get("attention_score"),
                "brand_score": data.get("brand_score"),
                "combined_score": data.get("combined_score"),
                "face_count": data.get("face_count", 0),
                "dominant_emotion": data.get("emotion_dominant") or data.get("dominant_emotion"),
                "emotion_confidence": data.get("emotion_confidence"),
                "top_labels": data.get("top_labels"),
                "detected_text": data.get("detected_text"),
                "face_details": data.get("face_details"),
            }
            if existing:
                for k, v in fields.items():
                    setattr(existing, k, v)
            else:
                db.add(RekognitionResult(creative_id=creative_id, **fields))

            db.commit()
            run_scoring(db, creative_id, creative.user_id)
            creative.analysis_status = "completed"

            user = db.query(User).filter(User.id == creative.user_id).first()
            if user:
                user.analyses_used = (user.analyses_used or 0) + 1

        elif status == "FAILED":
            creative.analysis_status = "failed"

        db.commit()
        logger.info(f"Creative {creative_id} processed: {creative.analysis_status}")

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        db.rollback()
    finally:
        db.close()

def run():
    logger.info("SQS Consumer started")
    while True:
        try:
            messages = poll_sqs_messages(max_messages=5)
            for msg in messages:
                process_message(msg)
            if not messages:
                time.sleep(10)
        except Exception as e:
            logger.error(f"SQS poll error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    run()
