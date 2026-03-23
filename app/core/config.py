"""
IFFIU Configuration — Environment-based settings
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "IFFIU"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    
    # Database
    DATABASE_URL: str = "postgresql://iffiu:iffiu_secret@localhost:5432/iffiu"
    
    # AWS — connects to existing KAMPA infrastructure
    AWS_REGION: str = "eu-central-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    
    # KAMPA Backend Integration
    KAMPA_LAMBDA_FUNCTION: str = "kampa-predict-analyze"
    KAMPA_S3_BUCKET: str = "kampa-transcoded-output"
    KAMPA_UPLOAD_BUCKET: str = "kampa-uploads"
    KAMPA_WRITEBACK_URL: str = "https://kampa-tool.com/api/predict-writeback.php"
    
    # Rekognition (same account as KAMPA)
    REKOGNITION_MIN_CONFIDENCE: float = 70.0
    
    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PRICE_STARTER: Optional[str] = None  # price_xxx
    STRIPE_PRICE_PRO: Optional[str] = None
    STRIPE_PRICE_ENTERPRISE: Optional[str] = None
    
    # Email (optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASS: Optional[str] = None
    
    # Upload limits
    MAX_UPLOAD_MB: int = 500
    ALLOWED_EXTENSIONS: list = [".mp4", ".mov", ".mxf", ".avi", ".jpg", ".jpeg", ".png", ".gif"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
