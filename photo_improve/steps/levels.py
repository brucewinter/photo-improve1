"""Auto-levels step: percentile-based histogram stretch.

Mimics the "auto levels" found in Photoshop / GIMP: for each color channel
(or for luminance if per_channel is False), find the value at low_percentile
and high_percentile, then linearly remap that range to [0, 255]. Optionally
applies a gamma correction.

This step is implemented end-to-end in v0.1 and uses no AI models.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from photo_improve.steps.base import StepContext, StepResult


log = logging.getLogger(__name__)


class LevelsStep:
    name = "levels"

    def __init__(self, options: dict[str, Any]) -> None:
        self.low_percentile = float(options.get("low_percentile", 0.5))
        self.high_percentile = float(options.get("high_percentile", 99.5))
        self.per_channel = bool(options.get("per_channel", True))
        self.gamma = float(options.get("gamma", 1.0))

        if not 0.0 <= self.low_percentile < self.high_percentile <= 100.0:
            raise ValueError(
                f"levels: low_percentile ({self.low_percentile}) must be "
                f"< high_percentile ({self.high_percentile}), both in [0, 100]."
            )
        if self.gamma <= 0:
            raise ValueError(f"levels: gamma must be > 0, got {self.gamma}")

    def process(self, ctx: StepContext) -> StepResult:
        with Image.open(ctx.current) as img:
            mode = img.mode
            if mode not in ("RGB", "L"):
                img = img.convert("RGB")
                mode = "RGB"
            arr = np.asarray(img, dtype=np.uint8)

        out_arr = apply_auto_levels(
            arr,
            low_percentile=self.low_percentile,
            high_percentile=self.high_percentile,
            per_channel=self.per_channel,
            gamma=self.gamma,
        )

        out_path = ctx.work_dir / f"levels{ctx.current.suffix or '.png'}"
        Image.fromarray(out_arr, mode=mode).save(out_path)
        return StepResult(output=out_path, notes=f"levels p={self.low_percentile}/{self.high_percentile} γ={self.gamma}")


def apply_auto_levels(
    arr: np.ndarray,
    *,
    low_percentile: float,
    high_percentile: float,
    per_channel: bool,
    gamma: float,
) -> np.ndarray:
    """Pure function — exposed for testing.

    Input: HxWx3 uint8 (RGB) or HxW uint8 (grayscale).
    Returns: same shape and dtype.
    """
    if arr.dtype != np.uint8:
        raise TypeError(f"apply_auto_levels expects uint8, got {arr.dtype}")

    f = arr.astype(np.float32)

    if f.ndim == 2 or not per_channel:
        # Treat the whole image (or each channel uniformly) using a single set of bounds.
        if f.ndim == 2:
            lo, hi = np.percentile(f, [low_percentile, high_percentile])
            f = _stretch(f, lo, hi)
        else:
            # Compute bounds on luminance, apply the same shift+scale to all channels
            # so we don't introduce a color cast.
            lum = 0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2]
            lo, hi = np.percentile(lum, [low_percentile, high_percentile])
            f = _stretch(f, lo, hi)
    else:
        # Per-channel: each channel gets its own bounds (corrects color casts).
        for c in range(f.shape[-1]):
            lo, hi = np.percentile(f[..., c], [low_percentile, high_percentile])
            f[..., c] = _stretch(f[..., c], lo, hi)

    if gamma != 1.0:
        # Gamma correction in [0, 1].
        f = np.clip(f, 0, 255) / 255.0
        f = np.power(f, 1.0 / gamma) * 255.0

    return np.clip(f, 0, 255).astype(np.uint8)


def _stretch(channel: np.ndarray, lo: float, hi: float) -> np.ndarray:
    """Linearly remap [lo, hi] → [0, 255]; clamp outside that."""
    if hi <= lo:
        return channel  # degenerate: nothing to do
    scale = 255.0 / (hi - lo)
    return (channel - lo) * scale
