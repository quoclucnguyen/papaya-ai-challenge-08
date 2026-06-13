"""Unit tests for OpenRouter request helpers without network calls."""

from __future__ import annotations

import base64
from types import SimpleNamespace

import pytest
from PIL import Image

from src.utils.llm import LLMClient, LLMResponseError


def _completion(content: str | None, finish_reason: str = "stop") -> SimpleNamespace:
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message, finish_reason=finish_reason)
    return SimpleNamespace(choices=[choice])


def test_parse_plain_and_fenced_json() -> None:
    assert LLMClient._parse_json_response('{"ok": true}') == {"ok": True}
    assert LLMClient._parse_json_response(
        '```json\n{"type": "receipt"}\n```'
    ) == {"type": "receipt"}


def test_image_data_url_contains_png(sample_image: Image.Image) -> None:
    data_url = LLMClient._image_to_data_url(sample_image)
    prefix, encoded = data_url.split(",", 1)
    assert prefix == "data:image/png;base64"
    assert base64.b64decode(encoded).startswith(b"\x89PNG")


def test_openrouter_configuration(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
    client = LLMClient()
    assert client.base_url == "https://openrouter.ai/api/v1"
    assert client.model == "google/gemini-2.5-flash"


def test_process_image_sends_openrouter_compatible_payload(
    sample_image: Image.Image,
) -> None:
    captured: dict = {}

    class Completions:
        def create(self, **kwargs):
            captured.update(kwargs)
            message = SimpleNamespace(content='{"document_type": "receipt"}')
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    client = LLMClient(api_key="test-key")
    client.client = SimpleNamespace(
        chat=SimpleNamespace(completions=Completions())
    )

    result = client.process_image(
        sample_image,
        system_prompt="Classify",
        user_prompt="Return JSON",
    )

    assert result == {"document_type": "receipt"}
    assert captured["response_format"] == {"type": "json_object"}
    user_content = captured["messages"][1]["content"]
    assert user_content[1]["type"] == "image_url"
    assert user_content[1]["image_url"]["url"].startswith(
        "data:image/png;base64,"
    )


def test_retries_truncated_then_succeeds(sample_image: Image.Image) -> None:
    responses = [
        _completion('{"ok": tru', finish_reason="length"),  # truncated
        _completion('{"document_type": "lab_report"}'),  # clean retry
    ]
    seen_requests: list[dict] = []

    class Completions:
        def create(self, **kwargs):
            seen_requests.append(kwargs)
            return responses.pop(0)

    client = LLMClient(api_key="test-key")
    client.client = SimpleNamespace(
        chat=SimpleNamespace(completions=Completions())
    )

    result = client.process_image(sample_image, "sys", "user")
    assert result == {"document_type": "lab_report"}
    assert responses == []  # both attempts consumed
    # First attempt forces JSON mode; retry drops it to avoid model looping.
    assert seen_requests[0]["response_format"] == {"type": "json_object"}
    assert "response_format" not in seen_requests[1]


def test_empty_choices_raises_clear_error(sample_image: Image.Image) -> None:
    class Completions:
        def create(self, **kwargs):
            return SimpleNamespace(choices=None, error={"code": 502})

    client = LLMClient(api_key="test-key", max_attempts=2)
    client.client = SimpleNamespace(
        chat=SimpleNamespace(completions=Completions())
    )

    with pytest.raises(LLMResponseError, match="after 2 attempts"):
        client.process_image(sample_image, "sys", "user")
