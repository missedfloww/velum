"""Tests for velum.cli — only fast, side-effect-free helpers.

We do not exercise the subprocess management code (start_backend,
start_frontend, main) here; that is integration-level and covered by
manual smoke tests per the plan.
"""

from __future__ import annotations

import httpx


class _FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


def test_wait_for_backend_returns_true_when_backend_responds(monkeypatch) -> None:
    """wait_for_backend returns True as soon as /health returns 200."""
    from velum import cli

    def fake_get(url: str, timeout: float = 0.0) -> _FakeResponse:
        assert url.endswith("/health")
        return _FakeResponse(200)

    monkeypatch.setattr(cli.httpx, "get", fake_get)

    assert cli.wait_for_backend("http://127.0.0.1:8000", timeout=1.0) is True


def test_wait_for_backend_returns_false_on_timeout(monkeypatch) -> None:
    """wait_for_backend returns False when the backend never becomes reachable."""
    from velum import cli

    def fake_get(url: str, timeout: float = 0.0):
        raise httpx.ConnectError("nope")

    # Avoid the real 1-second sleep between polls
    monkeypatch.setattr(cli.time, "sleep", lambda _s: None)
    monkeypatch.setattr(cli.httpx, "get", fake_get)

    assert cli.wait_for_backend("http://127.0.0.1:8000", timeout=0.1) is False


def test_wait_for_backend_handles_read_timeout(monkeypatch) -> None:
    """ReadTimeout is also treated as a transient failure, not an error."""
    from velum import cli

    calls = {"n": 0}

    def fake_get(url: str, timeout: float = 0.0):
        calls["n"] += 1
        if calls["n"] < 2:
            raise httpx.ReadTimeout("slow")
        return _FakeResponse(200)

    monkeypatch.setattr(cli.time, "sleep", lambda _s: None)
    monkeypatch.setattr(cli.httpx, "get", fake_get)

    assert cli.wait_for_backend("http://127.0.0.1:8000", timeout=5.0) is True
    assert calls["n"] >= 2


def test_wait_for_backend_handles_connect_timeout(monkeypatch) -> None:
    """ConnectTimeout (distinct from ConnectError) must be treated as transient.

    Regression test: on Windows, attempting to connect to a port whose listener
    has not yet bound can raise httpx.ConnectTimeout rather than ConnectError.
    """
    from velum import cli

    calls = {"n": 0}

    def fake_get(url: str, timeout: float = 0.0):
        calls["n"] += 1
        if calls["n"] < 2:
            raise httpx.ConnectTimeout("timed out")
        return _FakeResponse(200)

    monkeypatch.setattr(cli.time, "sleep", lambda _s: None)
    monkeypatch.setattr(cli.httpx, "get", fake_get)

    assert cli.wait_for_backend("http://127.0.0.1:8000", timeout=5.0) is True
    assert calls["n"] >= 2


def test_wait_for_backend_returns_false_when_is_alive_reports_dead(monkeypatch) -> None:
    """If is_alive() returns False, give up immediately without waiting for timeout.

    This is the contract that lets `main()` detect a crashed backend subprocess
    rather than waiting the full timeout for a process that will never respond.
    """
    from velum import cli

    def fake_get(url: str, timeout: float = 0.0):
        raise httpx.ConnectError("not yet")

    monkeypatch.setattr(cli.time, "sleep", lambda _s: None)
    monkeypatch.setattr(cli.httpx, "get", fake_get)

    # Long timeout but is_alive=False on first check should return immediately.
    assert (
        cli.wait_for_backend(
            "http://127.0.0.1:8000",
            timeout=600.0,
            is_alive=lambda: False,
        )
        is False
    )


def test_wait_for_backend_keeps_polling_while_alive(monkeypatch) -> None:
    """When is_alive() returns True, polling continues until /health responds."""
    from velum import cli

    calls = {"n": 0}

    def fake_get(url: str, timeout: float = 0.0):
        calls["n"] += 1
        if calls["n"] < 3:
            raise httpx.ConnectError("not yet")
        return _FakeResponse(200)

    monkeypatch.setattr(cli.time, "sleep", lambda _s: None)
    monkeypatch.setattr(cli.httpx, "get", fake_get)

    assert (
        cli.wait_for_backend(
            "http://127.0.0.1:8000",
            timeout=5.0,
            is_alive=lambda: True,
        )
        is True
    )


def test_cli_main_is_callable() -> None:
    """cli.main exists and is callable (smoke)."""
    from velum import cli

    assert callable(cli.main)
