"""Receipt extractor for hospital invoices."""

from __future__ import annotations

from typing import Any

from src.extractors.base import BaseExtractor
from src.models.base import ItemLine
from src.prompts.extraction import RECEIPT_EXTRACTION_PROMPT


class ReceiptExtractor(BaseExtractor):
    """Extracts data from hospital receipts/invoices."""

    def get_extraction_prompt(self) -> str:
        """Get receipt extraction prompt."""
        return RECEIPT_EXTRACTION_PROMPT

    def parse_response(self, response: dict[str, Any]) -> dict[str, Any]:
        """
        Parse LLM response into structured format.

        Args:
            response: Raw LLM response dict

        Returns:
            Structured extraction result
        """
        hospital_name, hospital_conf = self.get_confidence_field(
            response, "hospital_name"
        )
        patient_name, patient_conf = self.get_confidence_field(
            response, "patient_name"
        )

        date_value, date_conf = self.get_confidence_field(response, "date")
        parsed_date = self.parse_date(date_value, "date")
        if date_value is not None and parsed_date is None:
            date_conf = 0.0

        items_data, items_conf = self.get_confidence_field(response, "items")
        parsed_items: list[ItemLine] | None = None

        if items_data is not None:
            if not isinstance(items_data, list):
                self._add_parse_error("items", "Items must be a list")
                items_conf = 0.0
            else:
                parsed_items = []
                for index, item in enumerate(items_data):
                    if not isinstance(item, dict):
                        self._add_parse_error(
                            f"items[{index}]", "Item must be an object"
                        )
                        continue
                    quantity = self.parse_int(
                        item.get("quantity"), f"items[{index}].quantity"
                    )
                    unit_price = self.parse_float(
                        item.get("unit_price"), f"items[{index}].unit_price"
                    )
                    total = self.parse_float(
                        item.get("total"), f"items[{index}].total"
                    )
                    if quantity is None or unit_price is None or total is None:
                        continue
                    parsed_items.append(
                        ItemLine(
                            description=str(item.get("description", "")),
                            quantity=quantity,
                            unit_price=unit_price,
                            total=total,
                        )
                    )

        grand_total, total_conf = self.get_confidence_field(
            response, "grand_total"
        )
        parsed_total = self.parse_float(grand_total, "grand_total")
        if grand_total is not None and parsed_total is None:
            total_conf = 0.0
        payment_method, payment_conf = self.get_confidence_field(
            response, "payment_method"
        )

        return {
            "hospital_name": {"value": hospital_name, "confidence": hospital_conf},
            "patient_name": {"value": patient_name, "confidence": patient_conf},
            "date": {"value": parsed_date, "confidence": date_conf},
            "items": {"value": parsed_items, "confidence": items_conf},
            "grand_total": {"value": parsed_total, "confidence": total_conf},
            "payment_method": {
                "value": payment_method,
                "confidence": payment_conf,
            },
        }


def get_receipt_extractor(client: Any = None) -> ReceiptExtractor:
    """Get default receipt extractor."""
    return ReceiptExtractor(client)
