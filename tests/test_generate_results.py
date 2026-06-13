"""Tests for the batch result generation script."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_results import generate_results
from src.models.base import ExtractionResult


class FakePipeline:
    def extract(self, _: Path) -> ExtractionResult:
        return ExtractionResult(
            document_type="receipt",
            confidence=0.9,
            fields={
                "hospital_name": {
                    "value": "Test Hospital",
                    "confidence": 0.9,
                }
            },
        )


def test_generate_results_saves_json(tmp_path: Path) -> None:
    documents_dir = tmp_path / "documents"
    results_dir = tmp_path / "results"
    documents_dir.mkdir()
    (documents_dir / "receipt_01.pdf").write_bytes(b"fixture")

    successful, failed = generate_results(
        documents_dir=documents_dir,
        results_dir=results_dir,
        pipeline=FakePipeline(),
    )

    assert (successful, failed) == (1, 0)
    output = json.loads(
        (results_dir / "receipt_01.json").read_text(encoding="utf-8")
    )
    assert output["document_type"] == "receipt"
