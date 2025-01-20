from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

@router.get("/link/google/redirect")
async def redirect_to_google_for_link(request: Request):
    # Logic to redirect users to Google for linking accounts
    return {"message": "Redirected to Google for linking accounts"}
