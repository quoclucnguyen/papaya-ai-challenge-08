"""Base extractor class for all document types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any

from PIL import Image

from src.models.base import ValidationError
from src.prompts.extraction import BASE_EXTRACTION_SYSTEM_PROMPT
from src.utils.llm import LLMClient


class BaseExtractor(ABC):
    """Base class for document-specific extractors."""

    def __init__(self, client: LLMClient | None = None):
        """
        Initialize extractor.

        Args:
            client: LLM client (uses default if not provided)
        """
        self.client = client or LLMClient()
        self._parse_errors: list[ValidationError] = []

    @abstractmethod
    def get_extraction_prompt(self) -> str:
        """Get the extraction prompt for this document type."""
        pass

    @abstractmethod
    def parse_response(self, response: dict) -> dict:
        """Parse LLM response into structured format."""
        pass

    def extract(self, image: Image.Image) -> dict:
        """
        Extract fields from document image.

        Args:
            image: PIL Image of the document

        Returns:
            Dict with extracted fields and confidence scores
        """
        self._parse_errors = []
        response = self.client.process_image(
            image=image,
            system_prompt=BASE_EXTRACTION_SYSTEM_PROMPT,
            user_prompt=self.get_extraction_prompt(),
            output_format="json",
        )
        if not isinstance(response, dict):
            raise TypeError("LLM extraction response must be a JSON object")
        return self.parse_response(response)

    def extract_multi_page(self, images: list[Image.Image]) -> dict:
        """
        Extract from multi-page document.

        Args:
            images: List of PIL Images (pages)

        Returns:
            Merged extraction result
        """
        if not images:
            raise ValueError("At least one page is required")

        self._parse_errors = []
        response = self.client.process_images(
            images=images,
            system_prompt=BASE_EXTRACTION_SYSTEM_PROMPT,
            user_prompt=self.get_extraction_prompt(),
            output_format="json",
        )
        if not isinstance(response, dict):
            raise TypeError("LLM extraction response must be a JSON object")
        return self.parse_response(response)

    def consume_validation_errors(self) -> list[ValidationError]:
        """Return parser errors and clear them for the next extraction."""
        errors = list(self._parse_errors)
        self._parse_errors = []
        return errors

    def get_confidence_field(
        self, response: dict[str, Any], field_name: str
    ) -> tuple[Any, float]:
        """Read a value/confidence pair defensively from an LLM response."""
        field_data = response.get(field_name)
        if not isinstance(field_data, dict):
            return None, 0.0

        value = field_data.get("value")
        try:
            confidence = float(field_data.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0

        confidence = min(1.0, max(0.0, confidence))
        if value is None:
            confidence = 0.0
        return value, confidence

    def parse_date(self, value: Any, field_name: str) -> date | None:
        """Parse a date and record malformed values as validation errors."""
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if not isinstance(value, str):
            self._add_parse_error(field_name, f"Invalid date value: {value!r}")
            return None

        formats = (
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%d-%m-%Y",
            "%m-%d-%Y",
        )
        for date_format in formats:
            try:
                return datetime.strptime(value.strip(), date_format).date()
            except ValueError:
                continue

        self._add_parse_error(field_name, f"Invalid date format: {value}")
        return None

    def parse_float(self, value: Any, field_name: str) -> float | None:
        """Parse a numeric value and record malformed input."""
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            self._add_parse_error(field_name, f"Invalid number: {value!r}")
            return None

    def parse_int(self, value: Any, field_name: str) -> int | None:
        """Parse an integer value and reject fractional quantities."""
        number = self.parse_float(value, field_name)
        if number is None:
            return None
        if not number.is_integer():
            self._add_parse_error(field_name, f"Expected an integer: {value!r}")
            return None
        return int(number)

    def _add_parse_error(self, field: str, message: str) -> None:
        self._parse_errors.append(
            ValidationError(field=field, message=message, severity="warning")
        )
