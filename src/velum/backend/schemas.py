"""Pydantic schemas for API request/response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RedactRequest(BaseModel):
    """Request body for the /redact endpoint."""

    text: str = Field(..., min_length=1, max_length=500_000, description="Text to redact")


class SpanResponse(BaseModel):
    """A single detected PII span."""

    start: int
    end: int
    category: str
    text: str
    label: str
    score: float


class RedactResponse(BaseModel):
    """Response from the /redact endpoint."""

    original: str
    redacted: str
    spans: list[SpanResponse]


class HealthResponse(BaseModel):
    """Response from the /health endpoint."""

    status: str
    model: str
    device: str


class ModelInfo(BaseModel):
    """Information about a registered model."""

    name: str
    version: str
    device: str
    categories: str


class ModelsResponse(BaseModel):
    """Response from the /models endpoint."""

    models: list[ModelInfo]
    active: str
