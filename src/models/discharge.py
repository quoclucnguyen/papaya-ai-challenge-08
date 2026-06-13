"""Discharge Summary model."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field

from src.models.base import (
    ConfidenceField,
    ConfidenceProcedures,
    ConfidenceStr,
    Diagnosis,
    DocumentType,
    ExtractionResult,
    Procedure,
)


class DischargeFields(BaseModel):
    """Fields extracted from a discharge summary."""

    hospital_name: ConfidenceStr = Field(
        default_factory=lambda: ConfidenceField[str](value=None, confidence=0.0)
    )
    patient_name: ConfidenceStr = Field(
        default_factory=lambda: ConfidenceField[str](value=None, confidence=0.0)
    )
    admission_date: ConfidenceField[dt.date] = Field(
        default_factory=lambda: ConfidenceField[dt.date](
            value=None, confidence=0.0
        )
    )
    discharge_date: ConfidenceField[dt.date] = Field(
        default_factory=lambda: ConfidenceField[dt.date](
            value=None, confidence=0.0
        )
    )
    diagnosis: ConfidenceField[Diagnosis] = Field(
        default_factory=lambda: ConfidenceField[Diagnosis](value=None, confidence=0.0)
    )
    procedures_performed: ConfidenceProcedures = Field(
        default_factory=lambda: ConfidenceField[list[Procedure]](
            value=None, confidence=0.0
        )
    )
    attending_physician: ConfidenceStr = Field(
        default_factory=lambda: ConfidenceField[str](value=None, confidence=0.0)
    )
    discharge_instructions: ConfidenceStr = Field(
        default_factory=lambda: ConfidenceField[str](value=None, confidence=0.0)
    )


def create_discharge_result(
    hospital_name: str | None = None,
    hospital_confidence: float = 0.0,
    patient_name: str | None = None,
    patient_confidence: float = 0.0,
    admission_date: dt.date | None = None,
    admission_confidence: float = 0.0,
    discharge_date: dt.date | None = None,
    discharge_confidence: float = 0.0,
    diagnosis: Diagnosis | None = None,
    diagnosis_confidence: float = 0.0,
    procedures: list[Procedure] | None = None,
    procedures_confidence: float = 0.0,
    attending_physician: str | None = None,
    physician_confidence: float = 0.0,
    discharge_instructions: str | None = None,
    instructions_confidence: float = 0.0,
    confidence: float = 0.0,
    validation_errors: list | None = None,
) -> ExtractionResult:
    """Create a discharge summary extraction result."""
    fields = DischargeFields(
        hospital_name=ConfidenceField(value=hospital_name, confidence=hospital_confidence),
        patient_name=ConfidenceField(value=patient_name, confidence=patient_confidence),
        admission_date=ConfidenceField(value=admission_date, confidence=admission_confidence),
        discharge_date=ConfidenceField(value=discharge_date, confidence=discharge_confidence),
        diagnosis=ConfidenceField(value=diagnosis, confidence=diagnosis_confidence),
        procedures_performed=ConfidenceField(value=procedures, confidence=procedures_confidence),
        attending_physician=ConfidenceField(value=attending_physician, confidence=physician_confidence),
        discharge_instructions=ConfidenceField(value=discharge_instructions, confidence=instructions_confidence),
    )

    return ExtractionResult(
        document_type=DocumentType.DISCHARGE_SUMMARY,
        confidence=confidence,
        fields=fields.model_dump(),
        validation_errors=validation_errors or [],
    )
