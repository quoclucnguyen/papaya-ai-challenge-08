"""Arithmetic consistency validation for receipts."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from src.models.base import ExtractionResult, ValidationError
from src.validators.base import BaseValidator

SUM_TOLERANCE = 0.05
ITEM_TOLERANCE = 0.01


class SumValidator(BaseValidator):
    """Validate receipt line totals and the grand total."""

    def validate(self, result: ExtractionResult) -> list[ValidationError]:
        if result.document_type != "receipt":
            return []
        return self._validate_receipt_sums(result)

    def _validate_receipt_sums(
        self, result: ExtractionResult
    ) -> list[ValidationError]:
        errors: list[ValidationError] = []
        items_data = result.fields.get("items", {})
        total_data = result.fields.get("grand_total", {})
        if not isinstance(items_data, dict) or not isinstance(total_data, dict):
            return errors

        items = items_data.get("value") or []
        grand_total = total_data.get("value")
        if grand_total is None or not items:
            return errors

        numeric_total = float(grand_total)
        calculated_total = sum(
            float(self._get_value(item, "total") or 0.0) for item in items
        )
        difference = abs(numeric_total - calculated_total)
        denominator = max(abs(numeric_total), abs(calculated_total), 0.01)
        relative_diff = difference / denominator

        if relative_diff > SUM_TOLERANCE:
            errors.append(
                ValidationError(
                    field="grand_total",
                    message=(
                        f"Item totals sum to {calculated_total:.2f} but "
                        f"grand_total is {numeric_total:.2f} "
                        f"(diff: {relative_diff * 100:.1f}%)"
                    ),
                    severity="warning",
                )
            )

        for index, item in enumerate(items):
            quantity = float(self._get_value(item, "quantity") or 0.0)
            unit_price = float(self._get_value(item, "unit_price") or 0.0)
            total = float(self._get_value(item, "total") or 0.0)
            if quantity <= 0 or unit_price <= 0:
                continue

            calculated = quantity * unit_price
            item_denominator = max(abs(total), abs(calculated), 0.01)
            diff_ratio = abs(total - calculated) / item_denominator
            if diff_ratio > ITEM_TOLERANCE:
                errors.append(
                    ValidationError(
                        field=f"items[{index}]",
                        message=(
                            f"Item {index + 1}: {quantity:g} x "
                            f"{unit_price:.2f} = {calculated:.2f} "
                            f"but total is {total:.2f}"
                        ),
                        severity="info",
                    )
                )
        return errors

    @staticmethod
    def _get_value(item: Any, name: str) -> Any:
        if isinstance(item, BaseModel):
            return getattr(item, name, None)
        if isinstance(item, dict):
            return item.get(name)
        return None
