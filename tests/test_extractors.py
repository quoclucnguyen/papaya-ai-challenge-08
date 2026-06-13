"""Tests for type-specific response parsing."""

from __future__ import annotations

from src.extractors.discharge import DischargeExtractor
from src.extractors.lab import LabExtractor
from src.extractors.prescription import PrescriptionExtractor
from src.extractors.receipt import ReceiptExtractor


def field(value: object, confidence: float = 0.9) -> dict:
    return {"value": value, "confidence": confidence}


def test_receipt_parser_handles_numbers_and_items() -> None:
    extractor = ReceiptExtractor(client=object())
    result = extractor.parse_response(
        {
            "hospital_name": field("Bangkok Hospital"),
            "patient_name": field("Somchai Wong"),
            "date": field("2024-03-15"),
            "items": field(
                [
                    {
                        "description": "Consultation",
                        "quantity": "2",
                        "unit_price": "500.00",
                        "total": "1000.00",
                    }
                ]
            ),
            "grand_total": field("1000.00"),
            "payment_method": field("Card"),
        }
    )
    assert result["grand_total"]["value"] == 1000.0
    assert result["items"]["value"][0].quantity == 2


def test_receipt_parser_accepts_null_items() -> None:
    extractor = ReceiptExtractor(client=object())
    result = extractor.parse_response({"items": field(None, 0.8)})
    assert result["items"] == {"value": None, "confidence": 0.0}


def test_invalid_date_becomes_parse_error() -> None:
    extractor = ReceiptExtractor(client=object())
    result = extractor.parse_response({"date": field("31-31-2024")})
    errors = extractor.consume_validation_errors()
    assert result["date"] == {"value": None, "confidence": 0.0}
    assert errors[0].field == "date"


def test_discharge_parser_handles_null_diagnosis_and_procedures() -> None:
    extractor = DischargeExtractor(client=object())
    result = extractor.parse_response(
        {
            "diagnosis": field(None),
            "procedures_performed": field(None),
        }
    )
    assert result["diagnosis"]["value"] is None
    assert result["procedures_performed"]["value"] is None


def test_lab_parser_normalizes_and_flags_invalid_flag() -> None:
    extractor = LabExtractor(client=object())
    result = extractor.parse_response(
        {
            "tests": field(
                [
                    {
                        "test_name": "WBC",
                        "result": "12.5",
                        "unit": "x10^3/uL",
                        "reference_range": "4.5-11.0",
                        "flag": "unexpected",
                    }
                ]
            )
        }
    )
    assert result["tests"]["value"][0].flag == "normal"
    assert extractor.consume_validation_errors()[0].field == "tests[0].flag"


def test_prescription_parser_preserves_missing_quantity() -> None:
    extractor = PrescriptionExtractor(client=object())
    result = extractor.parse_response(
        {
            "medications": field(
                [
                    {
                        "name": "Amoxicillin",
                        "dosage": "500mg",
                        "frequency": "Every 8 hours",
                        "duration": "7 days",
                        "quantity": None,
                    }
                ]
            )
        }
    )
    assert result["medications"]["value"][0].quantity is None
