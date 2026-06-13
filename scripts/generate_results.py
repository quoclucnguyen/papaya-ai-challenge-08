"""Run the OpenRouter extraction pipeline for all generated test documents."""

from __future__ import annotations

import json
from pathlib import Path

from src.pipeline.extractor import ExtractionPipeline

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_DOCUMENTS_DIR = PROJECT_ROOT / "tests" / "fixtures" / "documents"
DEFAULT_RESULTS_DIR = PROJECT_ROOT / "results" / "extractions"


def generate_results(
    documents_dir: Path = DEFAULT_DOCUMENTS_DIR,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    pipeline: ExtractionPipeline | None = None,
) -> tuple[int, int]:
    """Extract all PDFs and return successful/failed counts."""
    pdf_files = sorted(documents_dir.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files found in {documents_dir}. "
            "Run: python -m generators.main"
        )

    results_dir.mkdir(parents=True, exist_ok=True)
    active_pipeline = pipeline or ExtractionPipeline()
    successful = 0
    failed = 0

    for document_path in pdf_files:
        print(f"Processing {document_path.name}...")
        try:
            result = active_pipeline.extract(document_path)
        except Exception as exc:
            failed += 1
            print(f"  ERROR: {exc}")
            continue

        output_path = results_dir / f"{document_path.stem}.json"
        output_path.write_text(
            json.dumps(
                result.model_dump(mode="json"),
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        successful += 1
        print(
            f"  {result.document_type}, confidence={result.confidence:.2f}, "
            f"validation_errors={len(result.validation_errors)}"
        )

    return successful, failed


def main() -> int:
    """CLI entry point."""
    try:
        successful, failed = generate_results()
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1

    print(
        f"Finished: {successful} result(s) saved to {DEFAULT_RESULTS_DIR}; "
        f"{failed} failed."
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
