"""Unit tests for validators."""

from datetime import date, timedelta

from src.models.base import ExtractionResult, ItemLine
from src.validators.amounts import AmountValidator
from src.validators.dates import DateValidator
from src.validators.sums import SumValidator


class TestDateValidator:
    """Tests for DateValidator."""

    def test_valid_date(self):
        """Test valid date passes validation."""
        result = ExtractionResult(
            document_type="receipt",
            confidence=0.9,
            fields={
                "date": {"value": date(2024, 3, 15), "confidence": 0.95},
            },
        )
        validator = DateValidator()
        errors = validator.validate(result)
        assert len(errors) == 0

    def test_invalid_date_format(self):
        """Test invalid date format is flagged."""
        result = ExtractionResult(
            document_type="receipt",
            confidence=0.9,
            fields={
                "date": {"value": "invalid-date", "confidence": 0.5},
            },
        )
        validator = DateValidator()
        errors = validator.validate(result)
        assert len(errors) > 0
        assert any("invalid format" in e.message for e in errors)

    def test_future_date_warning(self):
        """Test future dates are flagged."""
        future_date = date.today() + timedelta(days=30)
        result = ExtractionResult(
            document_type="receipt",
            confidence=0.9,
            fields={
                "date": {"value": future_date, "confidence": 0.95},
            },
        )
        validator = DateValidator()
        errors = validator.validate(result)
        assert len(errors) > 0
        assert any("future" in e.message for e in errors)

    def test_discharge_date_relationship(self):
        """Test discharge before admission is flagged."""
        result = ExtractionResult(
            document_type="discharge_summary",
            confidence=0.9,
            fields={
                "admission_date": {"value": date(2024, 6, 5), "confidence": 0.95},
                "discharge_date": {"value": date(2024, 6, 1), "confidence": 0.95},
            },
        )
        validator = DateValidator()
        errors = validator.validate(result)
        assert len(errors) > 0
        assert any("before admission" in e.message for e in errors)


class TestAmountValidator:
    """Tests for AmountValidator."""

    def test_valid_amount(self):
        """Test valid amount passes."""
        result = ExtractionResult(
            document_type="receipt",
            confidence=0.9,
            fields={
                "grand_total": {"value": 1000.0, "confidence": 0.95},
            },
        )
        validator = AmountValidator()
        errors = validator.validate(result)
        assert len(errors) == 0

    def test_negative_amount_error(self):
        """Test negative amount is flagged."""
        result = ExtractionResult(
            document_type="receipt",
            confidence=0.9,
            fields={
                "grand_total": {"value": -100.0, "confidence": 0.5},
            },
        )
        validator = AmountValidator()
        errors = validator.validate(result)
        assert len(errors) > 0
        assert any("positive" in e.message for e in errors)

    def test_item_negative_quantity(self):
        """Test negative item quantity is flagged."""
        result = ExtractionResult(
            document_type="receipt",
            confidence=0.9,
            fields={
                "items": {
                    "value": [ItemLine(description="Test", quantity=-1, unit_price=100.0, total=100.0)],
                    "confidence": 0.9,
                },
            },
        )
        validator = AmountValidator()
        errors = validator.validate(result)
        assert len(errors) > 0
        assert any("quantity" in e.field for e in errors)


class TestSumValidator:
    """Tests for SumValidator."""

    def test_matching_sums(self):
        """Test matching sums pass validation."""
        items = [
            ItemLine(description="Item 1", quantity=1, unit_price=100.0, total=100.0),
            ItemLine(description="Item 2", quantity=1, unit_price=200.0, total=200.0),
        ]
        result = ExtractionResult(
            document_type="receipt",
            confidence=0.9,
            fields={
                "items": {"value": items, "confidence": 0.9},
                "grand_total": {"value": 300.0, "confidence": 0.95},
            },
        )
        validator = SumValidator()
        errors = validator.validate(result)
        assert len(errors) == 0

    def test_sum_mismatch_warning(self):
        """Test sum mismatch outside tolerance is flagged."""
        items = [
            ItemLine(description="Item 1", quantity=1, unit_price=100.0, total=100.0),
        ]
        result = ExtractionResult(
            document_type="receipt",
            confidence=0.9,
            fields={
                "items": {"value": items, "confidence": 0.9},
                "grand_total": {"value": 150.0, "confidence": 0.95},  # 50% mismatch
            },
        )
        validator = SumValidator()
        errors = validator.validate(result)
        assert len(errors) > 0
        assert any("grand_total" in e.field for e in errors)

    def test_item_calculation_mismatch(self):
        """Test item calculation mismatch is flagged."""
        items = [
            ItemLine(description="Item 1", quantity=2, unit_price=100.0, total=250.0),  # Should be 200
        ]
        result = ExtractionResult(
            document_type="receipt",
            confidence=0.9,
            fields={
                "items": {"value": items, "confidence": 0.9},
                "grand_total": {"value": 250.0, "confidence": 0.95},
            },
        )
        validator = SumValidator()
        errors = validator.validate(result)
        # Should have info-level warning for calculation mismatch
        assert any(e.severity == "info" for e in errors)

    def test_non_receipt_document(self):
        """Test validator only applies to receipts."""
        result = ExtractionResult(
            document_type="lab_report",
            confidence=0.9,
            fields={},
        )
        validator = SumValidator()
        errors = validator.validate(result)
        assert len(errors) == 0
