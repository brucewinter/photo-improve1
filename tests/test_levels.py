"""Tests for the auto-levels math."""
import numpy as np
import pytest

from photo_improve.steps.levels import LevelsStep, apply_auto_levels


def test_full_range_unchanged():
    """An image already spanning [0, 255] should be (nearly) unchanged."""
    arr = np.tile(np.arange(256, dtype=np.uint8), (10, 1))  # 10x256 grayscale ramp
    out = apply_auto_levels(arr, low_percentile=0.0, high_percentile=100.0,
                             per_channel=False, gamma=1.0)
    assert out.min() == 0
    assert out.max() == 255
    # Gradient should be preserved (monotonic non-decreasing along the row).
    assert np.all(np.diff(out[0].astype(int)) >= 0)


def test_compressed_range_stretched():
    """An image confined to [50, 150] should be stretched to roughly [0, 255]."""
    arr = np.full((20, 20, 3), 100, dtype=np.uint8)
    arr[0, 0] = 50
    arr[-1, -1] = 150
    out = apply_auto_levels(arr, low_percentile=0.0, high_percentile=100.0,
                             per_channel=True, gamma=1.0)
    assert out.min() == 0
    assert out.max() == 255


def test_grayscale_input():
    arr = np.full((10, 10), 128, dtype=np.uint8)
    arr[0, 0] = 64
    arr[-1, -1] = 192
    out = apply_auto_levels(arr, low_percentile=0.0, high_percentile=100.0,
                             per_channel=False, gamma=1.0)
    assert out.shape == arr.shape
    assert out.dtype == np.uint8


def test_gamma_brightens():
    """gamma > 1 should brighten midtones."""
    arr = np.full((10, 10, 3), 128, dtype=np.uint8)
    out = apply_auto_levels(arr, low_percentile=0.0, high_percentile=100.0,
                             per_channel=True, gamma=2.0)
    # With gamma=2, mid-gray (128/255 = 0.50) → 0.50^(1/2) ≈ 0.707 → ~180.
    assert out.mean() > 150


def test_uint8_required():
    arr = np.zeros((4, 4), dtype=np.float32)
    with pytest.raises(TypeError):
        apply_auto_levels(arr, low_percentile=0, high_percentile=100,
                           per_channel=False, gamma=1.0)


def test_step_validates_percentiles():
    with pytest.raises(ValueError, match="low_percentile"):
        LevelsStep({"low_percentile": 90, "high_percentile": 10})


def test_step_validates_gamma():
    with pytest.raises(ValueError, match="gamma"):
        LevelsStep({"gamma": 0})


def test_per_channel_corrects_color_cast():
    """A red-tinted image should have its red pulled down by per-channel levels."""
    # Red channel ranges 100..200; green/blue range 0..255.
    arr = np.zeros((10, 10, 3), dtype=np.uint8)
    arr[..., 0] = np.linspace(100, 200, 100, dtype=np.uint8).reshape(10, 10)
    arr[..., 1] = np.linspace(0, 255, 100, dtype=np.uint8).reshape(10, 10)
    arr[..., 2] = np.linspace(0, 255, 100, dtype=np.uint8).reshape(10, 10)

    out = apply_auto_levels(arr, low_percentile=0.0, high_percentile=100.0,
                             per_channel=True, gamma=1.0)
    # After per-channel levels, red should also span ~0..255.
    assert out[..., 0].min() == 0
    assert out[..., 0].max() == 255
