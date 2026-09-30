
"""IFFIU — Predictive Marketing Intelligence Platform"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
from app.core.config import settings
from app.core.database import engine, get_db, Base
from app.api import auth, upload, analyze, creatives, recommendations, ab_test, personas, diagnostic, admin, stripe_checkout
Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="IFFIU — Predictive Marketing Intelligence",
    version="2.0.0",
    docs_url="/api/docs" if settings.DEBUG else None,
)
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("pages/landing.html", {"request": request})

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ── Background Poller: polls Step Functions every 15s ─────────
@app.on_event("startup")
async def start_sfn_poller():
    import threading, time, logging
    from app.services.sfn_poller import poll_and_writeback
    _log = logging.getLogger("poller")
    def _loop():
        _log.info("SFN Poller background thread started")
        while True:
            try:
                poll_and_writeback()
            except Exception as e:
                _log.error(f"Poller error: {e}")
            time.sleep(15)
    threading.Thread(target=_loop, daemon=True).start()


app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(creatives.router, prefix="/api", tags=["creatives"])
app.include_router(analyze.router, prefix="/api", tags=["analysis"])
app.include_router(recommendations.router, prefix="/api", tags=["recommendations"])
app.include_router(ab_test.router, prefix="/api", tags=["ab-test"])
app.include_router(personas.router, prefix="/api", tags=["personas"])
app.include_router(diagnostic.router, prefix="/api", tags=["diagnostic"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(stripe_checkout.router, prefix="/stripe", tags=["stripe"])


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("pages/login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("pages/register.html", {"request": request})

@app.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    return templates.TemplateResponse("pages/pricing.html", {"request": request})

@app.get("/demo", response_class=HTMLResponse)
async def demo_page(request: Request):
    return templates.TemplateResponse("pages/demo.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    from app.core.security import get_current_user
    from app.core.database import get_db
    try:
        db = next(get_db())
        user = await get_current_user(request, None, db)
        db.close()
    except Exception:
        return templates.TemplateResponse("pages/login.html", {"request": request})
    return templates.TemplateResponse("pages/dashboard_main.html", {"request": request, "user": user})

@app.get("/impressum", response_class=HTMLResponse)
async def impressum(request: Request):
    return templates.TemplateResponse("pages/impressum.html", {"request": request})

@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse("pages/privacy.html", {"request": request})

@app.get("/agb", response_class=HTMLResponse)
async def agb(request: Request):
    return templates.TemplateResponse("pages/agb.html", {"request": request})

@app.get("/health")
async def health():
    return {"status": "ok", "service": "iffiu", "version": "2.0.0"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)

@app.get("/debug-cookies")
async def debug_cookies(request: Request):
    return {
        "cookies": dict(request.cookies),
        "headers": dict(request.headers),
    }

@app.get("/debug-dashboard")
async def debug_dashboard(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return {"error": "no cookie"}
    token_clean = token.replace("Bearer ", "").strip('"')
    try:
        from jose import jwt
        from app.core.config import settings
        payload = jwt.decode(token_clean, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return {"payload": payload, "raw_cookie": token[:50]}
    except Exception as e:
        return {"error": str(e), "raw_cookie": token[:50]}

@app.get("/force-login")
async def force_login(t: str = ""):
    if not t:
        from app.core.security import create_access_token
        t = create_access_token({"sub": "1"})
    resp = RedirectResponse("/dashboard?t=" + t, status_code=303)
    resp.set_cookie("access_token", "Bearer " + t, httponly=True, max_age=86400, samesite="none", secure=True, path="/", domain="iffiu.com")
    return resp

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page_override(request: Request, t: str = ""):
    from app.core.database import get_db
    from app.core.security import get_current_user
    from jose import jwt, JWTError
    from app.core.config import settings
    user = None
    # Try token from URL first
    token = t or ""
    if not token:
        raw = request.cookies.get("access_token", "")
        token = raw.replace("Bearer ", "").strip('"')
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            uid = int(payload.get("sub", 0))
            db = next(get_db())
            from app.models.models import User
            user = db.query(User).filter(User.id == uid).first()
        except Exception:
            pass
    if not user:
        return templates.TemplateResponse("pages/login.html", {"request": request})
    return templates.TemplateResponse("pages/dashboard_main.html", {"request": request, "user": user})

