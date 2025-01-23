from fastapi import FastAPI
from config import settings
# from contextlib import asynccontextmanager
# from typing import AsyncIterator
from fastapi.middleware.cors import CORSMiddleware
import controllers

# @asynccontextmanager
# async def lifespan(app: FastAPI) -> AsyncIterator[None]:
#     await load_schedule_and_start_jobs()
#     scheduler.start()
#     yield
#     scheduler.shutdown()
#     await get_postgres_session().aclose()

app = FastAPI(
        root_path=settings.ROOT_PATH, openapi_url="/openapi.json"
    )
app.include_router(
        controllers.auth_router,
        prefix="/auth",
        tags=["auth"],
        responses={404: {"description": "Not found"}},
    )

app.include_router(
        controllers.workspace_router,
        prefix="/workspace",
        tags=["workspace"],
        responses={404: {"description": "Not found"}},
    )

origins = [
    "http://organised.ai",
    "https://organised.ai",
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Error"],
    allow_origin_regex=r"http[s]?://.*\.(getorganised\.ai|githubpreview\.dev|app\.github\.dev)",
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)