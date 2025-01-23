from pydantic import BaseModel, field_validator 
from typing import List
from datetime import datetime

class OnboardingRequest(BaseModel):  
    plan: str  
    session_id: str  
    user: int  
    workspace: str  
    spaces: List[str]  
    hash: str  


class EventCreate(BaseModel):  
    title: str  
    description: str  
    start_at: datetime  
    end_at: datetime  

    @field_validator("end_at")  
    def end_must_be_after_start(cls, end_at, values):  
        start_at = values.get('start_at')  
        if start_at and end_at <= start_at:  
            raise ValueError("end_at must occur after start_at")  
        return end_at