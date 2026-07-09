"""logger_config.py
Centralized logging configuration for Baby Project Manager.
Call setup_logging() once at application startup (main.py).
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path


def setup_logging() -> logging.Logger:
    """Configure application-wide logging.

    Log level is controlled by the ``BPM_LOG_LEVEL`` environment variable.
    Defaults to ``WARNING`` for normal use; set to ``DEBUG`` for development.

    Example::

        BPM_LOG_LEVEL=DEBUG python src/main.py

    Returns:
        The root ``bpm`` logger already configured with handlers.
    """
    log_level_name = os.environ.get("BPM_LOG_LEVEL", "WARNING").upper()
    log_level = getattr(logging, log_level_name, logging.WARNING)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    handlers: list[logging.Handler] = [console_handler]

    if log_level <= logging.DEBUG:
        log_dir = Path.home() / ".baby-project-manager" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(
            log_dir / "bpm_debug.log", encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    root_logger = logging.getLogger("bpm")
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    for handler in handlers:
        root_logger.addHandler(handler)

    # Suppress noisy third-party loggers
    logging.getLogger("pdfplumber").setLevel(logging.WARNING)
    logging.getLogger("pdfminer").setLevel(logging.WARNING)

    return root_logger
