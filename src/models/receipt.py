"""Receipt model for medical invoices/receipts."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field

from src.models.base import (
    ConfidenceField,
    ConfidenceFloat,
    ConfidenceStr,
    DocumentType,
    ExtractionResult,
    ItemLine,
)


class ReceiptFields(BaseModel):
    """Fields extracted from a receipt document."""

    hospital_name: ConfidenceStr = Field(
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
    items: ConfidenceField[list[ItemLine]] = Field(
        default_factory=lambda: ConfidenceField[list[ItemLine]](
            value=None, confidence=0.0
        )
    )
    grand_total: ConfidenceFloat = Field(
        default_factory=lambda: ConfidenceField[float](value=None, confidence=0.0)
    )
    payment_method: ConfidenceStr = Field(
        default_factory=lambda: ConfidenceField[str](value=None, confidence=0.0)
    )


def create_receipt_result(
    hospital_name: str | None = None,
    hospital_confidence: float = 0.0,
    patient_name: str | None = None,
    patient_confidence: float = 0.0,
    date: dt.date | None = None,
    date_confidence: float = 0.0,
    items: list[ItemLine] | None = None,
    items_confidence: float = 0.0,
    grand_total: float | None = None,
    total_confidence: float = 0.0,
    payment_method: str | None = None,
    payment_confidence: float = 0.0,
    confidence: float = 0.0,
    validation_errors: list | None = None,
) -> ExtractionResult:
    """Create a receipt extraction result.

    Args:
        Various field values and their confidence scores.

    Returns:
        ExtractionResult with receipt document type.
    """
    fields = ReceiptFields(
        hospital_name=ConfidenceField(value=hospital_name, confidence=hospital_confidence),
        patient_name=ConfidenceField(value=patient_name, confidence=patient_confidence),
        date=ConfidenceField(value=date, confidence=date_confidence),
        items=ConfidenceField(value=items, confidence=items_confidence),
        grand_total=ConfidenceField(value=grand_total, confidence=total_confidence),
        payment_method=ConfidenceField(value=payment_method, confidence=payment_confidence),
    )

    return ExtractionResult(
        document_type=DocumentType.RECEIPT,
        confidence=confidence,
        fields=fields.model_dump(),
        validation_errors=validation_errors or [],
    )
