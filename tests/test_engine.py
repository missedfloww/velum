"""Tests for the engine layer."""

from __future__ import annotations

from velum.engine.base import RedactionResult, RedactionSpan


class TestRedactionSpan:
    def test_label_strips_private_prefix(self):
        span = RedactionSpan(start=0, end=5, category="private_person", text="Alice", score=0.99)
        assert span.label == "PERSON"

    def test_label_non_private_category(self):
        span = RedactionSpan(start=0, end=5, category="account_number", text="12345", score=0.95)
        assert span.label == "ACCOUNT_NUMBER"


class TestRedactionResult:
    def test_categories_detected(self):
        result = RedactionResult(
            original_text="test",
            spans=(
                RedactionSpan(start=0, end=1, category="private_person", text="A", score=0.9),
                RedactionSpan(start=2, end=3, category="private_email", text="B", score=0.9),
            ),
            redacted_text="[PERSON] [EMAIL]",
        )
        assert result.categories_detected == {"private_person", "private_email"}

    def test_empty_spans(self):
        result = RedactionResult(
            original_text="no pii here",
            spans=(),
            redacted_text="no pii here",
        )
        assert result.categories_detected == set()


class TestMockRedactor:
    def test_detects_person(self, mock_redactor):
        result = mock_redactor.redact("Hello Alice Smith")
        assert len(result.spans) == 1
        assert result.spans[0].category == "private_person"
        assert result.spans[0].text == "Alice Smith"

    def test_detects_email(self, mock_redactor):
        result = mock_redactor.redact("Contact me at test@example.com please")
        assert len(result.spans) == 1
        assert result.spans[0].category == "private_email"
        assert result.spans[0].text == "test@example.com"

    def test_redacted_text_replaces_spans(self, mock_redactor):
        result = mock_redactor.redact("My name is Alice Smith and email is alice@example.com")
        assert "[PERSON]" in result.redacted_text
        assert "[EMAIL]" in result.redacted_text
        assert "Alice Smith" not in result.redacted_text
        assert result.redacted_text == "My name is [PERSON] and email is [EMAIL]"

    def test_no_pii_returns_original(self, mock_redactor):
        result = mock_redactor.redact("Hello world, no PII here")
        assert result.redacted_text == "Hello world, no PII here"
        assert len(result.spans) == 0

    def test_is_ready(self, mock_redactor):
        assert mock_redactor.is_ready() is True

    def test_model_info(self, mock_redactor):
        info = mock_redactor.model_info()
        assert info["name"] == "mock-redactor"
