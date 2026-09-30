"""Seed default Sinus-Milieu personas"""
import os, sys
sys.path.insert(0, "/app" if os.path.exists("/app/app") else ".")
from app.core.database import SessionLocal
from app.models.models import Persona

PERSONAS = [
    {"slug":"konservativ","name":"Konservativ-Etablierte","age_range":"40-70","income_level":"High","education":"Akademisch","tradition_score":75,"status_score":85,"weight_trust":0.8,"weight_clarity":0.6,"weight_emotion":0.3,"weight_action":0.4,"avatar_emoji":"🏛️","color_hex":"#1e3a5f","sort_order":1},
    {"slug":"liberal","name":"Liberal-Intellektuelle","age_range":"30-70","income_level":"High","education":"Akademisch","tradition_score":35,"status_score":85,"weight_trust":0.5,"weight_clarity":0.8,"weight_emotion":0.5,"weight_action":0.3,"avatar_emoji":"📚","color_hex":"#4a90d9","sort_order":2},
    {"slug":"performer","name":"Performer","age_range":"25-55","income_level":"High","education":"Hoch","tradition_score":30,"status_score":80,"weight_trust":0.4,"weight_clarity":0.5,"weight_emotion":0.7,"weight_action":0.9,"avatar_emoji":"🚀","color_hex":"#e63946","sort_order":3},
    {"slug":"expeditive","name":"Expeditive","age_range":"18-35","income_level":"Medium","education":"Hoch","tradition_score":15,"status_score":65,"weight_trust":0.3,"weight_clarity":0.4,"weight_emotion":0.9,"weight_action":0.7,"avatar_emoji":"✨","color_hex":"#9b59b6","sort_order":4},
    {"slug":"adaptiv","name":"Adaptiv-Pragmatische","age_range":"20-45","income_level":"Medium","education":"Mittel","tradition_score":45,"status_score":55,"weight_trust":0.7,"weight_clarity":0.8,"weight_emotion":0.5,"weight_action":0.6,"avatar_emoji":"🎯","color_hex":"#059669","sort_order":5},
    {"slug":"sozial","name":"Sozialökologische","age_range":"30-60","income_level":"Medium","education":"Hoch","tradition_score":30,"status_score":65,"weight_trust":0.8,"weight_clarity":0.6,"weight_emotion":0.7,"weight_action":0.3,"avatar_emoji":"🌿","color_hex":"#27ae60","sort_order":6},
    {"slug":"mitte","name":"Bürgerliche Mitte","age_range":"30-65","income_level":"Medium","education":"Mittel","tradition_score":60,"status_score":50,"weight_trust":0.8,"weight_clarity":0.8,"weight_emotion":0.4,"weight_action":0.5,"avatar_emoji":"🏠","color_hex":"#f39c12","sort_order":7},
    {"slug":"traditionelle","name":"Traditionelle","age_range":"55-80","income_level":"Low","education":"Einfach","tradition_score":90,"status_score":30,"weight_trust":0.9,"weight_clarity":0.8,"weight_emotion":0.2,"weight_action":0.2,"avatar_emoji":"🏡","color_hex":"#92400e","sort_order":8},
    {"slug":"prekaere","name":"Prekäre","age_range":"35-65","income_level":"Low","education":"Einfach","tradition_score":65,"status_score":20,"weight_trust":0.6,"weight_clarity":0.8,"weight_emotion":0.4,"weight_action":0.5,"avatar_emoji":"🔧","color_hex":"#78716c","sort_order":9},
    {"slug":"hedonisten","name":"Konsum-Hedonisten","age_range":"18-40","income_level":"Low","education":"Mittel","tradition_score":20,"status_score":30,"weight_trust":0.3,"weight_clarity":0.4,"weight_emotion":0.8,"weight_action":0.7,"avatar_emoji":"🎮","color_hex":"#e11d48","sort_order":10},
]

db = SessionLocal()
existing = db.query(Persona).count()
if existing > 0:
    print(f"Already {existing} personas in DB. Skipping seed.")
else:
    for p in PERSONAS:
        db.add(Persona(**p))
    db.commit()
    print(f"Seeded {len(PERSONAS)} Sinus-Milieu personas")
db.close()
