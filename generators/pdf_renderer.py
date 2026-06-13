"""Portable PDF renderers based on PyMuPDF."""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any

import fitz  # type: ignore[import-untyped]

PAGE_WIDTH = 595
PAGE_HEIGHT = 842
MARGIN = 42


class PDFWriter:
    """Simple multi-page writer for realistic structured fixtures."""

    def __init__(self, title: str, facility: str) -> None:
        self.document = fitz.open()
        self.title = title
        self.facility = facility
        self.page: fitz.Page
        self.y = float(MARGIN)
        self._new_page()

    def _new_page(self) -> None:
        self.page = self.document.new_page(
            width=PAGE_WIDTH,
            height=PAGE_HEIGHT,
        )
        self.font_name = "helv"
        self.y = MARGIN
        self._text(self.facility, size=18, bold=True, color=(0.08, 0.22, 0.4))
        self._text(self.title, size=13, bold=True)
        self._rule()

    def _ensure_space(self, height: float) -> None:
        if self.y + height > PAGE_HEIGHT - MARGIN:
            self._new_page()

    def _text(
        self,
        text: str,
        *,
        size: float = 10,
        bold: bool = False,
        indent: float = 0,
        color: tuple[float, float, float] = (0.12, 0.12, 0.12),
    ) -> None:
        font_name = "hebo" if bold and self.font_name == "helv" else self.font_name
        lines = textwrap.wrap(
            str(text),
            width=max(35, int(92 - indent / 5)),
            replace_whitespace=False,
        ) or [""]
        line_height = size * 1.45
        self._ensure_space(line_height * len(lines))
        for line in lines:
            self.page.insert_text(
                (MARGIN + indent, self.y),
                line,
                fontsize=size,
                fontname=font_name,
                color=color,
            )
            self.y += line_height

    def _rule(self) -> None:
        self.page.draw_line(
            (MARGIN, self.y),
            (PAGE_WIDTH - MARGIN, self.y),
            color=(0.3, 0.45, 0.65),
            width=1,
        )
        self.y += 14

    def section(self, title: str) -> None:
        self.y += 4
        self._text(title.upper(), size=11, bold=True, color=(0.12, 0.3, 0.48))

    def field(self, label: str, value: Any) -> None:
        self._text(f"{label}: {value}", size=10)

    def row(self, values: list[str], widths: list[int]) -> None:
        cells = [
            str(value)[:width].ljust(width)
            for value, width in zip(values, widths, strict=True)
        ]
        self._text(" | ".join(cells), size=8.5)

    def save(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.document.set_metadata(
            {
                "title": self.title,
                "author": self.facility,
                "subject": "Synthetic medical document for extraction testing",
            }
        )
        self.document.save(
            output_path,
            garbage=4,
            deflate=True,
            no_new_id=True,
        )
        self.document.close()


def render_receipt(source: dict[str, Any], output_path: Path) -> None:
    writer = PDFWriter("HOSPITAL RECEIPT / INVOICE", source["hospital_name"])
    writer.field("Receipt No", source["receipt_number"])
    writer.field("Date", source["date"])
    writer.field("Patient", source["patient_name"])
    writer.field("Payment Method", source["payment_method"])
    writer.section("Itemized Charges")
    widths = [35, 5, 12, 12]
    writer.row(["Description", "Qty", "Unit Price", "Total"], widths)
    writer._rule()
    for item in source["items"]:
        writer.row(
            [
                item["description"],
                str(item["quantity"]),
                f"{item['unit_price']:.2f}",
                f"{item['total']:.2f}",
            ],
            widths,
        )
    writer._rule()
    writer.field("GRAND TOTAL", f"{source['grand_total']:.2f} THB")
    writer._text("Thank you for your payment.", size=9)
    writer.save(output_path)


def render_discharge(source: dict[str, Any], output_path: Path) -> None:
    writer = PDFWriter("DISCHARGE SUMMARY", source["hospital_name"])
    writer.field("Patient Name", source["patient_name"])
    writer.field("Patient ID", source["patient_id"])
    writer.field("Admission Date", source["admission_date"])
    writer.field("Discharge Date", source["discharge_date"])
    writer.field("Attending Physician", source["attending_physician"])
    writer.section("Diagnosis")
    writer.field("Primary", source["diagnosis"]["primary"])
    for diagnosis in source["diagnosis"].get("secondary", []):
        writer.field("Secondary", diagnosis)
    writer.section("Procedures Performed")
    for procedure in source["procedures"]:
        writer._text(
            f"- {procedure['name']} | Code: {procedure.get('code') or 'N/A'} "
            f"| Date: {procedure.get('date') or 'N/A'}",
            indent=8,
        )
    writer.section("Discharge Instructions")
    writer._text(source["discharge_instructions"])
    writer.section("Physician Signature")
    writer._text(source["attending_physician"])
    writer.save(output_path)


def render_lab(source: dict[str, Any], output_path: Path) -> None:
    writer = PDFWriter("LABORATORY REPORT", source["lab_name"])
    writer.field("Patient Name", source["patient_name"])
    writer.field("Patient ID", source["patient_id"])
    writer.field("Report Date", source["date"])
    writer.field("Ordering Physician", source["doctor"])
    writer.section("Test Results")
    widths = [27, 10, 12, 18, 7]
    writer.row(["Test", "Result", "Unit", "Reference", "Flag"], widths)
    writer._rule()
    for test in source["tests"]:
        writer.row(
            [
                test["test_name"],
                str(test["result"]),
                test.get("unit") or "-",
                test.get("reference_range") or "-",
                test["flag"].upper(),
            ],
            widths,
        )
    writer.save(output_path)


def render_prescription(source: dict[str, Any], output_path: Path) -> None:
    writer = PDFWriter("MEDICAL PRESCRIPTION", source["clinic_name"])
    writer.field("Patient", source["patient_name"])
    writer.field("Patient ID", source["patient_id"])
    writer.field("Date", source["date"])
    writer.field("Prescribing Physician", source["doctor_name"])
    writer.section("Medications")
    for index, medication in enumerate(source["medications"], 1):
        writer._text(f"{index}. {medication['name']}", bold=True)
        writer.field("Dosage", medication.get("dosage") or "N/A")
        writer.field("Frequency", medication.get("frequency") or "N/A")
        writer.field("Duration", medication.get("duration") or "N/A")
        writer.field("Quantity", medication.get("quantity") or "N/A")
        writer.y += 4
    writer.section("Prescriber")
    writer._text(f"{source['doctor_name']}, MD")
    writer.save(output_path)
