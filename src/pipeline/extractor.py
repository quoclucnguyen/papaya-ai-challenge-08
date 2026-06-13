"""Main extraction pipeline.

Coordinates classification, extraction, and validation.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Union

from pydantic import BaseModel

from src.extractors.classifier import DocumentClassifier, get_default_classifier
from src.extractors.discharge import get_discharge_extractor
from src.extractors.lab import get_lab_extractor
from src.extractors.prescription import get_prescription_extractor
from src.extractors.receipt import get_receipt_extractor
from src.models.base import ExtractionResult, ProcessingFailure, ValidationError
from src.models.discharge import DischargeFields
from src.models.lab import LabFields
from src.models.prescription import PrescriptionFields
from src.models.receipt import ReceiptFields
from src.pipeline.preprocessor import preprocess_document
from src.utils.llm import LLMClient, get_default_client
from src.validators import validate_result

FIELD_MODELS: dict[str, type[BaseModel]] = {
    "receipt": ReceiptFields,
    "discharge_summary": DischargeFields,
    "lab_report": LabFields,
    "prescription": PrescriptionFields,
}

SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"}


class ExtractionPipeline:
    """Main pipeline for medical document extraction."""

    def __init__(
        self,
        client: LLMClient | None = None,
        classifier: DocumentClassifier | None = None,
    ):
        """
        Initialize extraction pipeline.

        Args:
            client: LLM client (uses default if not provided)
            classifier: Document classifier (uses default if not provided)
        """
        self.client = client or get_default_client()
        self.classifier = classifier or get_default_classifier(self.client)

        # Get extractors for each type
        self.extractors = {
            "receipt": get_receipt_extractor(self.client),
            "discharge_summary": get_discharge_extractor(self.client),
            "lab_report": get_lab_extractor(self.client),
            "prescription": get_prescription_extractor(self.client),
        }

    def extract(self, document_path: Union[str, Path]) -> ExtractionResult:
        """
        Extract structured data from a medical document.

        Args:
            document_path: Path to PDF or image file

        Returns:
            ExtractionResult with fields, confidence, and validation errors
        """
        document_path = Path(document_path)

        # Step 1: Preprocess - convert to images
        images = preprocess_document(document_path)

        if not images:
            raise ValueError("Document preprocessing produced no pages")

        if len(images) > 1:
            classification = self.classifier.classify_multi_page(images)
        else:
            classification = self.classifier.classify(images[0])

        # Step 3: Extract fields using type-specific extractor
        extractor = self.extractors.get(classification.document_type)
        if not extractor:
            raise ValueError(f"No extractor for type: {classification.document_type}")

        # Extract from all pages and merge
        if len(images) == 1:
            extracted_fields = extractor.extract(images[0])
        else:
            extracted_fields = extractor.extract_multi_page(images)

        field_model = FIELD_MODELS[classification.document_type]
        validated_fields = field_model.model_validate(extracted_fields).model_dump()

        result = ExtractionResult(
            document_type=classification.document_type,
            confidence=classification.confidence,
            fields=validated_fields,
            validation_errors=[],
        )

        parse_errors = extractor.consume_validation_errors()
        validation_errors = parse_errors + validate_result(result)
        result.validation_errors = validation_errors

        field_confidences = [
            float(field["confidence"])
            for field in validated_fields.values()
            if isinstance(field, dict) and field.get("value") is not None
        ]
        if field_confidences:
            result.confidence = min(
                result.confidence,
                sum(field_confidences) / len(field_confidences),
            )

        penalty = sum(
            {
                "critical": 0.25,
                "error": 0.15,
                "warning": 0.05,
                "info": 0.0,
            }[error.severity]
            for error in validation_errors
        )
        result.confidence = max(0.0, result.confidence - penalty)

        return result

    def extract_batch(
        self, document_paths: Sequence[Union[str, Path]]
    ) -> list[ExtractionResult | ProcessingFailure]:
        """
        Extract from multiple documents.

        Args:
            document_paths: List of document paths

        Returns:
            List of ExtractionResults
        """
        results: list[ExtractionResult | ProcessingFailure] = []
        for path in document_paths:
            try:
                result = self.extract(path)
                results.append(result)
            except Exception as e:
                # Log error but continue processing other documents
                print(f"Error processing {path}: {e}")
                # Create error result
                results.append(
                    ProcessingFailure(
                        validation_errors=[
                            ValidationError(
                                field="document",
                                message=f"Failed to process: {e}",
                                severity="critical",
                            )
                        ]
                    )
                )
        return results


def extract_from_document(
    document_path: Union[str, Path], client: LLMClient | None = None
) -> dict:
    """
    Extract structured data from a medical document.

    Args:
        document_path: Path to PDF or image file
        client: Optional LLM client

    Returns:
        Extraction result dict
    """
    pipeline = ExtractionPipeline(client=client)
    result = pipeline.extract(document_path)
    return result.model_dump(mode="json")


def main() -> None:
    """CLI entry point."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.pipeline.extractor <document_path>")
        sys.exit(1)

    document_path = Path(sys.argv[1])
    if not document_path.exists():
        print(f"Error: File not found: {document_path}")
        sys.exit(1)

    try:
        if document_path.is_dir():
            paths = sorted(
                path
                for path in document_path.iterdir()
                if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
            )
            pipeline = ExtractionPipeline()
            payload: Any = [
                result.model_dump(mode="json")
                for result in pipeline.extract_batch(paths)
            ]
        else:
            payload = extract_from_document(document_path)
        print(json.dumps(payload, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
