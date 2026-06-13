"""Verify the committed fixture and ground-truth artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


def test_has_required_ten_documents(
    documents_dir: Path, expected_dir: Path
) -> None:
    pdfs = sorted(documents_dir.glob("*.pdf"))
    expected = sorted(expected_dir.glob("*.json"))
    assert len(pdfs) == 10
    assert len(expected) == 10
    assert [path.stem for path in pdfs] == [path.stem for path in expected]


def test_document_mix_matches_requirement(expected_dir: Path) -> None:
    counts = Counter(
        json.loads(path.read_text(encoding="utf-8"))["document_type"]
        for path in expected_dir.glob("*.json")
    )
    assert counts == {
        "receipt": 3,
        "discharge_summary": 3,
        "lab_report": 2,
        "prescription": 2,
    }


def test_expected_results_follow_output_shape(expected_dir: Path) -> None:
    for path in expected_dir.glob("*.json"):
        result = json.loads(path.read_text(encoding="utf-8"))
        assert set(result) == {
            "document_type",
            "confidence",
            "fields",
            "validation_errors",
        }
        for field_data in result["fields"].values():
            assert set(field_data) == {"value", "confidence"}
