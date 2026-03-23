"""
IFFIU Auth Routes — Register, Login, Session
"""

from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.core.database import get_db
from app.models.models import User

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/register")
async def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(""),
    company: str = Form(""),
    db: Session = Depends(get_db),
):
    existing = db.query(User).filter(User.email == email.lower().strip()).first()
    if existing:
        return JSONResponse({"error": "Email already registered"}, status_code=400)
    
    user = User(
        email=email.lower().strip(),
        password_hash=pwd_context.hash(password),
        name=name,
        company=company,
        plan="free_trial",
        analyses_limit=3,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    request.session["user_id"] = user.id
    return RedirectResponse("/dashboard", status_code=303)


@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if not user or not pwd_context.verify(password, user.password_hash):
        return JSONResponse({"error": "Invalid credentials"}, status_code=401)
    
    request.session["user_id"] = user.id
    return RedirectResponse("/dashboard", status_code=303)


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/")


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id, "email": user.email, "name": user.name,
        "company": user.company, "plan": user.plan,
        "analyses_used": user.analyses_used, "analyses_limit": user.analyses_limit,
    }
