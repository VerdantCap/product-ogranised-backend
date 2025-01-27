from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.delete("/workspace/{workspace_id}/excursion/{excursion_id}")
async def delete_excursion(workspace_id: int, excursion_id: int):
    # Logic to delete the excursion
    return {"message": "Excursion deleted"}
