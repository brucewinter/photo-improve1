"""Google Photos sync — STUB (planned for v0.6).

Public surface:
  - get_credentials(cfg): OAuth installed-app flow → Credentials
  - download_album(creds, name, dest_dir): list + download all media items
  - upload_to_album(creds, files, dest_album_name): upload + add to album

Credentials setup (when v0.6 lands):
  1. Create a project at https://console.cloud.google.com
  2. Enable the Photos Library API
  3. Create OAuth 2.0 client (type: Desktop) → download JSON
  4. Save to config.google_photos.credentials_path
  5. First run will open a browser for consent and cache token to token_path
"""

from photo_improve.google_photos.auth import get_credentials
from photo_improve.google_photos.download import download_album
from photo_improve.google_photos.upload import upload_to_album

__all__ = ["get_credentials", "download_album", "upload_to_album"]
