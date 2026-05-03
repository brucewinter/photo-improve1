"""Pipeline orchestrator: runs the configured steps over each input photo."""
from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path
from typing import Iterable

from PIL import Image

from photo_improve.config import Config, OutputConfig
from photo_improve.steps import STEP_REGISTRY, StepContext


log = logging.getLogger(__name__)


# Extensions we'll consider as photos.
PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp"}


def find_photos(input_dir: Path) -> list[Path]:
    """Return sorted list of photo files in input_dir (non-recursive)."""
    if not input_dir.exists():
        return []
    return sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in PHOTO_EXTENSIONS
    )


def run(cfg: Config, *, dry_run: bool = False) -> int:
    """Run the configured pipeline over every photo in input_dir.

    Returns the number of photos processed (or that would be processed in dry-run).
    """
    photos = find_photos(cfg.input_dir)
    if not photos:
        log.warning("No photos found in %s", cfg.input_dir)
        return 0

    enabled_steps = [s for s in cfg.steps if s.enabled]
    log.info(
        "Pipeline plan: %d photo(s), %d step(s) enabled: %s",
        len(photos),
        len(enabled_steps),
        ", ".join(s.name for s in enabled_steps) or "<none>",
    )

    if dry_run:
        for p in photos:
            log.info("[dry-run] would process %s", p.name)
        return len(photos)

    cfg.output_dir.mkdir(parents=True, exist_ok=True)

    # Instantiate steps once (some may load models lazily on first call).
    instantiated = []
    for step_cfg in enabled_steps:
        cls = STEP_REGISTRY.get(step_cfg.name)
        if cls is None:
            log.error("Unknown step in config: %r — skipping", step_cfg.name)
            continue
        instantiated.append(cls(step_cfg.options))

    processed = 0
    for photo in photos:
        try:
            _process_one(photo, instantiated, cfg)
            processed += 1
        except Exception:
            log.exception("Failed to process %s", photo.name)
    log.info("Done. Processed %d/%d photo(s).", processed, len(photos))
    return processed


def _process_one(src: Path, steps: list, cfg: Config) -> None:
    log.info("→ %s", src.name)
    with tempfile.TemporaryDirectory(prefix="photo-improve-") as tmp:
        work_dir = Path(tmp)
        ctx = StepContext(
            src=src,
            current=src,
            work_dir=work_dir,
            metadata={},
        )
        for step in steps:
            result = step.process(ctx)
            if result.skipped:
                log.debug("  · %s skipped (%s)", step.name, result.notes or "no reason given")
                continue
            log.debug("  · %s → %s", step.name, result.output.name)
            ctx.current = result.output

        final_out = _final_output_path(src, cfg)
        _save_final(ctx.current, final_out, cfg.output)


def _final_output_path(src: Path, cfg: Config) -> Path:
    ext = ".jpg" if cfg.output.format == "jpeg" else f".{cfg.output.format}"
    return cfg.output_dir / (src.stem + ext)


def _save_final(working_path: Path, final_out: Path, out_cfg: OutputConfig) -> None:
    """Convert the final working image to the configured output format."""
    final_out.parent.mkdir(parents=True, exist_ok=True)

    # If the working image is already in the right format and no recompression
    # is needed, just copy it. Otherwise, open + save.
    if working_path.suffix.lower() in {".jpg", ".jpeg"} and out_cfg.format == "jpeg":
        shutil.copy2(working_path, final_out)
        return
    if working_path.suffix.lower() == ".png" and out_cfg.format == "png":
        shutil.copy2(working_path, final_out)
        return

    with Image.open(working_path) as img:
        save_kwargs: dict = {}
        if out_cfg.format == "jpeg":
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            save_kwargs["quality"] = out_cfg.jpeg_quality
            save_kwargs["optimize"] = True
            if out_cfg.preserve_exif:
                exif = img.info.get("exif")
                if exif:
                    save_kwargs["exif"] = exif
        img.save(final_out, format=out_cfg.format.upper(), **save_kwargs)
