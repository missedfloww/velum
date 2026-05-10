"""Integration tests — full flow from API call to response.

These exercise the backend wiring (FastAPI app + registry + a redactor
implementing BaseRedactor) end-to-end via TestClient. The redactor is always
a mock or a tiny inline subclass — never the real OPFRedactor — so the
verification gate stays fast and fully local.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from velum.backend.app import create_app
from velum.engine.base import BaseRedactor, RedactionResult
from velum.engine.registry import ModelRegistry


@pytest.fixture
def integration_client(mock_redactor) -> TestClient:
    """Full integration client with mock redactor."""
    registry = ModelRegistry()
    registry.register("mock-model", mock_redactor)
    app = create_app(registry)
    return TestClient(app)


class TestFullRedactionFlow:
    def test_health_then_redact(self, integration_client):
        """Test the typical user flow: check health, then redact."""
        # First, check health
        health = integration_client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ready"

        # Then redact
        result = integration_client.post(
            "/redact",
            json={"text": "Contact Alice Smith at alice@example.com"},
        )
        assert result.status_code == 200
        data = result.json()

        # Verify both entities detected
        assert len(data["spans"]) == 2
        categories = {s["category"] for s in data["spans"]}
        assert "private_person" in categories
        assert "private_email" in categories

        # Verify labels are exposed correctly on the wire (closes Task 5
        # reviewer P2: previous test_redact_detects_email did not assert label).
        labels = {s["label"] for s in data["spans"]}
        assert "PERSON" in labels
        assert "EMAIL" in labels

        # Verify redacted text
        assert "Alice Smith" not in data["redacted"]
        assert "alice@example.com" not in data["redacted"]
        assert "[PERSON]" in data["redacted"]
        assert "[EMAIL]" in data["redacted"]

    def test_multiple_redactions(self, integration_client):
        """Test that multiple sequential redactions work."""
        texts = [
            "Alice Smith here",
            "No PII in this text",
            "Reach me at bob@test.org",
        ]
        for text in texts:
            response = integration_client.post("/redact", json={"text": text})
            assert response.status_code == 200

    def test_large_text_input(self, integration_client):
        """Test handling of larger text input."""
        text = "Hello Alice Smith. " * 100
        response = integration_client.post("/redact", json={"text": text})
        assert response.status_code == 200
        data = response.json()
        assert len(data["spans"]) == 100  # 100 mentions of Alice Smith


class _NeverReadyRedactor(BaseRedactor):
    """A redactor that is permanently 'loading'.

    Used to exercise the /redact 503 branch and the /health 'loading' branch
    that are otherwise unreachable in the existing test suite (closes Task 5
    reviewer P2 about dead-looking 503 code in routes.py).
    """

    def redact(self, text: str) -> RedactionResult:  # pragma: no cover - guarded by 503
        raise AssertionError("redact() must not be called when is_ready() is False")

    def is_ready(self) -> bool:
        return False

    def model_info(self) -> dict[str, str]:
        return {
            "name": "never-ready",
            "version": "0.0.1",
            "device": "cpu",
            "categories": "",
        }


class TestNotReadyFlow:
    """Cover the 'model loading' code paths in routes.py."""

    @pytest.fixture
    def not_ready_client(self) -> TestClient:
        registry = ModelRegistry()
        registry.register("never-ready", _NeverReadyRedactor())
        app = create_app(registry)
        return TestClient(app)

    def test_health_reports_loading_when_not_ready(self, not_ready_client):
        response = not_ready_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "loading"
        assert data["model"] == "never-ready"
        assert data["device"] == "cpu"

    def test_redact_returns_503_when_not_ready(self, not_ready_client):
        response = not_ready_client.post("/redact", json={"text": "anything"})
        assert response.status_code == 503
        detail = response.json().get("detail", "")
        assert "not ready" in detail.lower()
