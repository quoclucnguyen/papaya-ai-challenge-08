"""Tests for PDF and image preprocessing."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from src.pipeline.preprocessor import preprocess_document


def test_loads_generated_pdf(sample_receipt_path: Path) -> None:
    pages = preprocess_document(sample_receipt_path)
    assert len(pages) == 1
    assert pages[0].mode == "RGB"
    assert pages[0].width > 1000


def test_loads_image(tmp_path: Path) -> None:
    path = tmp_path / "sample.png"
    Image.new("L", (20, 10), 128).save(path)
    pages = preprocess_document(path)
    assert pages[0].mode == "RGB"


def test_rejects_unsupported_file(tmp_path: Path) -> None:
    path = tmp_path / "sample.txt"
    path.write_text("not a document", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported file type"):
        preprocess_document(path)
