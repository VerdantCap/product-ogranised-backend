from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import RedirectResponse

app = FastAPI()

class EnsureWorkspaceSubscriptionActive(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Simulate getting the workspace from the request
        workspace = self.get_workspace(request)

        # Check if the workspace has an active subscription
        if not self.has_active_subscription(workspace):
            # Redirect to the expired workspace route
            return RedirectResponse(url=f"/workspace/{workspace}/expired")

        # Continue processing the request
        response = await call_next(request)
        return response

    def get_workspace(self, request: Request):
        # Simulate getting the workspace from the request
        # Replace with actual logic to extract workspace
        return "example-workspace"

    def has_active_subscription(self, workspace):
        # Simulate checking if the workspace has an active subscription
        # Replace with actual logic to check subscription status
        return False

app.add_middleware(EnsureWorkspaceSubscriptionActive)