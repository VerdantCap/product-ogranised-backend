from fastapi import APIRouter
from app.middleware import MetricsMiddleware

router = APIRouter()
router.middleware("http")(MetricsMiddleware)

@router.get("/", tags=["home"])
async def home():
    return {"message": "Home Redirect"}

@router.get("/terms", tags=["terms"])
async def terms():
    return {"message": "Terms"}
