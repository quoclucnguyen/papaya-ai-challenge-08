"""OpenRouter vision client using the OpenAI-compatible API."""

from __future__ import annotations

import base64
import io
import json
import os
from typing import Any, Literal, cast, overload

import dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from PIL import Image

dotenv.load_dotenv()

ImageMediaType = Literal["image/jpeg", "image/png", "image/gif", "image/webp"]


class LLMResponseError(RuntimeError):
    """Raised when OpenRouter returns a response we cannot use."""


class LLMRetryableError(LLMResponseError):
    """A transient response problem worth retrying (empty/truncated/invalid)."""


class LLMClient:
    """Small wrapper around OpenRouter chat completions."""

    DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = "google/gemini-2.5-flash"
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_MAX_ATTEMPTS = 3

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        base_url: str | None = None,
        max_attempts: int | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not found. Set it in .env or pass api_key."
            )

        self.model = model or os.getenv("OPENROUTER_MODEL") or self.DEFAULT_MODEL
        self.max_tokens = max_tokens or int(
            os.getenv("OPENROUTER_MAX_TOKENS", str(self.DEFAULT_MAX_TOKENS))
        )
        self.base_url = (
            base_url
            or os.getenv("OPENROUTER_BASE_URL")
            or self.DEFAULT_BASE_URL
        )
        self.max_attempts = max_attempts or int(
            os.getenv("OPENROUTER_MAX_ATTEMPTS", str(self.DEFAULT_MAX_ATTEMPTS))
        )

        default_headers: dict[str, str] = {}
        app_url = os.getenv("OPENROUTER_APP_URL")
        app_title = os.getenv("OPENROUTER_APP_TITLE")
        if app_url:
            default_headers["HTTP-Referer"] = app_url
        if app_title:
            default_headers["X-OpenRouter-Title"] = app_title

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            default_headers=default_headers or None,
            max_retries=2,
            timeout=120.0,
        )

    @overload
    def process_image(
        self,
        image: Image.Image,
        system_prompt: str,
        user_prompt: str,
        output_format: Literal["json"] = "json",
    ) -> dict[str, Any]: ...

    @overload
    def process_image(
        self,
        image: Image.Image,
        system_prompt: str,
        user_prompt: str,
        output_format: Literal["text"],
    ) -> str: ...

    def process_image(
        self,
        image: Image.Image,
        system_prompt: str,
        user_prompt: str,
        output_format: Literal["text", "json"] = "json",
    ) -> str | dict[str, Any]:
        """Process one document image."""
        return self.process_images(
            images=[image],
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            output_format=output_format,
        )

    @overload
    def process_images(
        self,
        images: list[Image.Image],
        system_prompt: str,
        user_prompt: str,
        output_format: Literal["json"] = "json",
    ) -> dict[str, Any]: ...

    @overload
    def process_images(
        self,
        images: list[Image.Image],
        system_prompt: str,
        user_prompt: str,
        output_format: Literal["text"],
    ) -> str: ...

    def process_images(
        self,
        images: list[Image.Image],
        system_prompt: str,
        user_prompt: str,
        output_format: Literal["text", "json"] = "json",
    ) -> str | dict[str, Any]:
        """Process all pages in one OpenRouter request."""
        if not images:
            raise ValueError("At least one image is required")

        content: list[dict[str, Any]] = [{"type": "text", "text": user_prompt}]
        for image in images:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": self._image_to_data_url(image),
                        "detail": "high",
                    },
                }
            )

        messages = cast(
            list[ChatCompletionMessageParam],
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
        )
        request: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": 0,
        }
        if output_format == "json":
            request["response_format"] = {"type": "json_object"}

        last_error: LLMRetryableError | None = None
        for attempt in range(1, self.max_attempts + 1):
            attempt_request = dict(request)
            # Escalation: some small vision models loop and truncate under forced
            # JSON mode. After the first attempt, drop response_format and rely on
            # the prompt plus lenient JSON parsing instead.
            if attempt > 1:
                attempt_request.pop("response_format", None)
            try:
                return self._attempt_completion(attempt_request, output_format)
            except LLMRetryableError as exc:
                last_error = exc
                continue
        raise LLMResponseError(
            f"OpenRouter request failed after {self.max_attempts} attempts: "
            f"{last_error}"
        )

    def _attempt_completion(
        self,
        request: dict[str, Any],
        output_format: Literal["text", "json"],
    ) -> str | dict[str, Any]:
        """Run one completion call, raising LLMRetryableError on bad output."""
        completion = self.client.chat.completions.create(**request)

        choices = getattr(completion, "choices", None)
        if not choices:
            error = getattr(completion, "error", None)
            raise LLMRetryableError(
                f"response had no choices (provider error: {error})"
            )

        choice = choices[0]
        if getattr(choice, "finish_reason", None) == "length":
            raise LLMRetryableError(
                "response truncated at max_tokens (finish_reason=length)"
            )

        response_text = choice.message.content
        if not response_text:
            raise LLMRetryableError("response did not contain text content")

        if output_format == "text":
            return cast(str, response_text)
        try:
            return self._parse_json_response(response_text)
        except ValueError as exc:
            raise LLMRetryableError(str(exc)) from exc

    @classmethod
    def _image_to_data_url(cls, image: Image.Image) -> str:
        media_type = cls._get_media_type(image)
        encoded = base64.b64encode(cls._image_to_bytes(image)).decode("ascii")
        return f"data:{media_type};base64,{encoded}"

    @staticmethod
    def _parse_json_response(response_text: str) -> dict[str, Any]:
        """Parse an object from JSON mode or a fenced fallback response."""
        json_text = response_text.strip()
        if json_text.startswith("```"):
            first_newline = json_text.find("\n")
            closing_fence = json_text.rfind("```")
            if first_newline != -1 and closing_fence > first_newline:
                json_text = json_text[first_newline + 1 : closing_fence].strip()

        try:
            parsed = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse JSON response: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ValueError("JSON response must be an object")
        return cast(dict[str, Any], parsed)

    @staticmethod
    def _image_to_bytes(image: Image.Image) -> bytes:
        buffer = io.BytesIO()
        image.convert("RGB").save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def _get_media_type(image: Image.Image) -> ImageMediaType:
        if image.format == "JPEG":
            return "image/jpeg"
        if image.format == "GIF":
            return "image/gif"
        if image.format == "WEBP":
            return "image/webp"
        return "image/png"


def get_default_client() -> LLMClient:
    """Create an OpenRouter client from environment variables."""
    return LLMClient()
