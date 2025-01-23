import hmac  
import hashlib  
import json  
import stripe  
from fastapi import Depends, HTTPException
from workspace.dao import WorkspaceDAO
from models.workspace_model import Workspace
from config import settings


stripe.api_key = settings.STRIPE_SECRET

class WorkspaceService:  
    def __init__(self,
        workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO)
    ):  
        self.workspace_dao = workspace_dao  

    def verify_hash(self, data: dict, provided_hash: str) -> bool:  
        payload = json.dumps(data).encode('utf-8')  
        expected_hash = hmac.new(settings.STRIPE_HASH.encode(), payload, hashlib.sha256).hexdigest()  
        return expected_hash == provided_hash  

    async def retrieve_stripe_session(self, session_id: str):  
        try:  
            return stripe.checkout.Session.retrieve(session_id)  
        except stripe.error.StripeError:  
            raise HTTPException(status_code=400, detail="Failed to retrieve session")  

    async def retrieve_stripe_subscription(self, subscription_id: str):  
        try:  
            return stripe.Subscription.retrieve(subscription_id)  
        except stripe.error.StripeError:  
            raise HTTPException(status_code=400, detail="Failed to retrieve subscription")  

    async def create_billing_portal_session(self, subscription: stripe.Subscription, return_url: str) -> str:  
        try:  
            # Create a billing portal session using the subscription's customer  
            portal = stripe.billing_portal.Session.create(  
                customer=subscription.customer,  
                return_url=return_url  
            )  
            return portal.url  # Return the billing portal URL  
        except Exception as e:  
            # Handle exceptions and potentially log them  
            raise ValueError(f"Couldn't create billing portal session: {str(e)}")

    async def create_workspace(self, name: str, billing_plan: str, stripe_id: str, user_id: int, selected_spaces: list) -> Workspace:  
        workspace = await self.workspace_dao.create_workspace(name, billing_plan, stripe_id, user_id)  
        workspace = await self.workspace_dao.set_spaces(workspace, selected_spaces)  
        return workspace
    
    async def get_workspace(self, workspace_id: str) -> Workspace:
        workspace = await self.workspace_dao.get_workspace(workspace_id)
        return workspace
    
    async def update_workspace(self, workspace: Workspace, selected_spaces:  list) -> Workspace:
        workspace = await self.workspace_dao.set_spaces(workspace, selected_spaces)
        return workspace