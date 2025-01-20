from fastapi import FastAPI
from src.routers.accept_invite import router as accept_invite_router
from src.routers.accommodation_controller import router as accommodation_router
from src.routers.auth_from_google import router as auth_from_google_router
from src.routers.complete_onboarding import router as complete_onboarding_router
from src.routers.excursion_controller import router as excursion_router
from src.routers.handle_stripe_webhook import router as stripe_webhook_router
from src.routers.home_redirect import router as home_redirect_router
from src.routers.link_from_google import router as link_from_google_router
from src.routers.list_events import router as list_events_router
from src.routers.logout import router as logout_router
from src.routers.manage_subscription import router as manage_subscription_router
from src.routers.metrics_controller import router as metrics_router
from src.routers.redirect_to_google_for_auth import router as redirect_auth_router
from src.routers.redirect_to_google_for_link import router as redirect_link_router
from src.routers.transport_controller import router as transport_router
from src.routers.unlink_google_account import router as unlink_google_account_router

app = FastAPI()

app.include_router(accept_invite_router, prefix="/api")
app.include_router(accommodation_router, prefix="/api")
app.include_router(auth_from_google_router, prefix="/api")
app.include_router(complete_onboarding_router, prefix="/api")
app.include_router(excursion_router, prefix="/api")
app.include_router(stripe_webhook_router, prefix="/api")
app.include_router(home_redirect_router, prefix="/api")
app.include_router(link_from_google_router, prefix="/api")
app.include_router(list_events_router, prefix="/api")
app.include_router(logout_router, prefix="/api")
app.include_router(manage_subscription_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")
app.include_router(redirect_auth_router, prefix="/api")
app.include_router(redirect_link_router, prefix="/api")
app.include_router(transport_router, prefix="/api")
app.include_router(unlink_google_account_router, prefix="/api")
