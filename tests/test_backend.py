"""Tests for the backend API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from velum.backend.app import create_app
from velum.engine.registry import ModelRegistry


@pytest.fixture
def client(mock_redactor) -> TestClient:
    """Create a test client with mock redactor."""
    registry = ModelRegistry()
    registry.register("mock", mock_redactor)
    app = create_app(registry)
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ready(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["model"] == "mock-redactor"
        assert data["device"] == "cpu"


class TestRedactEndpoint:
    def test_redact_detects_person(self, client):
        response = client.post("/redact", json={"text": "Hello Alice Smith"})
        assert response.status_code == 200
        data = response.json()
        assert data["original"] == "Hello Alice Smith"
        assert "[PERSON]" in data["redacted"]
        assert len(data["spans"]) == 1
        assert data["spans"][0]["category"] == "private_person"
        assert data["spans"][0]["label"] == "PERSON"

    def test_redact_detects_email(self, client):
        response = client.post("/redact", json={"text": "Email: test@mail.com"})
        assert response.status_code == 200
        data = response.json()
        assert "[EMAIL]" in data["redacted"]
        assert data["spans"][0]["category"] == "private_email"

    def test_redact_no_pii(self, client):
        response = client.post("/redact", json={"text": "Hello world"})
        assert response.status_code == 200
        data = response.json()
        assert data["redacted"] == "Hello world"
        assert data["spans"] == []

    def test_redact_empty_text_rejected(self, client):
        response = client.post("/redact", json={"text": ""})
        assert response.status_code == 422

    def test_redact_missing_text(self, client):
        response = client.post("/redact", json={})
        assert response.status_code == 422


class TestModelsEndpoint:
    def test_list_models(self, client):
        response = client.get("/models")
        assert response.status_code == 200
        data = response.json()
        assert len(data["models"]) == 1
        assert data["active"] == "mock-redactor"
