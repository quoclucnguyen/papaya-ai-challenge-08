"""Base Pydantic models for medical document extraction."""

from __future__ import annotations

import datetime as dt
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, Field, field_validator, model_validator

T = TypeVar("T")


class ConfidenceField(BaseModel, Generic[T]):
    """A field with a value and confidence score."""

    value: T | None = Field(default=None, description="Extracted value, null if not found")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence score 0.0-1.0"
    )

    @model_validator(mode="after")
    def normalize_missing_value(self) -> ConfidenceField[T]:
        """A missing value must never retain a positive confidence score."""
        if self.value is None:
            self.confidence = 0.0
        return self

    def is_confident(self, threshold: float = 0.5) -> bool:
        """Check if confidence is above threshold."""
        return self.confidence >= threshold


class DocumentType(str):
    """Document type enumeration."""

    RECEIPT = "receipt"
    DISCHARGE_SUMMARY = "discharge_summary"
    LAB_REPORT = "lab_report"
    PRESCRIPTION = "prescription"

    @classmethod
    def all_values(cls) -> list[str]:
        """Get all document type values."""
        return [
            cls.RECEIPT,
            cls.DISCHARGE_SUMMARY,
            cls.LAB_REPORT,
            cls.PRESCRIPTION,
        ]


class ValidationError(BaseModel):
    """A validation error with severity and message."""

    field: str = Field(description="Field name that has the error")
    message: str = Field(description="Error message")
    severity: Literal["info", "warning", "error", "critical"] = Field(
        default="warning", description="Severity: warning, error, critical"
    )

    def __str__(self) -> str:
        return f"{self.severity.upper()}: {self.field} - {self.message}"


class ExtractionResult(BaseModel):
    """Result of document extraction."""

    document_type: str = Field(description="Detected document type")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Document classification confidence"
    )
    fields: dict[str, Any] = Field(
        default_factory=dict, description="Extracted fields with confidence"
    )
    validation_errors: list[ValidationError] = Field(
        default_factory=list, description="Validation errors found"
    )

    @field_validator("document_type")
    @classmethod
    def validate_document_type(cls, v: str) -> str:
        """Validate document type is one of the allowed values."""
        allowed = DocumentType.all_values()
        if v not in allowed:
            raise ValueError(f"document_type must be one of {allowed}")
        return v

    def has_validation_errors(self) -> bool:
        """Check if there are any validation errors."""
        return len(self.validation_errors) > 0

    def add_error(
        self,
        field: str,
        message: str,
        severity: Literal["info", "warning", "error", "critical"] = "warning",
    ) -> None:
        """Add a validation error."""
        self.validation_errors.append(
            ValidationError(field=field, message=message, severity=severity)
        )


class ProcessingFailure(BaseModel):
    """Failure returned by batch processing without breaking the remaining batch."""

    document_type: Literal["unknown"] = "unknown"
    confidence: float = 0.0
    fields: dict[str, Any] = Field(default_factory=dict)
    validation_errors: list[ValidationError]


class ItemLine(BaseModel):
    """An item line in a receipt."""

    description: str
    quantity: int
    unit_price: float
    total: float


class Diagnosis(BaseModel):
    """A diagnosis entry."""

    primary: str | None = None
    secondary: list[str] = Field(default_factory=list)


class Procedure(BaseModel):
    """A medical procedure."""

    code: str | None = None
    name: str
    date: dt.date | None = None


class LabTest(BaseModel):
    """A lab test result."""

    test_name: str
    result: str
    unit: str | None = None
    reference_range: str | None = None
    flag: str = Field(default="normal")  # normal, high, low

    @field_validator("flag")
    @classmethod
    def validate_flag(cls, v: str) -> str:
        """Validate flag value."""
        v_lower = v.lower()
        if v_lower not in {"normal", "high", "low"}:
            raise ValueError("flag must be normal, high, or low")
        return v_lower


class Medication(BaseModel):
    """A medication in a prescription."""

    name: str
    dosage: str | None = None
    frequency: str | None = None
    duration: str | None = None
    quantity: int | None = None


# Type aliases for use in other models
ConfidenceStr = ConfidenceField[str]
ConfidenceFloat = ConfidenceField[float]
ConfidenceDate = ConfidenceField[dt.date]
ConfidenceItemList = ConfidenceField[list[ItemLine]]
ConfidenceDiagnosis = ConfidenceField[Diagnosis]
ConfidenceProcedures = ConfidenceField[list[Procedure]]
ConfidenceTests = ConfidenceField[list[LabTest]]
ConfidenceMedications = ConfidenceField[list[Medication]]
