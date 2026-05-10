"""CLI entry point — launches the Velum backend and frontend together.

This module is the process orchestrator. The actual engine + backend wiring
lives in :mod:`velum.server`, which the backend subprocess invokes via
``python -m velum.server``. Keeping this layer thin means ``cli.py`` only
imports stdlib + ``httpx`` + ``velum.core.config`` and never crosses the
engine/backend/frontend boundary directly.
"""

from __future__ import annotations

import atexit
import logging
import os
import signal
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from types import FrameType

import httpx

from velum.core.config import Settings

logger = logging.getLogger(__name__)


def wait_for_backend(
    url: str,
    timeout: float = 1800.0,
    is_alive: Callable[[], bool] | None = None,
) -> bool:
    """Poll the backend ``/health`` endpoint until it responds, dies, or times out.

    The default timeout is generous (30 minutes) because the first run downloads
    the ~2.8GB OPF model from HuggingFace, which can take a long time on slow
    connections. The ``is_alive`` callback is the real fail-fast mechanism: when
    it returns ``False`` (e.g. because the backend subprocess crashed), this
    function returns immediately rather than waiting out the timeout.

    Args:
        url: Backend base URL (e.g. ``http://127.0.0.1:8000``).
        timeout: Maximum seconds to wait. Acts as a safety backstop.
        is_alive: Optional callable returning whether the backend process is
            still running. If provided and it returns ``False``, polling stops
            immediately. If ``None``, only the timeout bounds polling.

    Returns:
        ``True`` if the backend responded with HTTP 200 within the bounds,
        ``False`` otherwise.
    """
    start = time.time()
    while time.time() - start < timeout:
        if is_alive is not None and not is_alive():
            return False
        try:
            response = httpx.get(f"{url}/health", timeout=2.0)
            if response.status_code == 200:
                return True
        except httpx.TransportError:
            # Covers ConnectError, ConnectTimeout, ReadTimeout, WriteTimeout,
            # and other transient transport-level failures while the backend
            # subprocess is still starting up / loading the model.
            pass
        time.sleep(1.0)
    return False


def start_backend(settings: Settings) -> subprocess.Popen:
    """Start the FastAPI backend as a subprocess.

    Settings cross the subprocess boundary via the ``VELUM_*`` environment
    variable contract defined in :class:`velum.core.config.Settings`.

    Args:
        settings: Application settings.

    Returns:
        The backend subprocess handle.
    """
    env = {
        **os.environ,
        "VELUM_BACKEND_HOST": settings.backend_host,
        "VELUM_BACKEND_PORT": str(settings.backend_port),
        "VELUM_DEVICE": settings.device,
        "VELUM_MODEL": settings.model_name,
    }
    cmd = [sys.executable, "-m", "velum.server"]
    return subprocess.Popen(cmd, env=env)


def start_frontend(settings: Settings) -> subprocess.Popen:
    """Start the Streamlit frontend as a subprocess.

    Args:
        settings: Application settings.

    Returns:
        The frontend subprocess handle.
    """
    frontend_path = Path(__file__).parent / "frontend" / "app.py"

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(frontend_path),
        "--server.port",
        str(settings.frontend_port),
        "--server.headless",
        "false",
        "--browser.gatherUsageStats",
        "false",
    ]
    return subprocess.Popen(cmd)


def main() -> None:
    """Main entry point for the Velum CLI."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    settings = Settings.from_env()
    processes: list[subprocess.Popen] = []

    def cleanup() -> None:
        """Terminate all subprocesses, escalating to kill if needed."""
        for proc in processes:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()

    atexit.register(cleanup)

    def signal_handler(sig: int, frame: FrameType | None) -> None:
        logger.info("Shutting down Velum...")
        cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Starting Velum backend on %s ...", settings.backend_url)
    backend_proc = start_backend(settings)
    processes.append(backend_proc)

    logger.info(
        "Waiting for model to load (first run downloads ~2.8GB; subsequent runs are fast)..."
    )
    if not wait_for_backend(
        settings.backend_url,
        is_alive=lambda: backend_proc.poll() is None,
    ):
        if backend_proc.poll() is not None:
            logger.error(
                "Backend process exited during startup (code %d). Check logs above.",
                backend_proc.returncode,
            )
        else:
            logger.error("Backend did not become ready within timeout. Check logs above.")
        cleanup()
        sys.exit(1)

    logger.info("Backend ready.")

    logger.info("Starting Velum UI at http://localhost:%d", settings.frontend_port)
    frontend_proc = start_frontend(settings)
    processes.append(frontend_proc)

    try:
        while True:
            if backend_proc.poll() is not None:
                logger.error(
                    "Backend process exited unexpectedly (code %d)",
                    backend_proc.returncode,
                )
                break
            if frontend_proc.poll() is not None:
                logger.info("Frontend process exited (code %d)", frontend_proc.returncode)
                break
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()
