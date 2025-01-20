from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

@router.post("/accept-invite/{workspace_id}/{token}")
async def accept_invite(request: Request, workspace_id: int, token: str):
    # Logic to accept the workspace invitation
    return {"message": "Workspace invitation accepted"}
