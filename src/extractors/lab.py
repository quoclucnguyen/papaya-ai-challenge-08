"""Lab report extractor."""

from __future__ import annotations

from typing import Any

from src.extractors.base import BaseExtractor
from src.models.base import LabTest
from src.prompts.extraction import LAB_EXTRACTION_PROMPT


class LabExtractor(BaseExtractor):
    """Extracts data from lab reports."""

    def get_extraction_prompt(self) -> str:
        """Get lab report extraction prompt."""
        return LAB_EXTRACTION_PROMPT

    def parse_response(self, response: dict[str, Any]) -> dict[str, Any]:
        """Parse LLM response into structured format."""
        lab_name, lab_conf = self.get_confidence_field(response, "lab_name")
        patient_name, patient_conf = self.get_confidence_field(
            response, "patient_name"
        )

        date_value, date_conf = self.get_confidence_field(response, "date")
        parsed_date = self.parse_date(date_value, "date")
        if date_value is not None and parsed_date is None:
            date_conf = 0.0

        tests_data, tests_conf = self.get_confidence_field(response, "tests")
        parsed_tests: list[LabTest] | None = None
        if tests_data is not None:
            if not isinstance(tests_data, list):
                self._add_parse_error("tests", "Tests must be a list")
                tests_conf = 0.0
            else:
                parsed_tests = []
                for index, test in enumerate(tests_data):
                    if not isinstance(test, dict):
                        self._add_parse_error(
                            f"tests[{index}]", "Lab test must be an object"
                        )
                        continue
                    flag = str(test.get("flag", "normal")).lower()
                    if flag not in {"normal", "high", "low"}:
                        self._add_parse_error(
                            f"tests[{index}].flag",
                            f"Invalid lab flag: {flag}",
                        )
                        flag = "normal"
                    parsed_tests.append(
                        LabTest(
                            test_name=str(test.get("test_name", "")),
                            result=str(test.get("result", "")),
                            unit=test.get("unit"),
                            reference_range=test.get("reference_range"),
                            flag=flag,
                        )
                    )

        return {
            "lab_name": {"value": lab_name, "confidence": lab_conf},
            "patient_name": {"value": patient_name, "confidence": patient_conf},
            "date": {"value": parsed_date, "confidence": date_conf},
            "tests": {"value": parsed_tests, "confidence": tests_conf},
        }

def get_lab_extractor(client: Any = None) -> LabExtractor:
    """Get default lab extractor."""
    return LabExtractor(client)
