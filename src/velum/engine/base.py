"""Base interface for redaction engines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class RedactionSpan:
    """A single detected PII span in the input text."""

    start: int
    end: int
    category: str
    text: str
    score: float = 1.0

    @property
    def label(self) -> str:
        """Human-readable label for the category (e.g. 'PERSON' from 'private_person')."""
        return self.category.removeprefix("private_").upper()


@dataclass(frozen=True)
class RedactionResult:
    """Result of a redaction operation."""

    original_text: str
    spans: tuple[RedactionSpan, ...]
    redacted_text: str

    @property
    def categories_detected(self) -> set[str]:
        """Set of unique categories found in this result."""
        return {span.category for span in self.spans}


class BaseRedactor(ABC):
    """Abstract interface for PII redaction engines."""

    @abstractmethod
    def redact(self, text: str) -> RedactionResult:
        """Detect and redact PII in the given text.

        Args:
            text: Input text to analyze.

        Returns:
            RedactionResult with original text, detected spans, and redacted text.
        """
        ...

    @abstractmethod
    def is_ready(self) -> bool:
        """Whether the model is loaded and ready for inference."""
        ...

    @abstractmethod
    def model_info(self) -> dict[str, str]:
        """Metadata about the active model.

        Returns:
            Dict with keys: name, version, device, categories.
        """
        ...

    def ensure_loaded(self) -> None:
        """Pre-load any model resources.

        Default: no-op for redactors that load eagerly or have no load step.
        Subclasses with deferred resource loading (e.g. OPFRedactor) override this.
        """
        return
