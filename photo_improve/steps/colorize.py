"""Colorize step — STUB.

In v0.1 this is a no-op pass-through. The roadmap is v0.4 — likely DeOldify
or ddcolor (lighter, modern alternative).

When implementing:
  1. Add the chosen colorizer to pyproject.toml [project.optional-dependencies].ai
  2. If only_bw is set, sample saturation from the input; if avg saturation
     exceeds saturation_threshold, skip (treat as already-colored).
  3. Run colorizer, save PNG.

Heuristic for is_bw detection (HSV-based):
    avg_saturation = float(np.asarray(img.convert("HSV"))[..., 1].mean()) / 255.0
    is_bw = avg_saturation < saturation_threshold
"""
from __future__ import annotations

import logging
import shutil
from typing import Any

from photo_improve.steps.base import StepContext, StepResult


log = logging.getLogger(__name__)


class ColorizeStep:
    name = "colorize"

    def __init__(self, options: dict[str, Any]) -> None:
        self.only_bw = bool(options.get("only_bw", True))
        self.saturation_threshold = float(options.get("saturation_threshold", 0.05))

    def process(self, ctx: StepContext) -> StepResult:
        log.warning(
            "colorize step is a stub in v0.1 — pass-through (planned for v0.4: DeOldify/ddcolor; only_bw=%s, threshold=%.3f)",
            self.only_bw, self.saturation_threshold,
        )
        out = ctx.work_dir / f"colorize{ctx.current.suffix}"
        shutil.copy2(ctx.current, out)
        return StepResult(output=out, skipped=True, notes="stub: not yet implemented (v0.4)")
