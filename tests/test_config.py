"""Tests for config loading and validation."""
from pathlib import Path

import pytest

from photo_improve.config import Config, ConfigError


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "config.yaml"
    p.write_text(content, encoding="utf-8")
    return p


def test_load_minimal(tmp_path):
    cfg_path = _write(tmp_path, """
input_dir: input
output_dir: output
steps:
  - name: levels
    enabled: true
    low_percentile: 1.0
    high_percentile: 99.0
""")
    cfg = Config.load(cfg_path)
    assert len(cfg.steps) == 1
    assert cfg.steps[0].name == "levels"
    assert cfg.steps[0].enabled is True
    assert cfg.steps[0].options["low_percentile"] == 1.0
    # Paths resolve relative to the config file directory.
    assert cfg.input_dir == (tmp_path / "input").resolve()
    assert cfg.output_dir == (tmp_path / "output").resolve()


def test_missing_file(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        Config.load(tmp_path / "does-not-exist.yaml")


def test_step_without_name(tmp_path):
    cfg_path = _write(tmp_path, """
steps:
  - enabled: true
""")
    with pytest.raises(ConfigError, match="missing 'name'"):
        Config.load(cfg_path)


def test_steps_must_be_list(tmp_path):
    cfg_path = _write(tmp_path, """
steps: "not-a-list"
""")
    with pytest.raises(ConfigError, match="must be a list"):
        Config.load(cfg_path)


def test_defaults(tmp_path):
    cfg_path = _write(tmp_path, "steps: []\n")
    cfg = Config.load(cfg_path)
    assert cfg.output.format == "jpeg"
    assert cfg.output.jpeg_quality == 92
    assert cfg.logging.level == "INFO"
    assert cfg.watcher.enabled is False
    assert cfg.google_photos.enabled is False


def test_disabled_step_preserved(tmp_path):
    cfg_path = _write(tmp_path, """
steps:
  - name: upscale
    enabled: false
    scale: 4
""")
    cfg = Config.load(cfg_path)
    assert cfg.steps[0].enabled is False
    assert cfg.steps[0].options["scale"] == 4
