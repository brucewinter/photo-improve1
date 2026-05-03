"""Load and validate the YAML config."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when config.yaml is missing or invalid."""


@dataclass
class StepConfig:
    name: str
    enabled: bool = True
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class OutputConfig:
    format: str = "jpeg"
    jpeg_quality: int = 92
    preserve_exif: bool = True


@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: str | None = "logs/photo-improve.log"


@dataclass
class WatcherConfig:
    enabled: bool = False
    poll_interval_seconds: int = 5


@dataclass
class GooglePhotosConfig:
    enabled: bool = False
    source_album: str = ""
    destination_album: str = ""
    credentials_path: str = "~/.config/photo-improve/google-credentials.json"
    token_path: str = "~/.config/photo-improve/google-token.json"


@dataclass
class Config:
    input_dir: Path
    output_dir: Path
    steps: list[StepConfig]
    output: OutputConfig
    logging: LoggingConfig
    watcher: WatcherConfig
    google_photos: GooglePhotosConfig

    @classmethod
    def load(cls, path: Path) -> "Config":
        if not path.exists():
            raise ConfigError(
                f"Config file not found: {path}. "
                f"Copy config.example.yaml to config.yaml and edit."
            )
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls.from_dict(data, base_dir=path.parent)

    @classmethod
    def from_dict(cls, data: dict[str, Any], base_dir: Path) -> "Config":
        try:
            input_dir = _resolve_path(data.get("input_dir", "input"), base_dir)
            output_dir = _resolve_path(data.get("output_dir", "output"), base_dir)

            raw_steps = data.get("steps", [])
            if not isinstance(raw_steps, list):
                raise ConfigError("'steps' must be a list")
            steps = [_parse_step(s) for s in raw_steps]

            output = OutputConfig(**(data.get("output") or {}))
            logging_cfg = LoggingConfig(**(data.get("logging") or {}))
            watcher = WatcherConfig(**(data.get("watcher") or {}))
            google_photos = GooglePhotosConfig(**(data.get("google_photos") or {}))

            return cls(
                input_dir=input_dir,
                output_dir=output_dir,
                steps=steps,
                output=output,
                logging=logging_cfg,
                watcher=watcher,
                google_photos=google_photos,
            )
        except TypeError as e:
            raise ConfigError(f"Invalid config: {e}") from e


def _resolve_path(value: str, base_dir: Path) -> Path:
    p = Path(value).expanduser()
    return p if p.is_absolute() else (base_dir / p).resolve()


def _parse_step(raw: Any) -> StepConfig:
    if not isinstance(raw, dict):
        raise ConfigError(f"Each step must be a mapping, got: {raw!r}")
    name = raw.get("name")
    if not name:
        raise ConfigError("Step missing 'name'")
    enabled = bool(raw.get("enabled", True))
    options = {k: v for k, v in raw.items() if k not in {"name", "enabled"}}
    return StepConfig(name=name, enabled=enabled, options=options)
