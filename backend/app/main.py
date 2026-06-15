from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.db.seed import initialize_database


def create_app() -> FastAPI:
    initialize_database()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Prototype API for the radiation therapy SCI paper workshop.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    return app


app = create_app()
