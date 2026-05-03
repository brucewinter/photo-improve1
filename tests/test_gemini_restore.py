"""Tests for the gemini_restore step.

We don't hit the live API — just verify config validation, helper functions,
and that the step gives clear errors when prerequisites are missing.
"""
from pathlib import Path
from types import SimpleNamespace

import pytest

from photo_improve.steps.gemini_restore import (
    DEFAULT_MODEL,
    DEFAULT_PROMPT,
    GeminiRestoreStep,
    _extract_image_bytes,
    _extract_text,
    _mime_for,
)


def test_defaults_are_set():
    step = GeminiRestoreStep({})
    assert step.model == DEFAULT_MODEL
    assert step.prompt == DEFAULT_PROMPT
    assert step.api_key_env == "GEMINI_API_KEY"
    assert step.max_retries == 2


def test_options_override_defaults():
    step = GeminiRestoreStep({
        "model": "gemini-test",
        "prompt": "fix it",
        "api_key_env": "MY_KEY",
        "max_retries": 5,
    })
    assert step.model == "gemini-test"
    assert step.prompt == "fix it"
    assert step.api_key_env == "MY_KEY"
    assert step.max_retries == 5


def test_empty_prompt_rejected():
    with pytest.raises(ValueError, match="prompt"):
        GeminiRestoreStep({"prompt": "   "})


def test_negative_retries_rejected():
    with pytest.raises(ValueError, match="max_retries"):
        GeminiRestoreStep({"max_retries": -1})


def test_missing_api_key_gives_clear_error(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    step = GeminiRestoreStep({})
    with pytest.raises(RuntimeError, match="aistudio.google.com"):
        step._resolve_api_key()


def test_literal_api_key_in_config_works(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    step = GeminiRestoreStep({"api_key": "literal-key-from-config"})
    assert step._resolve_api_key() == "literal-key-from-config"


def test_api_key_env_rejects_literal_key():
    # The validator rejects values longer than 50 chars (real keys are ~39 chars
    # but this catches accidentally-pasted credentials of any reasonable length).
    suspiciously_long = "x" * 60
    with pytest.raises(ValueError, match="looks like an actual API key"):
        GeminiRestoreStep({"api_key_env": suspiciously_long})
        

def test_api_key_env_rejects_obviously_wrong_length():
    with pytest.raises(ValueError, match="looks like an actual API key"):
        GeminiRestoreStep({"api_key_env": "X" * 60})


def test_api_key_falls_back_to_google_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "fallback-value")
    step = GeminiRestoreStep({})
    assert step._resolve_api_key() == "fallback-value"


def test_api_key_primary_wins(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "primary")
    monkeypatch.setenv("GOOGLE_API_KEY", "fallback")
    step = GeminiRestoreStep({})
    assert step._resolve_api_key() == "primary"


def test_mime_for():
    assert _mime_for(Path("a.jpg")) == "image/jpeg"
    assert _mime_for(Path("a.JPEG")) == "image/jpeg"
    assert _mime_for(Path("a.png")) == "image/png"
    assert _mime_for(Path("a.tiff")) == "image/tiff"
    assert _mime_for(Path("a.unknown")) == "image/jpeg"


def test_extract_image_bytes_finds_inline_data():
    inline = SimpleNamespace(data=b"PNGBYTES")
    part_with_image = SimpleNamespace(text=None, inline_data=inline)
    part_with_text = SimpleNamespace(text="here you go", inline_data=None)
    content = SimpleNamespace(parts=[part_with_text, part_with_image])
    fake = SimpleNamespace(candidates=[SimpleNamespace(content=content)])
    assert _extract_image_bytes(fake) == b"PNGBYTES"


def test_extract_image_bytes_returns_none_when_absent():
    part = SimpleNamespace(text="sorry, can't do that", inline_data=None)
    content = SimpleNamespace(parts=[part])
    fake = SimpleNamespace(candidates=[SimpleNamespace(content=content)])
    assert _extract_image_bytes(fake) is None


def test_extract_text_collects_chunks():
    parts = [
        SimpleNamespace(text="hello", inline_data=None),
        SimpleNamespace(text="world", inline_data=None),
    ]
    content = SimpleNamespace(parts=parts)
    fake = SimpleNamespace(candidates=[SimpleNamespace(content=content)])
    assert _extract_text(fake) == "hello world"
