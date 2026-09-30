"""IFFIU Configuration"""
from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    APP_NAME: str = "IFFIU"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24h

    # Database
    DATABASE_URL: str = "postgresql://iffiu:iffiu_secret@db:5432/iffiu"

    # AWS
    AWS_REGION: str = "eu-central-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    S3_BUCKET: str = "kampa-qc-assets"
    STATE_MACHINE_ARN: str = "arn:aws:states:eu-central-1:754840114791:stateMachine:kampa-predict-state"
    SQS_QUEUE_URL: Optional[str] = None

    # Rekognition
    REKOGNITION_MIN_CONFIDENCE: float = 70.0

    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASS: Optional[str] = None
    ADMIN_EMAIL: str = "bahiarog@me.com"

    # Admin emails (comma-separated)
    ADMIN_EMAILS: str = "bahiarog@me.com"

    # Upload
    MAX_UPLOAD_MB: int = 500

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
