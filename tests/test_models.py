"""Unit tests for Pydantic models."""

import pytest

from src.models.base import (
    ConfidenceField,
    DocumentType,
    ExtractionResult,
    ItemLine,
    LabTest,
    Medication,
)
from src.models.receipt import create_receipt_result


class TestConfidenceField:
    """Tests for ConfidenceField model."""

    def test_confidence_field_with_value(self):
        """Test confidence field with a value."""
        field = ConfidenceField[str](value="Test Hospital", confidence=0.95)
        assert field.value == "Test Hospital"
        assert field.confidence == 0.95

    def test_confidence_field_with_null(self):
        """Test confidence field with null value."""
        field = ConfidenceField[str](value=None, confidence=0.0)
        assert field.value is None
        assert field.confidence == 0.0

    def test_confidence_range_validation(self):
        """Test confidence is clamped to 0-1 range."""
        # Valid confidence
        field = ConfidenceField[str](value="test", confidence=0.5)
        assert field.confidence == 0.5

        # Invalid confidences should raise error
        with pytest.raises(Exception):
            ConfidenceField[str](value="test", confidence=1.5)

        with pytest.raises(Exception):
            ConfidenceField[str](value="test", confidence=-0.1)

    def test_is_confident(self):
        """Test is_confident method."""
        field_high = ConfidenceField[str](value="test", confidence=0.8)
        assert field_high.is_confident(threshold=0.7) is True
        assert field_high.is_confident(threshold=0.9) is False

        field_low = ConfidenceField[str](value="test", confidence=0.3)
        assert field_low.is_confident(threshold=0.5) is False


class TestExtractionResult:
    """Tests for ExtractionResult model."""

    def test_extraction_result_basic(self):
        """Test basic extraction result."""
        result = ExtractionResult(
            document_type=DocumentType.RECEIPT,
            confidence=0.9,
            fields={"test": "value"},
            validation_errors=[],
        )
        assert result.document_type == DocumentType.RECEIPT
        assert result.confidence == 0.9
        assert result.has_validation_errors() is False

    def test_invalid_document_type(self):
        """Test validation rejects invalid document type."""
        with pytest.raises(ValueError):
            ExtractionResult(
                document_type="invalid_type",
                confidence=0.9,
                fields={},
            )

    def test_add_validation_error(self):
        """Test adding validation errors."""
        result = ExtractionResult(
            document_type=DocumentType.RECEIPT,
            confidence=0.9,
            fields={},
        )
        result.add_error("grand_total", "Sum mismatch", "warning")

        assert len(result.validation_errors) == 1
        assert result.validation_errors[0].field == "grand_total"
        assert result.validation_errors[0].message == "Sum mismatch"
        assert result.has_validation_errors() is True


class TestItemLine:
    """Tests for ItemLine model."""

    def test_item_line_valid(self):
        """Test valid item line."""
        item = ItemLine(
            description="Test Service",
            quantity=2,
            unit_price=100.0,
            total=200.0,
        )
        assert item.description == "Test Service"
        assert item.quantity == 2
        assert item.unit_price == 100.0
        assert item.total == 200.0

    def test_item_line_preserves_invalid_value_for_business_validation(self):
        """Business validators, not parsing, report invalid extracted amounts."""
        item = ItemLine(
            description="Test",
            quantity=-1,
            unit_price=100.0,
            total=200.0,
        )
        assert item.quantity == -1


class TestLabTest:
    """Tests for LabTest model."""

    def test_lab_test_valid(self):
        """Test valid lab test."""
        test = LabTest(
            test_name="WBC",
            result="12.5",
            unit="x10^3/uL",
            reference_range="4.5-11.0",
            flag="high",
        )
        assert test.test_name == "WBC"
        assert test.flag == "high"

    def test_lab_test_flag_validation(self):
        """Test flag must be valid."""
        with pytest.raises(ValueError):
            LabTest(
                test_name="WBC",
                result="12.5",
                flag="invalid",
            )

    def test_lab_test_flag_normalization(self):
        """Test flag is normalized to lowercase."""
        test = LabTest(
            test_name="WBC",
            result="12.5",
            flag="HIGH",
        )
        assert test.flag == "high"


class TestMedication:
    """Tests for Medication model."""

    def test_medication_valid(self):
        """Test valid medication."""
        med = Medication(
            name="Amoxicillin",
            dosage="500mg",
            frequency="Every 8 hours",
            duration="7 days",
            quantity=21,
        )
        assert med.name == "Amoxicillin"
        assert med.dosage == "500mg"
        assert med.quantity == 21

    def test_medication_optional_fields(self):
        """Test medication with optional fields as None."""
        med = Medication(
            name="Aspirin",
        )
        assert med.name == "Aspirin"
        assert med.dosage is None
        assert med.frequency is None


class TestReceiptResult:
    """Tests for receipt result creation."""

    def test_create_receipt_result(self):
        """Test creating a receipt result."""
        result = create_receipt_result(
            hospital_name="Test Hospital",
            hospital_confidence=0.95,
            patient_name="John Doe",
            patient_confidence=0.9,
            grand_total=1000.0,
            total_confidence=0.98,
            confidence=0.92,
        )

        assert result.document_type == DocumentType.RECEIPT
        assert result.confidence == 0.92
        assert result.fields["hospital_name"]["value"] == "Test Hospital"
        assert result.fields["hospital_name"]["confidence"] == 0.95

    def test_create_receipt_result_with_items(self):
        """Test creating receipt with items."""
        items = [
            ItemLine(description="Service 1", quantity=1, unit_price=100.0, total=100.0),
            ItemLine(description="Service 2", quantity=2, unit_price=50.0, total=100.0),
        ]

        result = create_receipt_result(
            items=items,
            items_confidence=0.85,
            grand_total=200.0,
            total_confidence=0.95,
        )

        assert len(result.fields["items"]["value"]) == 2
        assert result.fields["items"]["value"][0]["description"] == "Service 1"
