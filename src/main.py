from fastapi import FastAPI
from config import settings
# from contextlib import asynccontextmanager
# from typing import AsyncIterator
from fastapi.middleware.cors import CORSMiddleware
import controllers

# Initialize the FastAPI application
app = FastAPI(
        root_path=settings.ROOT_PATH, openapi_url="/openapi.json"
    )

# Include the authentication router
app.include_router(
        controllers.auth_router,
        prefix="/auth",
        tags=["auth"],
        responses={404: {"description": "Not found"}},
    )

# Include the workspace router
app.include_router(
        controllers.workspace_router,
        prefix="/workspace",
        tags=["workspace"],
        responses={404: {"description": "Not found"}},
    )


app.include_router(
    controllers.event_router,
    prefix="/event",
    tags=["event"],
    responses={404: {"description": "Not found"}},
)

app.include_router(
    controllers.item_router,
    prefix="/item",
    tags=["item"],
    responses={404: {"description": "Not found"}},
)

# Define allowed origins for CORS
origins = [
    "http://organised.ai",
    "https://organised.ai",
    "http://localhost",
    "http://localhost:3000",
]

# Add CORS middleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Error"],
    allow_origin_regex=r"http[s]?://.*\.(getorganised\.ai|githubpreview\.dev|app\.github\.dev)",
)

# Run the application using Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
