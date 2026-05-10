"""Model registry for managing available redaction engines."""

from __future__ import annotations

from velum.engine.base import BaseRedactor


class ModelRegistry:
    """Registry of available redaction models.

    For the MVP, this simply holds a single active redactor.
    Future versions will support discovering and switching between models.
    """

    def __init__(self) -> None:
        self._active: BaseRedactor | None = None
        self._models: dict[str, BaseRedactor] = {}

    def register(self, name: str, redactor: BaseRedactor) -> None:
        """Register a redactor under a given name."""
        self._models[name] = redactor
        if self._active is None:
            self._active = redactor

    def get_active(self) -> BaseRedactor:
        """Return the currently active redactor.

        Raises:
            RuntimeError: If no model is registered.
        """
        if self._active is None:
            raise RuntimeError("No redaction model registered. Call register() first.")
        return self._active

    def set_active(self, name: str) -> None:
        """Switch the active model by name.

        Raises:
            KeyError: If the model name is not registered.
        """
        if name not in self._models:
            raise KeyError(f"Model '{name}' not registered. Available: {list(self._models.keys())}")
        self._active = self._models[name]

    def list_models(self) -> list[dict[str, str]]:
        """List all registered models with their info."""
        # TODO(post-MVP): list_models() collapses the registry key into model_info()["name"]
        # because of the dict spread. Harmless with one model in the MVP. Revisit when the
        # /models schema gains a separate "alias" field for multi-model support.
        return [
            {"name": name, **redactor.model_info()}
            for name, redactor in self._models.items()
        ]
