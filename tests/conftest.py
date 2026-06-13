"""Pytest configuration and fixtures."""

from collections.abc import Generator
from pathlib import Path

import pytest
from PIL import Image

# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"
DOCUMENTS_DIR = FIXTURES_DIR / "documents"
EXPECTED_DIR = Path(__file__).parent / "expected"


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def documents_dir() -> Path:
    """Path to test documents directory."""
    return DOCUMENTS_DIR


@pytest.fixture
def expected_dir() -> Path:
    """Path to expected results directory."""
    return EXPECTED_DIR


@pytest.fixture
def sample_receipt_path() -> Path:
    """Path to sample receipt document."""
    return DOCUMENTS_DIR / "receipt_01.pdf"


@pytest.fixture
def sample_discharge_path() -> Path:
    """Path to sample discharge summary."""
    return DOCUMENTS_DIR / "discharge_01.pdf"


@pytest.fixture
def sample_lab_path() -> Path:
    """Path to sample lab report."""
    return DOCUMENTS_DIR / "lab_01.pdf"


@pytest.fixture
def sample_prescription_path() -> Path:
    """Path to sample prescription."""
    return DOCUMENTS_DIR / "prescription_01.pdf"


@pytest.fixture
def mock_api_key(monkeypatch) -> None:
    """Mock OpenRouter API key for testing."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key_for_mocking")


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Temporary directory for test outputs."""
    output_dir = tmp_path / "output"
    output_dir.mkdir(exist_ok=True)
    yield output_dir


@pytest.fixture
def sample_image() -> Image.Image:
    """Small RGB image for mocked vision requests."""
    return Image.new("RGB", (120, 80), "white")
