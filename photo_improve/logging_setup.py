"""Logging configuration."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from photo_improve.config import LoggingConfig


def setup_logging(cfg: LoggingConfig, override_level: str | None = None) -> None:
    """Configure root logger with console + optional file handler."""
    level_name = (override_level or cfg.level).upper()
    level = getattr(logging, level_name, logging.INFO)

    fmt = "%(asctime)s %(levelname)-7s %(name)s — %(message)s"
    formatter = logging.Formatter(fmt, datefmt="%H:%M:%S")

    root = logging.getLogger()
    root.setLevel(level)
    # Remove pre-existing handlers (avoid duplicate output on reconfigure).
    for h in list(root.handlers):
        root.removeHandler(h)

    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(formatter)
    root.addHandler(console)

    if cfg.file:
        log_path = Path(cfg.file).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
