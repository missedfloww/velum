"""Velum server entry point — wires engine + backend and runs uvicorn.

Run as: ``python -m velum.server``

Settings are read from environment variables (see :class:`velum.core.config.Settings`).
This module is the composition layer between the engine and the backend; it is
intentionally importable so the wiring is type-checked and testable.
"""

from __future__ import annotations

import logging

from velum.backend.app import create_app
from velum.core.config import Settings
from velum.engine.opf_redactor import OPFRedactor
from velum.engine.registry import ModelRegistry

logger = logging.getLogger(__name__)


def main() -> None:
    """Construct the registry, load the model, and run uvicorn."""
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    settings = Settings.from_env()

    logger.info("Loading OPF model on device=%s ...", settings.device)
    registry = ModelRegistry()
    redactor = OPFRedactor(device=settings.device)
    redactor.ensure_loaded()
    registry.register(settings.model_name, redactor)

    app = create_app(registry)

    logger.info("Starting uvicorn on %s:%d", settings.backend_host, settings.backend_port)
    uvicorn.run(
        app,
        host=settings.backend_host,
        port=settings.backend_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
