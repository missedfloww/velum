"""Tests for the velum.server module (engine + backend composition layer).

These tests stub out the heavy pieces (model load, uvicorn) so they stay
fast and don't actually open sockets or download model weights.
"""

from __future__ import annotations

import importlib

import pytest


def test_server_module_imports() -> None:
    """velum.server can be imported without crashing."""
    server = importlib.import_module("velum.server")
    assert server is not None


def test_server_main_is_callable() -> None:
    """velum.server exposes a callable main()."""
    server = importlib.import_module("velum.server")
    assert hasattr(server, "main")
    assert callable(server.main)


def test_server_main_wires_registry_and_runs_uvicorn(monkeypatch, mock_redactor) -> None:
    """main() should construct a registry, register a redactor, and call uvicorn.run.

    Stubs out OPFRedactor (so no model download) and uvicorn.run (so no socket).
    Also captures the registry passed to create_app to lock down that the
    redactor main() built is actually the one that gets registered.
    """
    import velum.server as server
    from velum.backend.app import create_app as original_create_app

    # Force settings via env
    monkeypatch.setenv("VELUM_BACKEND_HOST", "127.0.0.1")
    monkeypatch.setenv("VELUM_BACKEND_PORT", "9123")
    monkeypatch.setenv("VELUM_DEVICE", "cpu")
    monkeypatch.setenv("VELUM_MODEL", "test-model")

    # Replace OPFRedactor with a factory that returns mock_redactor
    construction_args: dict[str, object] = {}

    def fake_opf(device: str = "cpu"):
        construction_args["device"] = device
        return mock_redactor

    monkeypatch.setattr(server, "OPFRedactor", fake_opf)

    # Capture the registry handed to create_app
    captured: dict[str, object] = {}

    def fake_create_app(registry):
        captured["registry"] = registry
        return original_create_app(registry)

    monkeypatch.setattr(server, "create_app", fake_create_app)

    # Capture uvicorn.run calls
    run_calls: list[dict[str, object]] = []

    class FakeUvicorn:
        @staticmethod
        def run(app, **kwargs):
            run_calls.append({"app": app, **kwargs})

    monkeypatch.setitem(__import__("sys").modules, "uvicorn", FakeUvicorn)

    server.main()

    assert construction_args["device"] == "cpu"
    assert len(run_calls) == 1
    call = run_calls[0]
    assert call["host"] == "127.0.0.1"
    assert call["port"] == 9123
    # The app should be a FastAPI instance
    from fastapi import FastAPI

    assert isinstance(call["app"], FastAPI)

    # The registry main() built must contain the redactor we mocked, registered
    # under the model_name from settings (VELUM_MODEL=test-model).
    registry = captured["registry"]
    active = registry.get_active()
    assert active is mock_redactor
    # And the registry's bookkeeping records the configured name.
    assert "test-model" in registry._models  # type: ignore[attr-defined]
    assert registry._models["test-model"] is mock_redactor  # type: ignore[attr-defined]


@pytest.mark.parametrize("env_var", ["VELUM_BACKEND_HOST", "VELUM_BACKEND_PORT"])
def test_server_uses_settings_from_env(env_var: str) -> None:
    """Sanity check that Settings.from_env still drives the server (smoke)."""
    # This is implicitly covered by the test above; included as a discoverable
    # marker that the contract is env-var driven.
    from velum.core.config import Settings

    s = Settings.from_env()
    assert hasattr(s, "backend_host")
    assert hasattr(s, "backend_port")
