"""Admin API — User management, stats"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.security import require_admin
from app.models.models import User, Creative, KampaScore

router = APIRouter()

@router.get("/users")
async def list_users(admin=Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return {"users": [{"id": u.id, "email": u.email, "name": u.name, "company": u.company, "plan": u.plan, "analyses_used": u.analyses_used, "analyses_limit": u.analyses_limit, "is_admin": u.is_admin, "created_at": str(u.created_at)} for u in users]}

@router.get("/stats")
async def admin_stats(admin=Depends(require_admin), db: Session = Depends(get_db)):
    return {
        "total_users": db.query(func.count(User.id)).scalar(),
        "total_creatives": db.query(func.count(Creative.id)).scalar(),
        "total_analyses": db.query(func.count(KampaScore.id)).scalar(),
        "paid_users": db.query(func.count(User.id)).filter(User.plan != "free_trial").scalar(),
    }

@router.post("/users/{user_id}/toggle-active")
async def toggle_user(user_id: int, admin=Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    user.is_active = not user.is_active
    db.commit()
    return {"success": True, "user_id": user_id, "is_active": user.is_active}
