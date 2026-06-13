"""Prescription model."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field

from src.models.base import (
    ConfidenceField,
    ConfidenceStr,
    DocumentType,
    ExtractionResult,
    Medication,
)


class PrescriptionFields(BaseModel):
    """Fields extracted from a prescription."""

    doctor_name: ConfidenceStr = Field(
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
    medications: ConfidenceField[list[Medication]] = Field(
        default_factory=lambda: ConfidenceField[list[Medication]](
            value=None, confidence=0.0
        )
    )


def create_prescription_result(
    doctor_name: str | None = None,
    doctor_confidence: float = 0.0,
    patient_name: str | None = None,
    patient_confidence: float = 0.0,
    date: dt.date | None = None,
    date_confidence: float = 0.0,
    medications: list[Medication] | None = None,
    medications_confidence: float = 0.0,
    confidence: float = 0.0,
    validation_errors: list | None = None,
) -> ExtractionResult:
    """Create a prescription extraction result."""
    fields = PrescriptionFields(
        doctor_name=ConfidenceField(value=doctor_name, confidence=doctor_confidence),
        patient_name=ConfidenceField(value=patient_name, confidence=patient_confidence),
        date=ConfidenceField(value=date, confidence=date_confidence),
        medications=ConfidenceField(value=medications, confidence=medications_confidence),
    )

    return ExtractionResult(
        document_type=DocumentType.PRESCRIPTION,
        confidence=confidence,
        fields=fields.model_dump(),
        validation_errors=validation_errors or [],
    )
