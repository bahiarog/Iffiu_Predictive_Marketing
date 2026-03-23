"""
IFFIU Onboarding Routes — 3-Fragen Wizard

Nach der Registrierung wird der User durch 3 kurze Fragen geführt:
1. Branche
2. Unternehmensgröße
3. 3 Produkte beschreiben

Anschließend werden automatisch passende Custom-Personas generiert.
"""

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import User, UserProfile
from app.services.persona_generator import generate_custom_personas

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _get_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


@router.get("/", response_class=HTMLResponse)
async def onboarding_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login")

    # Wenn Onboarding bereits abgeschlossen → direkt zum Dashboard
    if user.profile and user.profile.onboarding_done:
        return RedirectResponse("/dashboard")

    return templates.TemplateResponse("pages/onboarding.html", {
        "request": request,
        "user": user,
    })


@router.post("/save")
async def onboarding_save(
    request: Request,
    industry: str = Form(...),
    company_size: str = Form(...),
    product_1: str = Form(""),
    product_2: str = Form(""),
    product_3: str = Form(""),
    db: Session = Depends(get_db),
):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login")

    # Profil anlegen oder updaten
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)

    profile.industry = industry.lower().strip()
    profile.company_size = company_size.lower().strip()
    profile.product_1 = product_1.strip()
    profile.product_2 = product_2.strip()
    profile.product_3 = product_3.strip()
    profile.onboarding_done = True
    db.commit()
    db.refresh(profile)

    # Custom-Personas generieren
    generate_custom_personas(db, profile)

    return RedirectResponse("/dashboard", status_code=303)
