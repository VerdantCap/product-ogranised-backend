from pydantic import BaseModel 
from typing import List

class OnboardingRequest(BaseModel):  
    plan: str  
    session_id: str  
    user: int  
    workspace: str  
    spaces: List[str]  
    hash: str  
