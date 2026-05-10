"""Shared test fixtures."""

from __future__ import annotations

import re

import pytest

from velum.engine.base import BaseRedactor, RedactionResult, RedactionSpan


class MockRedactor(BaseRedactor):
    """A mock redactor for testing that returns predictable results."""

    def __init__(self) -> None:
        self._ready = True

    def redact(self, text: str) -> RedactionResult:
        """Detect fake PII.

        'Alice Smith' becomes private_person; email patterns become private_email.
        """
        spans: list[RedactionSpan] = []

        # Detect "Alice Smith" pattern
        for match in re.finditer(r"Alice Smith", text):
            spans.append(
                RedactionSpan(
                    start=match.start(),
                    end=match.end(),
                    category="private_person",
                    text=match.group(),
                    score=0.99,
                )
            )

        # Detect email pattern
        for match in re.finditer(r"[\w.-]+@[\w.-]+\.\w+", text):
            spans.append(
                RedactionSpan(
                    start=match.start(),
                    end=match.end(),
                    category="private_email",
                    text=match.group(),
                    score=0.98,
                )
            )

        spans.sort(key=lambda s: s.start)

        # Build redacted text
        redacted = text
        offset = 0
        for span in spans:
            placeholder = f"[{span.label}]"
            redacted = redacted[: span.start + offset] + placeholder + redacted[span.end + offset :]
            offset += len(placeholder) - (span.end - span.start)

        return RedactionResult(
            original_text=text,
            spans=tuple(spans),
            redacted_text=redacted,
        )

    def is_ready(self) -> bool:
        return self._ready

    def model_info(self) -> dict[str, str]:
        return {
            "name": "mock-redactor",
            "version": "0.0.1",
            "device": "cpu",
            "categories": "private_person,private_email",
        }


@pytest.fixture
def mock_redactor() -> MockRedactor:
    """Provide a MockRedactor instance."""
    return MockRedactor()
