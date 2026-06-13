# Checklist nghiệm thu - Challenge 08

Ngày cập nhật: 2026-06-13

## Project

- [x] Python 3.11+ và `pyproject.toml`
- [x] OpenRouter/OpenAI SDK, Pydantic, Pillow, PyMuPDF, pytest
- [x] `.env.example` với `OPENROUTER_API_KEY`
- [x] `pip install -e ".[dev]"` thành công

## Models và output

- [x] `ConfidenceField` có `value` và confidence 0.0-1.0
- [x] Models cho receipt, discharge summary, lab report, prescription
- [x] `ExtractionResult` đúng output shape
- [x] Missing value được chuẩn hóa thành `null` + confidence `0.0`
- [x] Nested fields được Pydantic validate trước khi trả output

## Classification và extraction

- [x] Hỗ trợ 4 document types
- [x] Classification có confidence
- [x] Type-specific prompt và extractor cho cả 4 types
- [x] Multi-page gửi toàn bộ pages cho model
- [x] Parser chịu được `null`, invalid date và invalid number
- [ ] Xác minh OpenRouter classification đúng 10/10 documents
- [ ] Đối chiếu extraction thực tế với ground truth

## Validation

- [x] Date format/range/future validation
- [x] Admission date không sau discharge date
- [x] Amount và quantity phải dương
- [x] Item line calculation tolerance 1%
- [x] Item totals so với grand total tolerance 5%
- [x] Low classification/field confidence warnings
- [x] Validation được wire vào production pipeline

## Test artifacts

- [x] 3 receipts
- [x] 3 discharge summaries
- [x] 2 lab reports
- [x] 2 prescriptions
- [x] Tổng cộng 10 PDF trong `tests/fixtures/documents/`
- [x] 10 ground-truth JSON trong `tests/expected/`
- [x] PDF và expected JSON được sinh từ cùng source data

## Tests và quality

- [x] Model tests
- [x] Classifier tests
- [x] Extractor tests
- [x] Validator tests
- [x] Preprocessor tests
- [x] OpenRouter client helper tests
- [x] Pipeline single-page, multi-page và batch tests
- [x] Artifact count/type tests
- [x] `pytest`: 54 passed
- [x] Source coverage: 83%
- [x] `ruff`: passed
- [x] `mypy`: passed
- [x] Generator deterministic cho cả 20 PDF/JSON artifacts

## Submission

- [x] README setup/run/prompt engineering
- [x] Timeline estimate trong `PLAN.md`
- [x] 10 test documents included
- [x] Ground truth included
- [ ] Chạy `python scripts/generate_results.py` bằng OpenRouter key hợp lệ
- [ ] Commit 10 actual extraction JSON trong `results/extractions/`
- [ ] Xác minh/push GitHub repository

> Code và offline verification đã hoàn tất. Ba mục cuối cần API key hoặc Git remote.
