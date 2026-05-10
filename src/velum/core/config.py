"""Application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Velum application settings.

    All values can be overridden via environment variables prefixed with VELUM_.
    """

    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    frontend_port: int = 8501
    device: str = "cpu"
    model_name: str = "openai/privacy-filter"

    @classmethod
    def from_env(cls) -> Settings:
        """Load settings from environment variables."""
        return cls(
            backend_host=os.environ.get("VELUM_BACKEND_HOST", "127.0.0.1"),
            backend_port=int(os.environ.get("VELUM_BACKEND_PORT", "8000")),
            frontend_port=int(os.environ.get("VELUM_FRONTEND_PORT", "8501")),
            device=os.environ.get("VELUM_DEVICE", "cpu"),
            model_name=os.environ.get("VELUM_MODEL", "openai/privacy-filter"),
        )

    @property
    def backend_url(self) -> str:
        """Full URL for the backend API."""
        return f"http://{self.backend_host}:{self.backend_port}"
