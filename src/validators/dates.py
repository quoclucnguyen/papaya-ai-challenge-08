"""Date validator."""

from __future__ import annotations

from datetime import date
from typing import Any

from src.models.base import ExtractionResult, ValidationError
from src.validators.base import BaseValidator


class DateValidator(BaseValidator):
    """Validate date values and relationships."""

    MIN_YEAR = 1950
    MAX_YEAR = 2030

    def validate(self, result: ExtractionResult) -> list[ValidationError]:
        errors: list[ValidationError] = []
        date_fields = {
            "date": "Document date",
            "admission_date": "Admission date",
            "discharge_date": "Discharge date",
        }

        for field_name, display_name in date_fields.items():
            field_data = result.fields.get(field_name, {})
            if not isinstance(field_data, dict):
                continue
            date_value = field_data.get("value")
            if date_value is not None:
                error = self._validate_date(date_value, field_name, display_name)
                if error:
                    errors.append(error)

        errors.extend(self._validate_date_relationships(result))
        return errors

    def _validate_date(
        self, date_value: Any, field_name: str, display_name: str
    ) -> ValidationError | None:
        parsed_date: date
        if isinstance(date_value, date):
            parsed_date = date_value
        elif isinstance(date_value, str):
            try:
                parsed_date = date.fromisoformat(date_value)
            except ValueError:
                return ValidationError(
                    field=field_name,
                    message=f"{display_name} has invalid format",
                    severity="warning",
                )
        else:
            return ValidationError(
                field=field_name,
                message=f"{display_name} is not a valid date",
                severity="warning",
            )

        if not self.MIN_YEAR <= parsed_date.year <= self.MAX_YEAR:
            return ValidationError(
                field=field_name,
                message=(
                    f"{display_name} year {parsed_date.year} is outside "
                    "reasonable range"
                ),
                severity="warning",
            )

        if parsed_date > date.today():
            return ValidationError(
                field=field_name,
                message=f"{display_name} is in the future",
                severity="warning",
            )
        return None

    def _validate_date_relationships(
        self, result: ExtractionResult
    ) -> list[ValidationError]:
        if result.document_type != "discharge_summary":
            return []

        admission_data = result.fields.get("admission_date", {})
        discharge_data = result.fields.get("discharge_date", {})
        if not isinstance(admission_data, dict) or not isinstance(
            discharge_data, dict
        ):
            return []

        admission_date = admission_data.get("value")
        discharge_date = discharge_data.get("value")
        if (
            isinstance(admission_date, date)
            and isinstance(discharge_date, date)
            and admission_date > discharge_date
        ):
            return [
                ValidationError(
                    field="discharge_date",
                    message="Discharge date is before admission date",
                    severity="error",
                )
            ]
        return []
