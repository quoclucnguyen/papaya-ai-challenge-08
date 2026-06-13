"""Prescription extractor."""

from __future__ import annotations

from typing import Any

from src.extractors.base import BaseExtractor
from src.models.base import Medication
from src.prompts.extraction import PRESCRIPTION_EXTRACTION_PROMPT


class PrescriptionExtractor(BaseExtractor):
    """Extracts data from medical prescriptions."""

    def get_extraction_prompt(self) -> str:
        """Get prescription extraction prompt."""
        return PRESCRIPTION_EXTRACTION_PROMPT

    def parse_response(self, response: dict[str, Any]) -> dict[str, Any]:
        """Parse LLM response into structured format."""
        doctor_name, doctor_conf = self.get_confidence_field(
            response, "doctor_name"
        )
        patient_name, patient_conf = self.get_confidence_field(
            response, "patient_name"
        )

        date_value, date_conf = self.get_confidence_field(response, "date")
        parsed_date = self.parse_date(date_value, "date")
        if date_value is not None and parsed_date is None:
            date_conf = 0.0

        medications_data, medications_conf = self.get_confidence_field(
            response, "medications"
        )
        parsed_medications: list[Medication] | None = None
        if medications_data is not None:
            if not isinstance(medications_data, list):
                self._add_parse_error("medications", "Medications must be a list")
                medications_conf = 0.0
            else:
                parsed_medications = []
                for index, medication in enumerate(medications_data):
                    if not isinstance(medication, dict):
                        self._add_parse_error(
                            f"medications[{index}]",
                            "Medication must be an object",
                        )
                        continue
                    quantity = self.parse_int(
                        medication.get("quantity"),
                        f"medications[{index}].quantity",
                    )
                    parsed_medications.append(
                        Medication(
                            name=str(medication.get("name", "")),
                            dosage=medication.get("dosage"),
                            frequency=medication.get("frequency"),
                            duration=medication.get("duration"),
                            quantity=quantity,
                        )
                    )

        return {
            "doctor_name": {"value": doctor_name, "confidence": doctor_conf},
            "patient_name": {"value": patient_name, "confidence": patient_conf},
            "date": {"value": parsed_date, "confidence": date_conf},
            "medications": {"value": parsed_medications, "confidence": medications_conf},
        }

def get_prescription_extractor(client: Any = None) -> PrescriptionExtractor:
    """Get default prescription extractor."""
    return PrescriptionExtractor(client)
