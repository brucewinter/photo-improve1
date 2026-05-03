"""Classical photo enhancement step.

Stacks a series of well-tuned image-processing operations to give old scans
a modern look without needing AI models. Each sub-effect is independently
toggleable so you can dial it in for your photos.

Order of operations matters and is fixed:
  1. White balance (corrects yellow/sepia cast on aged photos)
  2. CLAHE (local contrast — adds 'punch' without crushing highlights)
  3. Bilateral denoise (smooths scan grain, keeps edges crisp)
  4. Unsharp mask (clarity and detail)
  5. Saturation boost (modern photos are more saturated)

Implemented with OpenCV for speed; runs instantly on CPU.
"""
from __future__ import annotations

import logging
from typing import Any

import cv2
import numpy as np
from PIL import Image

from photo_improve.steps.base import StepContext, StepResult


log = logging.getLogger(__name__)


class EnhanceStep:
    name = "enhance"

    def __init__(self, options: dict[str, Any]) -> None:
        # White balance.
        self.white_balance = bool(options.get("white_balance", True))

        # CLAHE: local contrast.
        self.clahe = bool(options.get("clahe", True))
        self.clahe_clip_limit = float(options.get("clahe_clip_limit", 2.0))
        self.clahe_grid_size = int(options.get("clahe_grid_size", 8))

        # Bilateral denoise.
        self.denoise = bool(options.get("denoise", True))
        self.denoise_strength = int(options.get("denoise_strength", 7))   # diameter
        self.denoise_sigma_color = int(options.get("denoise_sigma_color", 35))
        self.denoise_sigma_space = int(options.get("denoise_sigma_space", 35))

        # Unsharp mask.
        self.sharpen = bool(options.get("sharpen", True))
        self.sharpen_amount = float(options.get("sharpen_amount", 0.6))    # 0..2
        self.sharpen_radius = float(options.get("sharpen_radius", 1.5))    # gaussian sigma

        # Saturation.
        self.saturation = bool(options.get("saturation", True))
        self.saturation_boost = float(options.get("saturation_boost", 1.15))  # 1.0 = no change

        if not 0.0 <= self.sharpen_amount <= 5.0:
            raise ValueError(f"enhance: sharpen_amount must be in [0, 5], got {self.sharpen_amount}")
        if self.saturation_boost < 0:
            raise ValueError(f"enhance: saturation_boost must be >= 0, got {self.saturation_boost}")

    def process(self, ctx: StepContext) -> StepResult:
        with Image.open(ctx.current) as img:
            mode = img.mode
            if mode != "RGB":
                img = img.convert("RGB")
            arr = np.asarray(img, dtype=np.uint8)

        # OpenCV uses BGR.
        bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        applied: list[str] = []

        if self.white_balance:
            bgr = apply_white_balance(bgr)
            applied.append("wb")
        if self.clahe:
            bgr = apply_clahe(bgr, clip_limit=self.clahe_clip_limit, grid_size=self.clahe_grid_size)
            applied.append("clahe")
        if self.denoise:
            bgr = apply_bilateral_denoise(
                bgr, d=self.denoise_strength,
                sigma_color=self.denoise_sigma_color,
                sigma_space=self.denoise_sigma_space,
            )
            applied.append("denoise")
        if self.sharpen:
            bgr = apply_unsharp_mask(bgr, amount=self.sharpen_amount, radius=self.sharpen_radius)
            applied.append("sharpen")
        if self.saturation:
            bgr = apply_saturation(bgr, factor=self.saturation_boost)
            applied.append("sat")

        out_arr = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

        out_path = ctx.work_dir / f"enhance{ctx.current.suffix or '.png'}"
        Image.fromarray(out_arr, mode="RGB").save(out_path)
        return StepResult(output=out_path, notes=f"enhance: {'+'.join(applied) or 'no-op'}")


# --- Pure functions (testable) ---------------------------------------------------


def apply_white_balance(bgr: np.ndarray) -> np.ndarray:
    """LAB-based white balance: shift A and B channels toward neutral.

    Old scans often have a yellow/orange cast — yellowed paper, faded dyes.
    Computing the mean of the A and B channels in LAB space and subtracting it
    pulls the photo back toward neutral grays without affecting luminance.
    """
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    L, A, B = cv2.split(lab)
    # Pull A and B toward 128 (neutral) by their distance from neutral, scaled by L.
    a_mean = A.mean()
    b_mean = B.mean()
    A = A - (a_mean - 128) * (L / 255.0) * 1.1
    B = B - (b_mean - 128) * (L / 255.0) * 1.1
    out = cv2.merge([L, A, B])
    out = np.clip(out, 0, 255).astype(np.uint8)
    return cv2.cvtColor(out, cv2.COLOR_LAB2BGR)


def apply_clahe(bgr: np.ndarray, *, clip_limit: float, grid_size: int) -> np.ndarray:
    """Contrast Limited Adaptive Histogram Equalization on the L channel.

    Operates only on luminance (L in LAB) so colors aren't shifted.
    """
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    L, A, B = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(grid_size, grid_size))
    L = clahe.apply(L)
    return cv2.cvtColor(cv2.merge([L, A, B]), cv2.COLOR_LAB2BGR)


def apply_bilateral_denoise(
    bgr: np.ndarray, *, d: int, sigma_color: int, sigma_space: int
) -> np.ndarray:
    """Edge-preserving denoise. Good for scan grain."""
    return cv2.bilateralFilter(bgr, d=d, sigmaColor=sigma_color, sigmaSpace=sigma_space)


def apply_unsharp_mask(bgr: np.ndarray, *, amount: float, radius: float) -> np.ndarray:
    """Unsharp mask: blurred = blur(image); out = image + amount * (image - blurred)."""
    blurred = cv2.GaussianBlur(bgr, ksize=(0, 0), sigmaX=radius)
    sharpened = cv2.addWeighted(bgr, 1.0 + amount, blurred, -amount, 0)
    return np.clip(sharpened, 0, 255).astype(np.uint8)


def apply_saturation(bgr: np.ndarray, *, factor: float) -> np.ndarray:
    """Multiply HSV saturation by factor (1.0 = no change, 1.2 = +20%)."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * factor, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
