from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def _get_user(request, db):
    uid = request.session.get("user_id")
    if not uid: return None
    return db.query(User).filter(User.id==uid).first()

@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user: return RedirectResponse("/login")
    return templates.TemplateResponse("pages/dashboard_main.html", {"request":request,"user":user})

@router.get("/analysis/{creative_id}", response_class=HTMLResponse)
async def analysis_detail(request: Request, creative_id: int, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user: return RedirectResponse("/login")
    return templates.TemplateResponse("pages/analysis_detail.html", {"request":request,"user":user,"creative_id":creative_id})
