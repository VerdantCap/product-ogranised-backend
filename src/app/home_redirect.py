from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

@router.get("/home")
async def home_redirect(request: Request):
    # Logic to redirect users to the home page
    return {"message": "Redirected to home"}
