"""Google Photos album download — STUB (v0.6)."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def download_album(creds: Any, album_name: str, dest_dir: Path) -> list[Path]:
    """Download every media item in `album_name` to `dest_dir`.

    Implementation outline (v0.6):
      - Build the photoslibrary v1 service from creds.
      - albums.list() → find album by title → get its id.
      - mediaItems.search({albumId: ...}) with pagination.
      - For each media item: GET item['baseUrl'] + '=d' (full-resolution download).
      - Save to dest_dir using item['filename'] (de-dupe collisions).
      - Return list of saved paths.
    """
    raise NotImplementedError(
        "Google Photos download is planned for v0.6. "
        "See module docstring for the implementation outline."
    )
