"""Step protocol — what every pipeline step implements."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass
class StepContext:
    """Mutable per-photo context threaded through the pipeline."""
    src: Path                       # original input file (unchanged)
    current: Path                   # current working file (may be in a temp dir)
    work_dir: Path                  # scratch directory unique to this photo
    metadata: dict[str, Any]        # arbitrary per-photo annotations (e.g., is_bw)


@dataclass
class StepResult:
    """What a step returns after processing."""
    output: Path                    # path to the file produced by this step
    skipped: bool = False           # true if step intentionally did nothing
    notes: str = ""                 # optional human-readable note for logs


class Step(Protocol):
    """Every step exposes a name and a process method."""

    name: str

    def __init__(self, options: dict[str, Any]) -> None: ...

    def process(self, ctx: StepContext) -> StepResult: ...
