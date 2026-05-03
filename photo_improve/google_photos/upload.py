"""Google Photos album upload — STUB (v0.6)."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable


def upload_to_album(creds: Any, files: Iterable[Path], dest_album_name: str) -> str:
    """Upload `files` and add them to `dest_album_name` (creating if needed).

    Returns the album id of the destination album.

    Implementation outline (v0.6):
      Per Photos Library API:
        1. POST /v1/uploads with each file's bytes (raw upload), get an uploadToken.
        2. POST /v1/mediaItems:batchCreate with [{ uploadToken }, ...] and albumId.
      Album creation:
        - albums.list() → look for matching title.
        - if missing: albums.create({title: dest_album_name}) → use new id.
      Note: the Photos Library API does NOT allow uploads into existing albums
      that you didn't create via the API. Make a fresh album for restored copies.
    """
    raise NotImplementedError(
        "Google Photos upload is planned for v0.6. "
        "See module docstring for the implementation outline."
    )
