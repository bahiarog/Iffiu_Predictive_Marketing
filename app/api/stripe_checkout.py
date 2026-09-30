"""Stripe Checkout"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.models import User

router = APIRouter()

PLANS = {
    "starter":      {"name": "IFFIU Starter",      "price_eur": 5900,  "analyses": 25},
    "professional": {"name": "IFFIU Professional",  "price_eur": 19900, "analyses": 100},
    "enterprise":   {"name": "IFFIU Enterprise",    "price_eur": 39900, "analyses": 999999},
}

@router.post("/create-checkout")
async def create_checkout(request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(503, "Payment not configured. Contact info@pimentagroup.de")

    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY

    data = await request.json()
    plan_id = data.get("plan")
    if plan_id not in PLANS:
        raise HTTPException(400, "Invalid plan")

    plan = PLANS[plan_id]
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "eur",
                "product_data": {"name": plan["name"]},
                "unit_amount": plan["price_eur"],
                "recurring": {"interval": "month"},
            },
            "quantity": 1,
        }],
        mode="subscription",
        success_url=str(request.base_url) + "dashboard?payment=success",
        cancel_url=str(request.base_url) + "pricing?payment=cancelled",
        customer_email=user.email,
        metadata={"plan": plan_id, "user_id": str(user.id)},
    )
    return {"url": session.url}

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    if not settings.STRIPE_WEBHOOK_SECRET:
        return {"status": "not configured"}

    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
    except Exception:
        raise HTTPException(400, "Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("metadata", {}).get("user_id")
        plan_id = session.get("metadata", {}).get("plan")
        if user_id and plan_id and plan_id in PLANS:
            user = db.query(User).filter(User.id == int(user_id)).first()
            if user:
                user.plan = plan_id
                user.analyses_limit = PLANS[plan_id]["analyses"]
                user.stripe_customer_id = session.get("customer")
                db.commit()

    return {"status": "ok"}
