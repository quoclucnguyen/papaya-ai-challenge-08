"""Amount validator."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from src.models.base import ExtractionResult, ValidationError
from src.validators.base import BaseValidator


class AmountValidator(BaseValidator):
    """Validate receipt amounts and quantities."""

    def validate(self, result: ExtractionResult) -> list[ValidationError]:
        errors: list[ValidationError] = []
        total_data = result.fields.get("grand_total", {})
        if isinstance(total_data, dict):
            total = total_data.get("value")
            if total is not None:
                error = self._validate_positive(total, "grand_total", "Grand total")
                if error:
                    errors.append(error)

        if result.document_type == "receipt":
            errors.extend(self._validate_receipt_items(result))
        return errors

    def _validate_positive(
        self, value: Any, field_name: str, display_name: str
    ) -> ValidationError | None:
        try:
            amount = float(value)
        except (TypeError, ValueError):
            return ValidationError(
                field=field_name,
                message=f"{display_name} is not a valid number",
                severity="error",
            )
        if amount <= 0:
            return ValidationError(
                field=field_name,
                message=f"{display_name} must be positive: {amount}",
                severity="error",
            )
        return None

    def _validate_receipt_items(
        self, result: ExtractionResult
    ) -> list[ValidationError]:
        errors: list[ValidationError] = []
        items_data = result.fields.get("items", {})
        if not isinstance(items_data, dict):
            return errors

        for index, item in enumerate(items_data.get("value") or []):
            for name, label in (
                ("quantity", "quantity"),
                ("unit_price", "unit price"),
                ("total", "total"),
            ):
                value = self._get_value(item, name)
                error = self._validate_positive(
                    value, f"items[{index}].{name}", f"Item {index + 1} {label}"
                )
                if error:
                    errors.append(error)
        return errors

    @staticmethod
    def _get_value(item: Any, name: str) -> Any:
        if isinstance(item, BaseModel):
            return getattr(item, name, None)
        if isinstance(item, dict):
            return item.get(name)
        return None
