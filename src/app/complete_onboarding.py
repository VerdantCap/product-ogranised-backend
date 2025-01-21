from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from stripe import Session as StripeSession, Subscription as StripeSubscription, error as StripeError
from app.dependencies import get_db, get_current_user
from app.models import Workspace, User
from app.enums import BillingPlan
import stripe
import hmac
import hashlib
import json

router = APIRouter()

class OnboardingRequest(BaseModel):
    plan: str
    session_id: str
    user: int
    workspace: str
    spaces: list[str]
    hash: str

@router.post("/complete-onboarding")
async def complete_onboarding(
    request: OnboardingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate hash
    hash_data = json.dumps({
        'plan': request.plan,
        'uid': request.user,
        'user': request.user,
        'workspace': request.workspace,
        'spaces': request.spaces,
    })
    expected_hash = hmac.new(
        key=stripe.api_key.encode(),
        msg=hash_data.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()

    if expected_hash != request.hash:
        raise HTTPException(status_code=400, detail="Invalid hash")

    if request.user != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Retrieve Stripe session
    try:
        session = StripeSession.retrieve(request.session_id)
    except StripeError.StripeError:
        raise HTTPException(status_code=400, detail="Invalid session")

    if request.user != session.client_reference_id:
        raise HTTPException(status_code=400, detail="Invalid session reference")

    # Retrieve Stripe subscription
    try:
        subscription = StripeSubscription.retrieve(session.subscription)
    except StripeError.StripeError:
        raise HTTPException(status_code=400, detail="Invalid subscription")

    if subscription.status != 'active':
        raise HTTPException(status_code=400, detail="Inactive subscription")

    # Create workspace
    plan = BillingPlan(request.plan)
    workspace = Workspace(
        name=request.workspace.strip(),
        billing_plan=plan,
        stripe_id=subscription.id,
        owner_id=current_user.id
    )
    db.add(workspace)
    db.commit()

    # Set spaces and join workspace
    workspace.set_spaces(request.spaces)
    current_user.join_workspace(workspace)
    db.commit()

    return {"message": "Onboarding complete", "workspace_id": workspace.id}
