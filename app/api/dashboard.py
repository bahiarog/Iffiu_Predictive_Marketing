"""
IFFIU Dashboard Routes — Protected user pages
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User
from app.services.persona_generator import get_user_personas

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_user_or_redirect(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request, db: Session = Depends(get_db)):
    user = get_user_or_redirect(request, db)
    if not user:
        return RedirectResponse("/login")

    # Onboarding noch nicht abgeschlossen → Wizard zeigen
    if not user.profile or not user.profile.onboarding_done:
        return RedirectResponse("/onboarding")

    personas = get_user_personas(db, user.id)
    persona_dicts = [
        {
            "id": p.id,
            "name": p.name,
            "description_de": p.description_de,
            "avatar_emoji": p.avatar_emoji,
            "color_hex": p.color_hex,
            "age_range": p.age_range,
            "income_level": p.income_level,
            "tradition_score": p.tradition_score,
            "status_score": p.status_score,
        }
        for p in personas
    ]

    return templates.TemplateResponse("pages/dashboard_main.html", {
        "request": request,
        "user": user,
        "personas": persona_dicts,
        "onboarding_profile": user.profile,
    })


@router.get("/analysis/{creative_id}", response_class=HTMLResponse)
async def analysis_detail(request: Request, creative_id: int, db: Session = Depends(get_db)):
    user = get_user_or_redirect(request, db)
    if not user:
        return RedirectResponse("/login")
    return templates.TemplateResponse("pages/analysis_detail.html", {
        "request": request, "user": user, "creative_id": creative_id
    })
