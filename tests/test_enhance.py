"""Tests for the classical enhance step."""
import cv2
import numpy as np
import pytest

from photo_improve.steps.enhance import (
    EnhanceStep,
    apply_bilateral_denoise,
    apply_clahe,
    apply_saturation,
    apply_unsharp_mask,
    apply_white_balance,
)


def _bgr(h=20, w=20, color=(120, 120, 120)) -> np.ndarray:
    """Build a uniform BGR image."""
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[..., 0] = color[0]
    img[..., 1] = color[1]
    img[..., 2] = color[2]
    return img


def test_white_balance_neutralizes_yellow_cast():
    """A yellow-tinted image should have its B (blue-yellow) channel pulled toward neutral."""
    # Yellow cast: high R, high G, low B in BGR (so BGR=(50, 180, 200))
    yellow = _bgr(color=(50, 180, 200))
    out = apply_white_balance(yellow)

    # Convert both to LAB and check that the B channel (yellow-blue axis) of the output
    # is closer to 128 (neutral) than the input's was.
    lab_in = cv2.cvtColor(yellow, cv2.COLOR_BGR2LAB)
    lab_out = cv2.cvtColor(out, cv2.COLOR_BGR2LAB)
    in_b_dist = abs(lab_in[..., 2].mean() - 128)
    out_b_dist = abs(lab_out[..., 2].mean() - 128)
    assert out_b_dist < in_b_dist, f"WB didn't reduce yellow cast: in={in_b_dist}, out={out_b_dist}"


def test_clahe_increases_contrast_on_low_contrast_image():
    img = np.full((100, 100, 3), 128, dtype=np.uint8)
    # Add a very faint gradient
    img[..., 0] = np.linspace(120, 136, 100, dtype=np.uint8)[None, :]
    img[..., 1] = np.linspace(120, 136, 100, dtype=np.uint8)[None, :]
    img[..., 2] = np.linspace(120, 136, 100, dtype=np.uint8)[None, :]
    out = apply_clahe(img, clip_limit=2.0, grid_size=8)
    # CLAHE should expand the dynamic range (std should increase).
    assert out.std() > img.std()


def test_unsharp_mask_increases_high_freq_energy():
    """Sharpening should increase the variance of pixel-to-pixel differences."""
    rng = np.random.default_rng(0)
    img = rng.integers(80, 180, size=(50, 50, 3), dtype=np.uint8)
    img = cv2.GaussianBlur(img, (0, 0), sigmaX=2.0)  # start blurry
    out = apply_unsharp_mask(img, amount=1.0, radius=1.5)

    # High-freq energy via Laplacian variance.
    in_lap = cv2.Laplacian(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
    out_lap = cv2.Laplacian(cv2.cvtColor(out, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
    assert out_lap > in_lap, f"Unsharp didn't add high-freq detail: {in_lap} → {out_lap}"


def test_saturation_boost_increases_saturation():
    # Build an image with definite color.
    img = _bgr(color=(50, 150, 50))  # green in BGR
    out = apply_saturation(img, factor=1.5)
    in_sat = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[..., 1].mean()
    out_sat = cv2.cvtColor(out, cv2.COLOR_BGR2HSV)[..., 1].mean()
    assert out_sat > in_sat


def test_saturation_factor_one_is_identity():
    img = _bgr(color=(50, 150, 50))
    out = apply_saturation(img, factor=1.0)
    # Allow small rounding errors from HSV roundtrip.
    assert np.abs(out.astype(int) - img.astype(int)).max() <= 2


def test_bilateral_smooths_noise_preserves_uniform():
    img = _bgr(color=(120, 120, 120))
    rng = np.random.default_rng(1)
    noisy = np.clip(img.astype(int) + rng.integers(-15, 15, img.shape), 0, 255).astype(np.uint8)
    out = apply_bilateral_denoise(noisy, d=7, sigma_color=35, sigma_space=35)
    assert out.std() < noisy.std()


def test_step_validates_options():
    with pytest.raises(ValueError, match="sharpen_amount"):
        EnhanceStep({"sharpen_amount": 99})
    with pytest.raises(ValueError, match="saturation_boost"):
        EnhanceStep({"saturation_boost": -0.5})


def test_step_all_disabled_is_identity(tmp_path):
    """If every sub-effect is off, the output should match the input (modulo encoding)."""
    from PIL import Image
    from photo_improve.steps.base import StepContext

    src = tmp_path / "src.png"
    work = tmp_path / "work"
    work.mkdir()
    arr = np.full((30, 30, 3), 100, dtype=np.uint8)
    Image.fromarray(arr).save(src)

    step = EnhanceStep({
        "white_balance": False, "clahe": False, "denoise": False,
        "sharpen": False, "saturation": False,
    })
    ctx = StepContext(src=src, current=src, work_dir=work, metadata={})
    result = step.process(ctx)

    out_arr = np.asarray(Image.open(result.output))
    # All sub-effects off → unchanged pixel values.
    assert np.array_equal(out_arr, arr)
