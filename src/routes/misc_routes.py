from fastapi import APIRouter
from app.middleware import MetricsMiddleware
from src.app.metrics_controller import router as metrics_router

router = APIRouter()

router.include_router(metrics_router, prefix="/metrics")
router.middleware("http")(MetricsMiddleware)

@router.post("/stripe/webhook", tags=["stripe"])
async def stripe_webhook():
    return {"message": "Stripe Webhook"}
