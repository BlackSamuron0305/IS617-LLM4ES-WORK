"""Minimal logging setup shared by the CLI and the runner."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
_configured = False


def setup_logging(level: str | int = "INFO") -> None:
    """Configure the ``hiringaudit`` logger once (console, stderr)."""
    global _configured
    logger = logging.getLogger("hiringaudit")
    logger.setLevel(level if isinstance(level, int) else level.upper())
    if not _configured:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(_FORMAT, datefmt="%H:%M:%S"))
        logger.addHandler(handler)
        logger.propagate = False
        _configured = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"hiringaudit.{name}" if not name.startswith("hiringaudit") else name)


def add_file_handler(path: str | Path) -> logging.Handler:
    """Also log to ``path`` (appending). Returns the handler so callers can remove it."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter(_FORMAT))
    logging.getLogger("hiringaudit").addHandler(handler)
    return handler


def remove_handler(handler: logging.Handler) -> None:
    logging.getLogger("hiringaudit").removeHandler(handler)
    handler.close()
