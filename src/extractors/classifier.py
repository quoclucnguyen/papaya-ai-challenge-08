"""Document classifier using vision LLM."""

from __future__ import annotations

from PIL import Image
from pydantic import BaseModel, Field

from src.prompts.classification import (
    CLASSIFICATION_SYSTEM_PROMPT,
    CLASSIFICATION_USER_PROMPT_TEMPLATE,
    MULTI_PAGE_CLASSIFICATION_HINT,
)
from src.utils.llm import LLMClient


class ClassificationResult(BaseModel):
    """Result of document classification."""

    document_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str | None = None

    def is_confident(self, threshold: float = 0.7) -> bool:
        """Check if classification confidence is above threshold."""
        return self.confidence >= threshold

    def __repr__(self) -> str:
        return f"ClassificationResult(type={self.document_type}, confidence={self.confidence})"


class DocumentClassifier:
    """Classifies medical documents into 4 types using vision LLM."""

    def __init__(self, client: LLMClient | None = None):
        """
        Initialize document classifier.

        Args:
            client: LLM client (uses default if not provided)
        """
        self.client = client or LLMClient()

    def classify(
        self,
        image: Image.Image,
        multi_page: bool = False,
    ) -> ClassificationResult:
        """
        Classify a document from its image.

        Args:
            image: PIL Image of the document
            multi_page: Whether this is part of a multi-page document

        Returns:
            ClassificationResult with document type and confidence
        """
        user_prompt = CLASSIFICATION_USER_PROMPT_TEMPLATE
        if multi_page:
            user_prompt += MULTI_PAGE_CLASSIFICATION_HINT

        response = self.client.process_image(
            image=image,
            system_prompt=CLASSIFICATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            output_format="json",
        )
        if not isinstance(response, dict):
            raise TypeError("LLM classification response must be a JSON object")
        return self._parse_response(response)

    def _parse_response(self, response: dict) -> ClassificationResult:
        """Validate a raw classification response."""
        document_type = response.get("document_type", "")
        try:
            confidence = float(response.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = min(1.0, max(0.0, confidence))
        reasoning = response.get("reasoning", "")

        # Validate document type
        valid_types = {"receipt", "discharge_summary", "lab_report", "prescription"}
        if document_type not in valid_types:
            raise ValueError(
                f"Invalid document type: {document_type}. Must be one of {valid_types}"
            )

        return ClassificationResult(
            document_type=document_type,
            confidence=confidence,
            reasoning=str(reasoning) if reasoning is not None else None,
        )

    def classify_multi_page(
        self,
        images: list[Image.Image],
    ) -> ClassificationResult:
        """
        Classify a multi-page document.

        Args:
            images: List of PIL Images (pages)

        Returns:
            ClassificationResult from first page (most representative)
        """
        if not images:
            raise ValueError("At least one page is required")

        response = self.client.process_images(
            images=images,
            system_prompt=CLASSIFICATION_SYSTEM_PROMPT,
            user_prompt=(
                CLASSIFICATION_USER_PROMPT_TEMPLATE
                + MULTI_PAGE_CLASSIFICATION_HINT
            ),
            output_format="json",
        )
        if not isinstance(response, dict):
            raise TypeError("LLM classification response must be a JSON object")
        return self._parse_response(response)


def get_default_classifier(client: LLMClient | None = None) -> DocumentClassifier:
    """Get default document classifier."""
    return DocumentClassifier(client)
