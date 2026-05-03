"""Command-line entry point."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from photo_improve import __version__
from photo_improve.config import Config, ConfigError
from photo_improve.logging_setup import setup_logging
from photo_improve.pipeline import run as pipeline_run


log = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="photo-improve",
        description="Local pipeline for restoring old scanned photos.",
    )
    p.add_argument("--version", action="version", version=f"photo-improve {__version__}")
    p.add_argument(
        "-c", "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to config.yaml (default: ./config.yaml)",
    )
    p.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Override config logging.level",
    )

    sub = p.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Process input/ → output/ once.")
    run_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen, don't write any files.",
    )

    sub.add_parser(
        "watch",
        help="Watch input/ and process new photos as they appear (planned, v0.5).",
    )

    sub.add_parser(
        "sync",
        help="Sync with Google Photos: download album, restore, upload (planned, v0.6).",
    )

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        cfg = Config.load(args.config)
    except ConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    setup_logging(cfg.logging, override_level=args.log_level)
    log.debug("Loaded config from %s", args.config)

    if args.command == "run":
        n = pipeline_run(cfg, dry_run=args.dry_run)
        return 0 if n >= 0 else 1

    if args.command == "watch":
        log.error("`watch` is not implemented yet (planned for v0.5).")
        return 64

    if args.command == "sync":
        log.error("`sync` is not implemented yet (planned for v0.6).")
        return 64

    parser.print_help()
    return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
