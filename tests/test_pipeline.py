"""End-to-end pipeline tests with a mocked OpenRouter client."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz

from src.models.base import ProcessingFailure
from src.pipeline.extractor import ExtractionPipeline


def field(value: object, confidence: float) -> dict[str, object]:
    return {"value": value, "confidence": confidence}


RECEIPT_RESPONSE = {
    "hospital_name": field("Bangkok Hospital", 0.98),
    "patient_name": field("Somchai Wong", 0.94),
    "date": field("2024-03-15", 0.97),
    "items": field(
        [
            {
                "description": "Consultation",
                "quantity": 1,
                "unit_price": 500.0,
                "total": 500.0,
            }
        ],
        0.91,
    ),
    "grand_total": field(500.0, 0.96),
    "payment_method": field("Credit Card", 0.88),
}


class FakeVisionClient:
    """Route mocked responses by classification/extraction system prompt."""

    def __init__(
        self,
        document_type: str = "receipt",
        extraction_response: dict[str, Any] | None = None,
    ) -> None:
        self.document_type = document_type
        self.extraction_response = extraction_response or RECEIPT_RESPONSE
        self.multi_page_counts: list[int] = []

    def _response(self, system_prompt: str) -> dict[str, Any]:
        if "classification expert" in system_prompt:
            return {
                "document_type": self.document_type,
                "confidence": 0.95,
                "reasoning": "Clear layout",
            }
        return self.extraction_response

    def process_image(self, **kwargs: Any) -> dict[str, Any]:
        return self._response(str(kwargs["system_prompt"]))

    def process_images(self, **kwargs: Any) -> dict[str, Any]:
        images = kwargs["images"]
        self.multi_page_counts.append(len(images))
        return self._response(str(kwargs["system_prompt"]))


def test_pipeline_extracts_and_validates_generated_pdf(
    sample_receipt_path: Path,
) -> None:
    pipeline = ExtractionPipeline(client=FakeVisionClient())
    result = pipeline.extract(sample_receipt_path)
    assert result.document_type == "receipt"
    assert result.fields["hospital_name"]["value"] == "Bangkok Hospital"
    assert result.fields["grand_total"]["value"] == 500.0
    assert result.validation_errors == []
    assert 0.8 < result.confidence <= 0.95


def test_pipeline_surfaces_amount_and_sum_errors(
    sample_receipt_path: Path,
) -> None:
    response = dict(RECEIPT_RESPONSE)
    response["grand_total"] = field(-10.0, 0.9)
    pipeline = ExtractionPipeline(
        client=FakeVisionClient(extraction_response=response)
    )
    result = pipeline.extract(sample_receipt_path)
    fields = {error.field for error in result.validation_errors}
    assert "grand_total" in fields
    assert result.confidence < 0.8


def test_pipeline_processes_all_pdf_pages(
    sample_receipt_path: Path, tmp_path: Path
) -> None:
    multi_page_path = tmp_path / "two_pages.pdf"
    with fitz.open(sample_receipt_path) as source:
        output = fitz.open()
        output.insert_pdf(source)
        output.insert_pdf(source)
        output.save(multi_page_path)
        output.close()

    client = FakeVisionClient()
    result = ExtractionPipeline(client=client).extract(multi_page_path)
    assert result.document_type == "receipt"
    assert client.multi_page_counts == [2, 2]


def test_batch_continues_after_document_failure(
    sample_receipt_path: Path, tmp_path: Path
) -> None:
    missing = tmp_path / "missing.pdf"
    results = ExtractionPipeline(client=FakeVisionClient()).extract_batch(
        [sample_receipt_path, missing]
    )
    assert results[0].document_type == "receipt"
    assert isinstance(results[1], ProcessingFailure)
    assert results[1].validation_errors[0].severity == "critical"
