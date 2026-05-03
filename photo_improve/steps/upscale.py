"""Upscale step — STUB.

In v0.1 this is a no-op pass-through that logs a warning. The roadmap is
to wire it to Real-ESRGAN (CPU-friendly) in v0.2.

When implementing:
  1. Add `realesrgan` to pyproject.toml [project.optional-dependencies].ai
  2. Lazily import the model on first call (downloads ~64MB of weights).
  3. Cache weights under ./models/ (already gitignored).
  4. Run with the configured `model` and `scale`.
  5. Save result to ctx.work_dir as PNG (lossless intermediate).
"""
from __future__ import annotations

import logging
import shutil
from typing import Any

from photo_improve.steps.base import StepContext, StepResult


log = logging.getLogger(__name__)


class UpscaleStep:
    name = "upscale"

    def __init__(self, options: dict[str, Any]) -> None:
        self.model = options.get("model", "realesr-general-x4v3")
        self.scale = int(options.get("scale", 2))

    def process(self, ctx: StepContext) -> StepResult:
        log.warning(
            "upscale step is a stub in v0.1 — pass-through (planned for v0.2: Real-ESRGAN %s @%dx)",
            self.model, self.scale,
        )
        # Pass-through: copy current → work_dir so downstream steps still see a stable file.
        out = ctx.work_dir / f"upscale{ctx.current.suffix}"
        shutil.copy2(ctx.current, out)
        return StepResult(output=out, skipped=True, notes="stub: not yet implemented (v0.2)")
