"""Convert PDF or image documents into PIL images for vision models."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path
from typing import Union

from PIL import Image

try:
    import fitz  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - dependency is declared by the project
    fitz = None  # type: ignore[assignment]


SUPPORTED_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".tiff",
    ".tif",
    ".bmp",
    ".gif",
    ".webp",
}


def preprocess_document(document_path: Union[str, Path]) -> list[Image.Image]:
    """Convert a PDF or image file to one RGB image per page."""
    path = Path(document_path)
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")
    if not path.is_file():
        raise ValueError(f"Document path must be a file: {path}")

    if is_pdf(path):
        return _convert_pdf_to_images(path)
    if is_image(path):
        return _load_image(path)
    raise ValueError(
        f"Unsupported file type: {path.suffix}. "
        "Supported: .pdf, .png, .jpg, .jpeg, .tiff, .bmp, .webp"
    )


def _convert_pdf_to_images(pdf_path: Path) -> list[Image.Image]:
    """Render PDF pages with PyMuPDF, avoiding an external Poppler install."""
    if fitz is None:
        raise ImportError(
            "PyMuPDF is required for PDF processing. Install with: pip install pymupdf"
        )

    images: list[Image.Image] = []
    try:
        with fitz.open(pdf_path) as document:
            matrix = fitz.Matrix(2.0, 2.0)
            for page in document:
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                image = Image.open(io.BytesIO(pixmap.tobytes("png")))
                images.append(image.convert("RGB"))
    except Exception as exc:
        raise RuntimeError(f"Failed to convert PDF to images: {exc}") from exc

    if not images:
        raise RuntimeError(f"PDF has no pages: {pdf_path}")
    return images


def _load_image(image_path: Path) -> list[Image.Image]:
    """Load a single image file and detach it from the source file handle."""
    try:
        with Image.open(image_path) as source:
            image = source.convert("RGB")
            image.load()
        return [image]
    except Exception as exc:
        raise RuntimeError(f"Failed to load image: {exc}") from exc


def image_to_bytes(image: Image.Image, format: str = "PNG") -> bytes:
    """Convert a PIL image to bytes."""
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    return buffer.getvalue()


def optimize_image_for_llm(
    image: Image.Image, max_size: tuple[int, int] = (2048, 2048)
) -> Image.Image:
    """Resize an image while preserving aspect ratio."""
    optimized = image.copy()
    if optimized.width > max_size[0] or optimized.height > max_size[1]:
        optimized.thumbnail(max_size, Image.Resampling.LANCZOS)
    return optimized


def is_pdf(document_path: Union[str, Path]) -> bool:
    """Return whether a path has a PDF extension."""
    return Path(document_path).suffix.lower() == ".pdf"


def is_image(document_path: Union[str, Path]) -> bool:
    """Return whether a path has a supported image extension."""
    return Path(document_path).suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS


def save_images_temporarily(
    images: list[Image.Image], prefix: str = "page"
) -> list[Path]:
    """Save images to temporary PNG files."""
    temp_paths: list[Path] = []
    for index, image in enumerate(images):
        with tempfile.NamedTemporaryFile(
            suffix=".png",
            prefix=f"{prefix}_{index}_",
            delete=False,
        ) as file_handle:
            image.save(file_handle.name, "PNG")
            temp_paths.append(Path(file_handle.name))
    return temp_paths
