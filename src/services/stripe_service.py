import stripe
import hmac  
import hashlib  
import json    
from fastapi import HTTPException

from config import settings
stripe.api_key = settings.STRIPE_SECRET

class StripeService:

    def verify_hash(self, data: dict, provided_hash: str) -> bool:  
        payload = json.dumps(data).encode('utf-8')  
        expected_hash = hmac.new(settings.STRIPE_HASH.encode(), payload, hashlib.sha256).hexdigest()  
        return expected_hash == provided_hash

    async def retrieve_stripe_session(self, session_id: str):  
        try:  
            return await stripe.checkout.Session.retrieve(session_id)  
        except stripe.error.StripeError:  
            raise HTTPException(status_code=400, detail="Failed to retrieve session")  

    async def retrieve_stripe_subscription(self, subscription_id: str):  
        try:  
            return await stripe.Subscription.retrieve(subscription_id)  
        except stripe.error.StripeError:  
            raise HTTPException(status_code=400, detail="Failed to retrieve subscription")  

    async def create_billing_portal_session(self, subscription: stripe.Subscription, return_url: str) -> str:  
        try:
            portal = stripe.billing_portal.Session.create(  
                customer=subscription.customer,  
                return_url=return_url  
            )  
            return portal.url  # Return the billing portal URL  
        except Exception as e:  
            # Handle exceptions and potentially log them  
            raise ValueError(f"Couldn't create billing portal session: {str(e)}")