"""Google Photos OAuth — STUB (v0.6)."""
from __future__ import annotations

from photo_improve.config import GooglePhotosConfig


SCOPES = [
    "https://www.googleapis.com/auth/photoslibrary.readonly",
    "https://www.googleapis.com/auth/photoslibrary.appendonly",
]


def get_credentials(cfg: GooglePhotosConfig):
    """Run OAuth installed-app flow, cache token, return Credentials.

    Implementation outline (v0.6):
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow

        token_path = Path(cfg.token_path).expanduser()
        creds = None
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(Path(cfg.credentials_path).expanduser()), SCOPES,
                )
                creds = flow.run_local_server(port=0)
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(creds.to_json())
        return creds
    """
    raise NotImplementedError(
        "Google Photos auth is planned for v0.6. "
        "See README roadmap for the implementation outline."
    )
