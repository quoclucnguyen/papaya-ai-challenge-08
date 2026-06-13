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
tương ứng nằm trong `tests/expected/`; kết quả extraction thực từ OpenRouter nằm trong
`results/extractions/`.

### Test documents and extraction results

Repository include đủ 10 test PDF documents, 10 expected extraction JSON và 10 live
extraction result JSON:

| # | Document type | Test document | Expected extraction | Live extraction result |
|---|---|---|---|---|
| 1 | receipt | `tests/fixtures/documents/receipt_01.pdf` | `tests/expected/receipt_01.json` | `results/extractions/receipt_01.json` |
| 2 | receipt | `tests/fixtures/documents/receipt_02.pdf` | `tests/expected/receipt_02.json` | `results/extractions/receipt_02.json` |
| 3 | receipt | `tests/fixtures/documents/receipt_03.pdf` | `tests/expected/receipt_03.json` | `results/extractions/receipt_03.json` |
| 4 | discharge_summary | `tests/fixtures/documents/discharge_01.pdf` | `tests/expected/discharge_01.json` | `results/extractions/discharge_01.json` |
| 5 | discharge_summary | `tests/fixtures/documents/discharge_02.pdf` | `tests/expected/discharge_02.json` | `results/extractions/discharge_02.json` |
| 6 | discharge_summary | `tests/fixtures/documents/discharge_03.pdf` | `tests/expected/discharge_03.json` | `results/extractions/discharge_03.json` |
| 7 | lab_report | `tests/fixtures/documents/lab_01.pdf` | `tests/expected/lab_01.json` | `results/extractions/lab_01.json` |
| 8 | lab_report | `tests/fixtures/documents/lab_02.pdf` | `tests/expected/lab_02.json` | `results/extractions/lab_02.json` |
| 9 | prescription | `tests/fixtures/documents/prescription_01.pdf` | `tests/expected/prescription_01.json` | `results/extractions/prescription_01.json` |
| 10 | prescription | `tests/fixtures/documents/prescription_02.pdf` | `tests/expected/prescription_02.json` | `results/extractions/prescription_02.json` |

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

Prompt được thiết kế theo hướng tách trách nhiệm giữa model và code: model chịu trách
nhiệm đọc nội dung nhìn thấy trên document, còn code chịu trách nhiệm normalize và
validate business rules.

- **Two-stage prompting:** chạy classification trước để chọn một trong 4 loại cố định
  (`receipt`, `discharge_summary`, `lab_report`, `prescription`), sau đó mới chạy
  extraction với schema riêng cho loại đó. Cách này giảm schema noise và giảm khả năng
  model điền nhầm field giữa các document type.
- **Schema-specific extraction:** mỗi prompt extraction mô tả đúng field bắt buộc của
  document type, kiểu dữ liệu mong muốn, nested list format và yêu cầu confidence cho
  từng field/item.
- **JSON-only contract:** prompt yêu cầu trả về JSON object duy nhất, không markdown,
  không giải thích thêm. Client cũng yêu cầu `response_format={"type": "json_object"}`
  khi model hỗ trợ.
- **Anti-hallucination constraint:** nếu thông tin không nhìn thấy hoặc không chắc chắn,
  model phải trả `null` với confidence thấp (`0.0` hoặc gần `0.0`) thay vì tự suy đoán.
- **Confidence calibration:** prompt nhấn mạnh confidence phải phản ánh độ rõ của text,
  vị trí field và tính nhất quán của document; không được set tất cả confidence cao một
  cách đồng đều.
- **Validation outside the LLM:** date parsing, amount positivity, line-item sum vs.
  grand total tolerance 5%, confidence bounds và missing-field normalization được thực
  hiện bằng Pydantic/validator code để kết quả ổn định và testable hơn.
- **Robust retry strategy:** một số vision model yếu có thể loop/truncate khi bị ép JSON
  mode. Client retry; từ retry thứ 2 bỏ strict JSON mode và parse JSON lenient để vẫn
  lấy được object hợp lệ nếu model sinh thêm text ngoài JSON.
- **No hardcoding to fixtures:** prompt không chứa tên bệnh viện/bệnh nhân cụ thể từ bộ
  test; pipeline chỉ dựa vào document image/PDF input và schema theo type nên có thể tái
  sử dụng cho document mới cùng format.

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
