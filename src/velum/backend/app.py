"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from velum.backend.routes import router, set_registry
from velum.engine.registry import ModelRegistry

# Velum is fully local — only the Streamlit frontend on localhost should ever
# call the backend. Restricting CORS to localhost:8501 (both 127.0.0.1 and
# localhost spellings) is tighter than the plan's "*" without breaking the UI.
_LOCAL_ORIGINS = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
]


def create_app(registry: ModelRegistry) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        registry: The model registry with at least one registered redactor.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="Velum API",
        description="Local PII redaction API",
        version="0.1.0",
    )

    # Allow only the local Streamlit frontend to call the API.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_LOCAL_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Inject the registry into routes
    set_registry(registry)

    # Mount routes
    app.include_router(router)

    return app
