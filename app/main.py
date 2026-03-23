"""
IFFIU — Predictive Marketing Intelligence Platform
Spin-off from KAMPA | Powered by AWS Rekognition + Sinus-Milieu AI
"""

from fastapi import FastAPI, Request, Depends, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import os

from app.core.config import settings
from app.core.database import engine, get_db, Base
from app.api import auth, analysis, dashboard, webhooks
from app.models import user, creative, persona, score

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="IFFIU — Predictive Marketing Intelligence",
    version="1.0.0",
    docs_url="/api/docs" if settings.DEBUG else None,
)

# Middleware
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files & templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include API routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])


# ─── Public Pages ────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("pages/landing.html", {"request": request})


@app.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    return templates.TemplateResponse("pages/pricing.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("pages/login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("pages/register.html", {"request": request})


@app.get("/demo", response_class=HTMLResponse)
async def demo_page(request: Request):
    """Live demo with sample data — perfect for sales meetings"""
    return templates.TemplateResponse("pages/demo.html", {"request": request})


# ─── Health Check ────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "iffiu", "version": "1.0.0"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
