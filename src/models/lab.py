"""Lab Report model."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field

from src.models.base import (
    ConfidenceField,
    ConfidenceStr,
    ConfidenceTests,
    DocumentType,
    ExtractionResult,
    LabTest,
)


class LabFields(BaseModel):
    """Fields extracted from a lab report."""

    lab_name: ConfidenceStr = Field(
        default_factory=lambda: ConfidenceField[str](value=None, confidence=0.0)
    )
    patient_name: ConfidenceStr = Field(
        default_factory=lambda: ConfidenceField[str](value=None, confidence=0.0)
    )
    date: ConfidenceField[dt.date] = Field(
        default_factory=lambda: ConfidenceField[dt.date](
            value=None, confidence=0.0
        )
    )
    tests: ConfidenceTests = Field(
        default_factory=lambda: ConfidenceField[list[LabTest]](
            value=None, confidence=0.0
        )
    )


def create_lab_result(
    lab_name: str | None = None,
    lab_confidence: float = 0.0,
    patient_name: str | None = None,
    patient_confidence: float = 0.0,
    date: dt.date | None = None,
    date_confidence: float = 0.0,
    tests: list[LabTest] | None = None,
    tests_confidence: float = 0.0,
    confidence: float = 0.0,
    validation_errors: list | None = None,
) -> ExtractionResult:
    """Create a lab report extraction result."""
    fields = LabFields(
        lab_name=ConfidenceField(value=lab_name, confidence=lab_confidence),
        patient_name=ConfidenceField(value=patient_name, confidence=patient_confidence),
        date=ConfidenceField(value=date, confidence=date_confidence),
        tests=ConfidenceField(value=tests, confidence=tests_confidence),
    )

    return ExtractionResult(
        document_type=DocumentType.LAB_REPORT,
        confidence=confidence,
        fields=fields.model_dump(),
        validation_errors=validation_errors or [],
    )
