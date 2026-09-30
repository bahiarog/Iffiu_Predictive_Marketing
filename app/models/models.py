"""IFFIU Database Models"""
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255))
    company = Column(String(255))
    plan = Column(String(50), default="free_trial")
    stripe_customer_id = Column(String(255))
    analyses_used = Column(Integer, default=0)
    analyses_limit = Column(Integer, default=3)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    creatives = relationship("Creative", back_populates="user")

class Creative(Base):
    __tablename__ = "creatives"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255))
    filename = Column(String(500))
    media_type = Column(String(20))
    s3_key = Column(String(500))
    s3_bucket = Column(String(255))
    duration_sec = Column(Float)
    width = Column(Integer)
    height = Column(Integer)
    file_size_bytes = Column(Integer)
    analysis_status = Column(String(20), default="pending")
    ab_group = Column(String(10))  # A/B testing
    created_at = Column(DateTime, server_default=func.now())
    user = relationship("User", back_populates="creatives")
    rekognition_result = relationship("RekognitionResult", back_populates="creative", uselist=False)
    persona_results = relationship("PersonaResult", back_populates="creative")
    kampa_score = relationship("KampaScore", back_populates="creative", uselist=False)

class RekognitionResult(Base):
    __tablename__ = "rekognition_results"
    id = Column(Integer, primary_key=True, index=True)
    creative_id = Column(Integer, ForeignKey("creatives.id"), nullable=False, unique=True)
    attention_score = Column(Float)
    brand_score = Column(Float)
    combined_score = Column(Float)
    risk_level = Column(String(20))
    face_count = Column(Integer, default=0)
    face_frame_count = Column(Integer, default=0)
    text_frame_count = Column(Integer, default=0)
    total_frames = Column(Integer, default=0)
    dominant_emotion = Column(String(50))
    emotion_confidence = Column(Float)
    video_duration_sec = Column(Float)
    top_labels = Column(JSON)
    top_emotions = Column(JSON)
    detected_text = Column(JSON)
    face_details = Column(JSON)
    heatmap_data = Column(JSON)  # Attention heatmap coordinates
    raw_analysis = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    creative = relationship("Creative", back_populates="rekognition_result")

class Persona(Base):
    __tablename__ = "personas"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    slug = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(50), default="sinus")
    age_range = Column(String(20))
    income_level = Column(String(20))
    education = Column(String(50))
    tradition_score = Column(Integer)
    status_score = Column(Integer)
    weight_trust = Column(Float, default=0.5)
    weight_clarity = Column(Float, default=0.5)
    weight_emotion = Column(Float, default=0.5)
    weight_action = Column(Float, default=0.5)
    avatar_url = Column(String(500))
    avatar_emoji = Column(String(10))
    color_hex = Column(String(10))
    description_de = Column(Text)
    description_en = Column(Text)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    results = relationship("PersonaResult", back_populates="persona")

class PersonaResult(Base):
    __tablename__ = "persona_results"
    id = Column(Integer, primary_key=True, index=True)
    creative_id = Column(Integer, ForeignKey("creatives.id"), nullable=False)
    persona_id = Column(Integer, ForeignKey("personas.id"), nullable=False)
    trust_score = Column(Float)
    clarity_score = Column(Float)
    emotion_score = Column(Float)
    action_score = Column(Float)
    combined_score = Column(Float)
    risk_level = Column(String(20))
    reasoning = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    creative = relationship("Creative", back_populates="persona_results")
    persona = relationship("Persona", back_populates="results")
    __table_args__ = (Index("ix_persona_results_creative_persona", "creative_id", "persona_id"),)

class KampaScore(Base):
    __tablename__ = "kampa_scores"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    creative_id = Column(Integer, ForeignKey("creatives.id"), nullable=False, unique=True)
    overall_score = Column(Float)
    risk_level = Column(String(20))
    trust_avg = Column(Float)
    clarity_avg = Column(Float)
    emotion_avg = Column(Float)
    action_avg = Column(Float)
    persona_count = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    creative = relationship("Creative", back_populates="kampa_score")

class ABTest(Base):
    __tablename__ = "ab_tests"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255))
    creative_a_id = Column(Integer, ForeignKey("creatives.id"), nullable=False)
    creative_b_id = Column(Integer, ForeignKey("creatives.id"), nullable=False)
    winner = Column(String(1))  # A or B or null
    score_a = Column(Float)
    score_b = Column(Float)
    comparison_data = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
