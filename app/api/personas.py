"""Personas CRUD"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import Persona

router = APIRouter()

@router.get("/personas")
async def list_personas(user=Depends(get_current_user), db: Session = Depends(get_db)):
    personas = db.query(Persona).filter(
        Persona.is_active == True,
        (Persona.user_id == None) | (Persona.user_id == user.id)
    ).order_by(Persona.sort_order).all()
    return {"personas": [{"id": p.id, "slug": p.slug, "name": p.name, "age_range": p.age_range, "income_level": p.income_level, "avatar_url": p.avatar_url, "avatar_emoji": p.avatar_emoji, "color_hex": p.color_hex} for p in personas]}
