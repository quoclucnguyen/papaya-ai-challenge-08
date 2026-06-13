"""Confidence and missing-value validation."""

from __future__ import annotations

from typing import Any

from src.models.base import ExtractionResult, ValidationError
from src.validators.base import BaseValidator


class ConfidenceValidator(BaseValidator):
    """Validate confidence structure and flag uncertain fields."""

    FIELD_THRESHOLD = 0.5
    CLASSIFICATION_THRESHOLD = 0.7

    def validate(self, result: ExtractionResult) -> list[ValidationError]:
        errors: list[ValidationError] = []
        if result.confidence < self.CLASSIFICATION_THRESHOLD:
            errors.append(
                ValidationError(
                    field="document_type",
                    message=(
                        "Document classification confidence is below "
                        f"{self.CLASSIFICATION_THRESHOLD:.1f}"
                    ),
                    severity="warning",
                )
            )

        for field_name, field_data in result.fields.items():
            if not isinstance(field_data, dict):
                errors.append(
                    ValidationError(
                        field=field_name,
                        message="Field must contain value and confidence",
                        severity="error",
                    )
                )
                continue

            value = field_data.get("value")
            confidence = self._parse_confidence(field_data.get("confidence"))
            if confidence is None:
                errors.append(
                    ValidationError(
                        field=field_name,
                        message="Confidence must be between 0.0 and 1.0",
                        severity="error",
                    )
                )
            elif value is None and confidence != 0.0:
                errors.append(
                    ValidationError(
                        field=field_name,
                        message="Missing value must have confidence 0.0",
                        severity="error",
                    )
                )
            elif value is not None and confidence < self.FIELD_THRESHOLD:
                errors.append(
                    ValidationError(
                        field=field_name,
                        message=(
                            f"Field confidence {confidence:.2f} is below "
                            f"{self.FIELD_THRESHOLD:.1f}"
                        ),
                        severity="warning",
                    )
                )
        return errors

    @staticmethod
    def _parse_confidence(value: Any) -> float | None:
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            return None
        if not 0.0 <= confidence <= 1.0:
            return None
        return confidence
