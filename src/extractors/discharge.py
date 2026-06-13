"""Discharge summary extractor."""

from __future__ import annotations

from typing import Any

from src.extractors.base import BaseExtractor
from src.models.base import Diagnosis, Procedure
from src.prompts.extraction import DISCHARGE_EXTRACTION_PROMPT


class DischargeExtractor(BaseExtractor):
    """Extracts data from discharge summaries."""

    def get_extraction_prompt(self) -> str:
        """Get discharge summary extraction prompt."""
        return DISCHARGE_EXTRACTION_PROMPT

    def parse_response(self, response: dict[str, Any]) -> dict[str, Any]:
        """Parse LLM response into structured format."""
        hospital_name, hospital_conf = self.get_confidence_field(
            response, "hospital_name"
        )
        patient_name, patient_conf = self.get_confidence_field(
            response, "patient_name"
        )

        admission_value, admission_conf = self.get_confidence_field(
            response, "admission_date"
        )
        admission_date = self.parse_date(admission_value, "admission_date")
        if admission_value is not None and admission_date is None:
            admission_conf = 0.0

        discharge_value, discharge_conf = self.get_confidence_field(
            response, "discharge_date"
        )
        discharge_date = self.parse_date(discharge_value, "discharge_date")
        if discharge_value is not None and discharge_date is None:
            discharge_conf = 0.0

        diagnosis_data, diagnosis_conf = self.get_confidence_field(
            response, "diagnosis"
        )
        parsed_diagnosis: Diagnosis | None = None
        if diagnosis_data is not None:
            if isinstance(diagnosis_data, dict):
                secondary = diagnosis_data.get("secondary") or []
                parsed_diagnosis = Diagnosis(
                    primary=diagnosis_data.get("primary"),
                    secondary=[str(value) for value in secondary],
                )
            else:
                self._add_parse_error("diagnosis", "Diagnosis must be an object")
                diagnosis_conf = 0.0

        procedures_data, procedures_conf = self.get_confidence_field(
            response, "procedures_performed"
        )
        parsed_procedures: list[Procedure] | None = None
        if procedures_data is not None:
            if not isinstance(procedures_data, list):
                self._add_parse_error(
                    "procedures_performed", "Procedures must be a list"
                )
                procedures_conf = 0.0
            else:
                parsed_procedures = []
                for index, procedure in enumerate(procedures_data):
                    if not isinstance(procedure, dict):
                        self._add_parse_error(
                            f"procedures_performed[{index}]",
                            "Procedure must be an object",
                        )
                        continue
                    procedure_date = self.parse_date(
                        procedure.get("date"),
                        f"procedures_performed[{index}].date",
                    )
                    parsed_procedures.append(
                        Procedure(
                            code=procedure.get("code"),
                            name=str(procedure.get("name", "")),
                            date=procedure_date,
                        )
                    )

        physician, physician_conf = self.get_confidence_field(
            response, "attending_physician"
        )
        instructions, instructions_conf = self.get_confidence_field(
            response, "discharge_instructions"
        )

        return {
            "hospital_name": {"value": hospital_name, "confidence": hospital_conf},
            "patient_name": {"value": patient_name, "confidence": patient_conf},
            "admission_date": {"value": admission_date, "confidence": admission_conf},
            "discharge_date": {"value": discharge_date, "confidence": discharge_conf},
            "diagnosis": {"value": parsed_diagnosis, "confidence": diagnosis_conf},
            "procedures_performed": {"value": parsed_procedures, "confidence": procedures_conf},
            "attending_physician": {"value": physician, "confidence": physician_conf},
            "discharge_instructions": {"value": instructions, "confidence": instructions_conf},
        }

def get_discharge_extractor(client: Any = None) -> DischargeExtractor:
    """Get default discharge extractor."""
    return DischargeExtractor(client)
