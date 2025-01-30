import stripe
from fastapi import HTTPException

from config import settings
stripe.api_key = settings.STRIPE_SECRET

class StripeService:
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
        
    async def create_funding_session(self, user_id: str, user_email: str, success_url: str, cancel_url: str, plan: str = "") -> str: 
        try:  
            session = stripe.checkout.Session.create(
                customer_email=user_email,  
                client_reference_id=user_id,  
                line_items=[  
                    {  
                        # "price": STRIPE_PLANS[plan],  # Use plan's Stripe price ID  
                        "price": "price_1J5cyCLKZFl6ncHarqjPDMBq",
                        "quantity": 1,  
                    }  
                ],  
                mode="subscription",  
                success_url=success_url,  
                cancel_url=cancel_url,  
            )
            return session
        except stripe.error.StripeError as e:
            raise HTTPException(  
                status_code=500,  
                detail=f"There was a problem creating the session: {e.user_message}",  
            ) 