"""Gemini-powered photo restoration step.

Sends each photo to Google's Gemini 2.5 Flash Image model with a restoration
prompt and saves the returned image. Requires:

    pip install -e ".[gemini]"

And ONE of:
    - setx GEMINI_API_KEY "your-key" (then open a NEW shell), or
    - api_key: <key> directly in config.yaml under this step.

Get a free key at https://aistudio.google.com/apikey
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from PIL import Image

from photo_improve.steps.base import StepContext, StepResult


log = logging.getLogger(__name__)


DEFAULT_MODEL = "gemini-2.5-flash-image"
DEFAULT_PROMPT = (
    "Restore this old scanned photograph: clarify, sharpen, and adjust levels "
    "to match the quality of modern camera technology. Preserve the original "
    "composition, framing, and any people exactly. Do not add or remove "
    "elements. Return only the restored image."
)


class GeminiRestoreStep:
    name = "gemini_restore"

    def __init__(self, options: dict[str, Any]) -> None:
        self.model = str(options.get("model", DEFAULT_MODEL))
        self.prompt = str(options.get("prompt", DEFAULT_PROMPT))
        self.api_key = options.get("api_key")
        self.api_key_env = str(options.get("api_key_env", "GEMINI_API_KEY"))
        self.fallback_api_key_env = str(options.get("fallback_api_key_env", "GOOGLE_API_KEY"))
        self.max_retries = int(options.get("max_retries", 2))
        self.timeout_seconds = int(options.get("timeout_seconds", 60))

        if not self.prompt.strip():
            raise ValueError("gemini_restore: prompt must not be empty")
        if self.max_retries < 0:
            raise ValueError(f"gemini_restore: max_retries must be >= 0, got {self.max_retries}")

        # Defensive: detect the common mistake of pasting the API key into api_key_env.
        if self.api_key_env.startswith("AIza") or len(self.api_key_env) > 50:
            raise ValueError(
                "gemini_restore: api_key_env looks like an actual API key, not an env var name. "
                "Either set api_key_env: GEMINI_API_KEY (and put the key in the env var), "
                "or use api_key: <key> directly (less secure)."
            )

    def _resolve_api_key(self) -> str:
        if self.api_key:
            log.warning(
                "gemini_restore: using api_key from config.yaml. Storing keys in config is "
                "less secure than environment variables - consider api_key_env: GEMINI_API_KEY."
            )
            return str(self.api_key)
        key = os.environ.get(self.api_key_env) or os.environ.get(self.fallback_api_key_env)
        if not key:
            raise RuntimeError(
                f"gemini_restore: no API key found.\n"
                f"  Tried environment variables: {self.api_key_env}, {self.fallback_api_key_env}\n"
                f"  Either:\n"
                f"    1. Set the env var:  setx {self.api_key_env} \"your-key\"  (then open a NEW shell)\n"
                f"    2. Or put it in config.yaml under the gemini_restore step:  api_key: your-key\n"
                f"  Get a free key at https://aistudio.google.com/apikey"
            )
        return key

    def _client(self):
        try:
            from google import genai  # type: ignore
        except ImportError as e:
            raise RuntimeError(
                "gemini_restore: google-genai is not installed. "
                'Run `pip install -e ".[gemini]"` from the project root.'
            ) from e
        return genai.Client(api_key=self._resolve_api_key())

    def process(self, ctx: StepContext) -> StepResult:
        from google.genai import types

        client = self._client()
        image_bytes = Path(ctx.current).read_bytes()
        mime = _mime_for(ctx.current)

        last_err: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=self.model,
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type=mime),
                        self.prompt,
                    ],
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE", "TEXT"],
                    ),
                )
                out_bytes = _extract_image_bytes(response)
                if out_bytes is None:
                    log.warning(
                        "gemini_restore: model returned no image (attempt %d/%d) - text response: %r",
                        attempt + 1, self.max_retries + 1, _extract_text(response)[:200],
                    )
                    last_err = RuntimeError("model returned no image")
                    continue

                out_path = ctx.work_dir / f"gemini_restore_{ctx.current.stem}.png"
                out_path.write_bytes(out_bytes)
                with Image.open(out_path) as im:
                    im.verify()
                return StepResult(output=out_path, notes=f"gemini_restore via {self.model}")
            except Exception as e:
                last_err = e
                log.warning(
                    "gemini_restore: attempt %d/%d failed: %s",
                    attempt + 1, self.max_retries + 1, e,
                )

        log.error("gemini_restore: giving up on %s after %d attempts: %s",
                  ctx.current.name, self.max_retries + 1, last_err)
        return StepResult(output=ctx.current, skipped=True,
                          notes=f"gemini_restore failed: {last_err}")


def _mime_for(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        ".tif": "image/tiff",
        ".tiff": "image/tiff",
    }.get(ext, "image/jpeg")


def _extract_image_bytes(response):
    candidates = getattr(response, "candidates", None) or []
    for cand in candidates:
        content = getattr(cand, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            inline = getattr(part, "inline_data", None)
            if inline is not None:
                data = getattr(inline, "data", None)
                if data:
                    return data if isinstance(data, bytes) else bytes(data)
    return None


def _extract_text(response) -> str:
    chunks: list[str] = []
    for cand in getattr(response, "candidates", None) or []:
        content = getattr(cand, "content", None)
        for part in getattr(content, "parts", None) or []:
            text = getattr(part, "text", None)
            if text:
                chunks.append(text)
    return " ".join(chunks)
