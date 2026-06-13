"""Tests for document classification."""

from __future__ import annotations

import pytest
from PIL import Image

from src.extractors.classifier import DocumentClassifier


class FakeClient:
    """Return configured OpenRouter-style JSON responses."""

    def __init__(self, response: dict) -> None:
        self.response = response
        self.process_images_calls = 0

    def process_image(self, **_: object) -> dict:
        return self.response

    def process_images(self, **_: object) -> dict:
        self.process_images_calls += 1
        return self.response


@pytest.mark.parametrize(
    "document_type",
    ["receipt", "discharge_summary", "lab_report", "prescription"],
)
def test_classifies_all_supported_types(
    document_type: str, sample_image: Image.Image
) -> None:
    classifier = DocumentClassifier(
        FakeClient(
            {
                "document_type": document_type,
                "confidence": 0.92,
                "reasoning": "Clear document layout",
            }
        )
    )
    result = classifier.classify(sample_image)
    assert result.document_type == document_type
    assert result.confidence == 0.92


def test_rejects_unknown_document_type(sample_image: Image.Image) -> None:
    classifier = DocumentClassifier(
        FakeClient({"document_type": "medical_note", "confidence": 0.8})
    )
    with pytest.raises(ValueError, match="Invalid document type"):
        classifier.classify(sample_image)


def test_multi_page_sends_all_pages(sample_image: Image.Image) -> None:
    client = FakeClient({"document_type": "lab_report", "confidence": 0.9})
    classifier = DocumentClassifier(client)
    result = classifier.classify_multi_page([sample_image, sample_image.copy()])
    assert result.document_type == "lab_report"
    assert client.process_images_calls == 1
