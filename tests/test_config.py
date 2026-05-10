"""Tests for velum.core.config."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from velum.core.config import Settings


def test_defaults_match_spec() -> None:
    """Default Settings values must match the spec."""
    s = Settings()
    assert s.backend_host == "127.0.0.1"
    assert s.backend_port == 8000
    assert s.frontend_port == 8501
    assert s.device == "cpu"
    assert s.model_name == "openai/privacy-filter"


def test_from_env_uses_defaults_when_no_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """from_env() returns the default Settings when no VELUM_ vars are set."""
    for var in (
        "VELUM_BACKEND_HOST",
        "VELUM_BACKEND_PORT",
        "VELUM_FRONTEND_PORT",
        "VELUM_DEVICE",
        "VELUM_MODEL",
    ):
        monkeypatch.delenv(var, raising=False)

    s = Settings.from_env()
    assert s == Settings()


def test_from_env_honors_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    """from_env() reads VELUM_BACKEND_PORT, VELUM_DEVICE, VELUM_MODEL overrides."""
    monkeypatch.setenv("VELUM_BACKEND_PORT", "9100")
    monkeypatch.setenv("VELUM_DEVICE", "cuda")
    monkeypatch.setenv("VELUM_MODEL", "custom/model")

    s = Settings.from_env()
    assert s.backend_port == 9100
    assert s.device == "cuda"
    assert s.model_name == "custom/model"
    # Untouched fields keep defaults
    assert s.backend_host == "127.0.0.1"
    assert s.frontend_port == 8501


def test_backend_url_composes_host_and_port() -> None:
    """backend_url returns http://<host>:<port>."""
    s = Settings(backend_host="0.0.0.0", backend_port=12345)
    assert s.backend_url == "http://0.0.0.0:12345"


def test_settings_is_frozen() -> None:
    """Settings instances are immutable (frozen dataclass)."""
    s = Settings()
    with pytest.raises(FrozenInstanceError):
        s.backend_port = 9999  # type: ignore[misc]
