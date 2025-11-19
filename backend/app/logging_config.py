"""
Centralized logging configuration for the Agentic Research backend.

Uvicorn's default logging config only installs handlers for its own loggers,
leaving the root logger at WARNING with no handlers. That prevents INFO-level
logs from application modules (including the lifecycle breadcrumbs requested for
the ResearcherAgent) from ever reaching stdout or error.txt.

This module installs a root StreamHandler that emits at INFO level by default
and keeps the setup idempotent so reloading (e.g., uvicorn --reload) does not
register duplicate handlers.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Optional

LOG_FORMAT = os.getenv(
    "AGENTIC_LOG_FORMAT",
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
DATE_FORMAT = os.getenv("AGENTIC_LOG_DATEFMT", "%H:%M:%S")
DEFAULT_LEVEL = os.getenv("AGENTIC_LOG_LEVEL", "INFO").upper()

_CONFIGURED = False


def configure_logging(level: Optional[str] = None) -> None:
    """
    Ensure the root logger emits INFO-level application logs.

    Args:
        level: Optional override for log level string (e.g., "DEBUG").
    """
    global _CONFIGURED
    target_level_name = level or DEFAULT_LEVEL
    try:
        target_level = getattr(logging, target_level_name, logging.INFO)
    except AttributeError:  # pragma: no cover - defensive fallback
        target_level = logging.INFO

    root_logger = logging.getLogger()
    root_logger.setLevel(target_level)

    # Install a stdout handler if none exist, otherwise normalize levels.
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(target_level)
        handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        root_logger.addHandler(handler)
    else:
        for handler in root_logger.handlers:
            handler.setLevel(target_level)
            if handler.formatter is None:
                handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

    logging.captureWarnings(True)
    _CONFIGURED = True


def ensure_logging() -> None:
    """
    Convenience wrapper so modules can import and guarantee configuration.
    """
    if not _CONFIGURED:
        configure_logging()

