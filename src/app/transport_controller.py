from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.delete("/workspace/{workspace_id}/transport/{transport_id}")
async def delete_transport(workspace_id: int, transport_id: int):
    # Logic to delete the transport
    return {"message": "Transport deleted"}
