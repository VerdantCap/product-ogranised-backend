from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.delete("/workspace/{workspace_id}/accommodation/{accommodation_id}")
async def delete_accommodation(workspace_id: int, accommodation_id: int):
    # Logic to delete the accommodation
    return {"message": "Accommodation deleted"}
