"""Generate 10 medical PDF fixtures and their ground-truth JSON files."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from generators.discharge import SAMPLE_DISCHARGES
from generators.lab import SAMPLE_LABS
from generators.pdf_renderer import (
    render_discharge,
    render_lab,
    render_prescription,
    render_receipt,
)
from generators.prescription import SAMPLE_PRESCRIPTIONS
from generators.receipt import SAMPLE_RECEIPTS

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_DOCUMENTS_DIR = PROJECT_ROOT / "tests" / "fixtures" / "documents"
DEFAULT_EXPECTED_DIR = PROJECT_ROOT / "tests" / "expected"


def confidence_field(value: Any) -> dict[str, Any]:
    """Wrap a known ground-truth value using the extraction output shape."""
    return {"value": value, "confidence": 1.0 if value is not None else 0.0}


def build_expected(document_type: str, source: dict[str, Any]) -> dict[str, Any]:
    """Build a reference extraction result from generator source data."""
    if document_type == "receipt":
        fields = {
            "hospital_name": confidence_field(source["hospital_name"]),
            "patient_name": confidence_field(source["patient_name"]),
            "date": confidence_field(source["date"]),
            "items": confidence_field(source["items"]),
            "grand_total": confidence_field(source["grand_total"]),
            "payment_method": confidence_field(source["payment_method"]),
        }
    elif document_type == "discharge_summary":
        fields = {
            "hospital_name": confidence_field(source["hospital_name"]),
            "patient_name": confidence_field(source["patient_name"]),
            "admission_date": confidence_field(source["admission_date"]),
            "discharge_date": confidence_field(source["discharge_date"]),
            "diagnosis": confidence_field(source["diagnosis"]),
            "procedures_performed": confidence_field(source["procedures"]),
            "attending_physician": confidence_field(
                source["attending_physician"]
            ),
            "discharge_instructions": confidence_field(
                source["discharge_instructions"]
            ),
        }
    elif document_type == "lab_report":
        fields = {
            "lab_name": confidence_field(source["lab_name"]),
            "patient_name": confidence_field(source["patient_name"]),
            "date": confidence_field(source["date"]),
            "tests": confidence_field(source["tests"]),
        }
    elif document_type == "prescription":
        fields = {
            "doctor_name": confidence_field(source["doctor_name"]),
            "patient_name": confidence_field(source["patient_name"]),
            "date": confidence_field(source["date"]),
            "medications": confidence_field(source["medications"]),
        }
    else:
        raise ValueError(f"Unsupported document type: {document_type}")

    return {
        "document_type": document_type,
        "confidence": 1.0,
        "fields": fields,
        "validation_errors": [],
    }


def generate_all_documents(
    output_dir: Path = DEFAULT_DOCUMENTS_DIR,
    expected_dir: Path = DEFAULT_EXPECTED_DIR,
) -> None:
    """Generate PDFs and matching expected JSON files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    expected_dir.mkdir(parents=True, exist_ok=True)

    jobs: list[
        tuple[str, str, list[dict[str, Any]], Any]
    ] = [
        ("receipt", "receipt", SAMPLE_RECEIPTS, render_receipt),
        (
            "discharge",
            "discharge_summary",
            SAMPLE_DISCHARGES,
            render_discharge,
        ),
        ("lab", "lab_report", SAMPLE_LABS, render_lab),
        (
            "prescription",
            "prescription",
            SAMPLE_PRESCRIPTIONS,
            render_prescription,
        ),
    ]

    generated = 0
    for filename_prefix, document_type, samples, renderer in jobs:
        for index, source in enumerate(samples, 1):
            stem = f"{filename_prefix}_{index:02d}"
            renderer(source, output_dir / f"{stem}.pdf")
            expected = build_expected(document_type, source)
            (expected_dir / f"{stem}.json").write_text(
                json.dumps(expected, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"Generated {stem}.pdf and {stem}.json")
            generated += 1

    print(
        f"Generated {generated} documents in {output_dir} "
        f"and ground truth in {expected_dir}"
    )


def main() -> None:
    """CLI entry point."""
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DOCUMENTS_DIR
    expected_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_EXPECTED_DIR
    generate_all_documents(output_dir, expected_dir)


if __name__ == "__main__":
    main()
