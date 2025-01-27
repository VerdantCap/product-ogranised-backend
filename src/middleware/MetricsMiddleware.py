from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter

app = FastAPI()

# Initialize the counter
http_requests_total = Counter(
    'http_requests_total', 
    'The total number of HTTP requests', 
    ['method', 'endpoint']
)

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Normalize the path
        endpoint = self.normalize_path(request.url.path)
        method = request.method

        # Increment the counter
        http_requests_total.labels(method=method, endpoint=endpoint).inc()

        # Process the request
        response = await call_next(request)
        return response

    def normalize_path(self, path: str) -> str:
        # Split the path into its parts
        segments = path.strip('/').split('/')
        
        # Filter out segments that are deemed user identifiers
        normalized_segments = [segment for segment in segments if not self.is_user_identifier(segment)]
        
        # Return the new path, excluding the user identifier
        return '/' + '/'.join(normalized_segments)

    def is_user_identifier(self, segment: str) -> bool:
        # Determine if a segment is likely a user ID, for instance, by pattern
        return bool(re.match(r'^[a-f0-9]{8}$', segment))  # Example: Replace with actual pattern or condition

# Add the middleware to the FastAPI app
app.add_middleware(MetricsMiddleware)