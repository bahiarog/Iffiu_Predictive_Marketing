"""Auth API — Register, Login, Profile"""
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.core.email_service import notify_admin_new_registration, send_welcome_email
from app.core.config import settings
from app.models.models import User

router = APIRouter()

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str = ""
    company: str = ""

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

async def _parse_body(request: Request) -> tuple:
    ct = request.headers.get("content-type", "")
    if "json" in ct:
        return await request.json(), False
    form = await request.form()
    return dict(form), True

@router.post("/register")
async def register(request: Request, db: Session = Depends(get_db)):
    data, is_form = await _parse_body(request)
    req = RegisterRequest(**data)
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        if is_form:
            return RedirectResponse("/register?error=exists", status_code=303)
        raise HTTPException(400, "Email already registered")
    admin_emails = [e.strip().lower() for e in settings.ADMIN_EMAILS.split(",")]
    is_admin = req.email.lower() in admin_emails
    user = User(
        email=req.email,
        password_hash=hash_password(req.password),
        name=req.name,
        company=req.company,
        is_admin=is_admin,
        analyses_limit=999999 if is_admin else 3,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    try:
        notify_admin_new_registration(req.email, req.name, req.company)
        send_welcome_email(req.email, req.name)
    except Exception:
        pass
    token = create_access_token({"sub": str(user.id)})
    if is_form:
        resp = RedirectResponse("/dashboard", status_code=303)
        resp.set_cookie("access_token", f"Bearer {token}", httponly=True, max_age=86400, samesite="lax", secure=True)
        return resp
    return {"success": True, "token": token, "user": {"id": user.id, "email": user.email, "name": user.name, "plan": user.plan, "is_admin": user.is_admin}}

@router.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    data, is_form = await _parse_body(request)
    req = LoginRequest(**data)
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        if is_form:
            return RedirectResponse("/login?error=invalid", status_code=303)
        raise HTTPException(401, "Invalid credentials")
    if not user.is_active:
        if is_form:
            return RedirectResponse("/login?error=inactive", status_code=303)
        raise HTTPException(403, "Account deactivated")
    token = create_access_token({"sub": str(user.id)})
    if is_form:
        resp = RedirectResponse("/dashboard", status_code=303)
        resp.set_cookie("access_token", f"Bearer {token}", httponly=True, max_age=86400, samesite="lax", secure=True)
        return resp
    resp = JSONResponse({"success": True, "token": token, "user": {"id": user.id, "email": user.email, "name": user.name, "plan": user.plan, "is_admin": user.is_admin, "analyses_used": user.analyses_used, "analyses_limit": user.analyses_limit}})
    resp.set_cookie("access_token", f"Bearer {token}", httponly=True, max_age=86400, samesite="lax", secure=True)
    return resp

@router.get("/me")
async def me(user=Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "name": user.name, "company": user.company, "plan": user.plan, "is_admin": user.is_admin, "analyses_used": user.analyses_used, "analyses_limit": user.analyses_limit}

@router.post("/logout")
async def logout():
    resp = RedirectResponse("/", status_code=303)
    resp.delete_cookie("access_token")
    return resp
@router.get("/login")
async def login_get(request: Request, email: str = "", password: str = ""):
    """GET-based login fallback"""
    if not email or not password:
        from fastapi.responses import HTMLResponse
        return HTMLResponse("Missing email or password", status_code=400)
    from app.core.database import get_db
    db = next(get_db())
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        db.close()
        return RedirectResponse("/login?error=invalid", status_code=303)
    token = create_access_token({"sub": str(user.id)})
    resp = RedirectResponse("/dashboard", status_code=303)
    resp.set_cookie("access_token", f"Bearer {token}", httponly=True, max_age=86400, samesite="lax", secure=True)
    db.close()
    return resp

@router.get("/logout")
async def logout_get():
    from fastapi.responses import RedirectResponse
    resp = RedirectResponse("/", status_code=303)
    resp.delete_cookie("access_token")
    return resp
