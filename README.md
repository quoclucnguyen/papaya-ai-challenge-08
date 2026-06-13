# Challenge 08 - Medical Document Extractor

Pipeline Python trích xuất dữ liệu có cấu trúc từ medical PDF/image bằng vision model
qua **OpenRouter**. Pipeline gồm preprocessing, classification, extraction theo từng
document type, Pydantic normalization và business validation.

## Setup

Yêu cầu Python 3.11+:

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -e ".[dev]"
```

Tạo `.env` từ `.env.example` và điền key:

```dotenv
OPENROUTER_API_KEY=your_key
OPENROUTER_MODEL=google/gemini-2.5-flash
```

Model có thể đổi sang bất kỳ OpenRouter model nào hỗ trợ image input và JSON output.

## Commands

```bash
# Sinh lại 10 PDF và 10 ground-truth JSON
python -m generators.main

# Trích xuất một document
python -m src.pipeline.extractor tests/fixtures/documents/receipt_01.pdf

# Trích xuất cả thư mục và in JSON ra console
python -m src.pipeline.extractor tests/fixtures/documents/

# Lưu kết quả OpenRouter của 10 documents
python scripts/generate_results.py

# Verification
pytest
ruff check src generators scripts tests
mypy src generators scripts
```

## Dataset

`tests/fixtures/documents/` chứa:

- 3 hospital receipts/invoices
- 3 discharge summaries
- 2 lab reports
- 2 prescriptions

PDF được tạo trực tiếp bằng PyMuPDF, không cần GTK/Pango hoặc Poppler. Ground truth
tương ứng nằm trong `tests/expected/`.

## Output

```json
{
  "document_type": "receipt",
  "confidence": 0.91,
  "fields": {
    "hospital_name": {
      "value": "Bangkok Hospital",
      "confidence": 0.98
    },
    "grand_total": {
      "value": 6450.0,
      "confidence": 0.96
    }
  },
  "validation_errors": []
}
```

Missing fields được chuẩn hóa thành `null` với confidence `0.0`.

## Architecture

```text
PDF/image
  -> PyMuPDF/Pillow preprocessing
  -> OpenRouter vision classification
  -> type-specific OpenRouter extraction
  -> Pydantic field normalization
  -> date, amount, sum and confidence validators
  -> ExtractionResult JSON
```

Multi-page PDF được gửi đầy đủ trong cùng request classification và extraction.

## Prompt Engineering

- Two-stage prompts: classify trước, extract bằng schema riêng cho từng type.
- Chỉ cho phép 4 document types cố định.
- JSON-only output và field-by-field confidence.
- Negative constraint: không nhìn thấy thì `null` + `0.0`, không suy đoán.
- Date/number normalization và business validation được làm bằng code, không giao hoàn
  toàn cho model.
- Confidence thấp, date sai, amount không dương và lệch tổng trên 5% được ghi vào
  `validation_errors`.

## OpenRouter

Client dùng OpenAI-compatible endpoint:

```text
https://openrouter.ai/api/v1
```

Ảnh được gửi dưới dạng base64 data URL qua `image_url`; JSON mode được yêu cầu bằng
`response_format={"type": "json_object"}`. Có thể cấu hình thêm:

```dotenv
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MAX_TOKENS=4096
OPENROUTER_APP_URL=http://localhost
OPENROUTER_APP_TITLE=Medical Document Extractor
```

## Verification

Kết quả local ngày 2026-06-13 (live run 2026-06-14):

```text
pytest: 56 passed
coverage: 83%
ruff: passed
mypy: passed
pip install -e ".[dev]": passed
fixtures: 10 PDF + 10 expected JSON
generator: deterministic SHA-256 for all 20 artifacts
live extraction: 10/10 documents, khớp tuyệt đối ground truth (0 validation error)
```

Live run dùng model `nvidia/nemotron-nano-12b-v2-vl:free`. Unit/integration tests dùng
mocked OpenRouter responses nên không tiêu tốn API credit. Kết quả thực trong
`results/extractions/` được tạo khi chạy `python scripts/generate_results.py` với API
key hợp lệ.

Vision model yếu đôi khi loop/truncate khi bị ép JSON mode. Client tự retry và, từ lần
retry thứ 2, bỏ `response_format=json_object` rồi parse JSON lenient
(`OPENROUTER_MAX_ATTEMPTS`, mặc định 3).
