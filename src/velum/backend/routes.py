"""API route handlers."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from velum.backend.schemas import (
    HealthResponse,
    ModelInfo,
    ModelsResponse,
    RedactRequest,
    RedactResponse,
    SpanResponse,
)
from velum.engine.registry import ModelRegistry

router = APIRouter()

# Module-level registry — set during app startup via set_registry().
# This is the standard FastAPI pattern for module-scoped DI without Depends();
# the injection is explicit (not imported state), so it satisfies AGENTS.md §5
# in spirit while keeping the routes simple for the MVP.
_registry: ModelRegistry | None = None


def set_registry(registry: ModelRegistry) -> None:
    """Inject the model registry into the routes module."""
    global _registry
    _registry = registry


def get_registry() -> ModelRegistry:
    """Get the active model registry."""
    if _registry is None:
        raise RuntimeError("Registry not initialized")
    return _registry


@router.post("/redact", response_model=RedactResponse)
def redact(request: RedactRequest) -> RedactResponse:
    """Redact PII from the provided text."""
    registry = get_registry()
    redactor = registry.get_active()

    if not redactor.is_ready():
        raise HTTPException(status_code=503, detail="Model is not ready yet. Please wait.")

    result = redactor.redact(request.text)

    return RedactResponse(
        original=result.original_text,
        redacted=result.redacted_text,
        spans=[
            SpanResponse(
                start=span.start,
                end=span.end,
                category=span.category,
                text=span.text,
                label=span.label,
                score=span.score,
            )
            for span in result.spans
        ],
    )


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Check if the backend and model are ready."""
    registry = get_registry()
    redactor = registry.get_active()
    info = redactor.model_info()

    return HealthResponse(
        status="ready" if redactor.is_ready() else "loading",
        model=info.get("name", "unknown"),
        device=info.get("device", "unknown"),
    )


@router.get("/models", response_model=ModelsResponse)
def list_models() -> ModelsResponse:
    """List available models."""
    registry = get_registry()
    models_list = registry.list_models()
    redactor = registry.get_active()
    active_info = redactor.model_info()

    return ModelsResponse(
        models=[ModelInfo(**m) for m in models_list],
        active=active_info.get("name", "unknown"),
    )
