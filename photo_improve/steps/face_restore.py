"""Face restoration step — STUB.

In v0.1 this is a no-op pass-through. The roadmap is to wire it to GFPGAN
in v0.3 (or CodeFormer as an alternative — GFPGAN is gentler, CodeFormer
better on heavily damaged faces).

When implementing:
  1. Add `gfpgan` to pyproject.toml [project.optional-dependencies].ai
  2. Lazy-load the model.
  3. Apply with `strength` blended back over the original.
  4. Output PNG to ctx.work_dir.
"""
from __future__ import annotations

import logging
import shutil
from typing import Any

from photo_improve.steps.base import StepContext, StepResult


log = logging.getLogger(__name__)


class FaceRestoreStep:
    name = "face_restore"

    def __init__(self, options: dict[str, Any]) -> None:
        self.strength = float(options.get("strength", 0.7))
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError(f"face_restore: strength must be in [0, 1], got {self.strength}")

    def process(self, ctx: StepContext) -> StepResult:
        log.warning(
            "face_restore step is a stub in v0.1 — pass-through (planned for v0.3: GFPGAN, strength=%.2f)",
            self.strength,
        )
        out = ctx.work_dir / f"face_restore{ctx.current.suffix}"
        shutil.copy2(ctx.current, out)
        return StepResult(output=out, skipped=True, notes="stub: not yet implemented (v0.3)")
