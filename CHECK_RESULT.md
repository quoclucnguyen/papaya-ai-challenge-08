# Kết quả kiểm tra AI Challenge 08

Ngày kiểm tra: 2026-06-13 (cập nhật live 2026-06-14)

## Kết luận

**Trạng thái: ĐẠT — ĐÃ XÁC MINH LIVE OPENROUTER 10/10.**

Live run với model `nvidia/nemotron-nano-12b-v2-vl:free`: **10/10 document trích xuất
thành công và khớp tuyệt đối ground truth** (đúng classification + mọi field), 0
validation error. Kết quả nằm trong `results/extractions/`.

Hai document list-nặng (lab) ban đầu fail do model free loop/truncate trong forced
JSON mode; đã sửa bằng retry + escalation (bỏ `response_format=json_object` từ lần
retry, parse JSON lenient). Xem mục "Gia cố độ bền".

### Lịch sử trạng thái trước đó

**Trạng thái ban đầu: ĐẠT OFFLINE, CÒN BƯỚC XÁC MINH LIVE OPENROUTER.**

Các blocker trong lần kiểm tra trước đã được sửa:

- Pipeline khởi tạo và chạy được với injected/mock OpenRouter client.
- Validator registry được wire vào production pipeline.
- Parser xử lý an toàn `null`, invalid date và invalid number.
- Multi-page gửi toàn bộ pages cho classification và extraction.
- Batch failure không còn tạo `ExtractionResult` sai document type.
- Packaging editable hoạt động.
- Generator không còn phụ thuộc WeasyPrint/GTK hoặc Poppler.
- Có đủ 10 PDF và 10 ground-truth JSON.
- README/test metrics đã được cập nhật theo kết quả chạy thật.

Chưa thể xác nhận accuracy live hoặc tạo 10 actual extraction JSON vì môi trường không
có `.env` và `OPENROUTER_API_KEY`.

## OpenRouter

Implementation dùng OpenAI-compatible API:

```text
Base URL: https://openrouter.ai/api/v1
Default model: google/gemini-2.5-flash
API key: OPENROUTER_API_KEY
```

Vision pages được gửi dưới dạng base64 `image_url`. JSON mode dùng:

```json
{"type": "json_object"}
```

Model và base URL có thể đổi qua environment variables mà không sửa code.

## Kết quả verification

Đã chạy tại `answers/challenge-08`:

```text
pip install -e ".[dev]"                         PASS
pytest                                           PASS - 54/54
pytest --cov=src                                 PASS - 83% coverage
ruff check src generators scripts tests          PASS
mypy src generators scripts                      PASS
python -m compileall -q src generators scripts   PASS
python -m generators.main                        PASS
PDF text audit                                   PASS - 10/10
Generator SHA-256 repeatability                  PASS - 20/20 artifacts
```

Artifact:

| Hạng mục | Kết quả |
|---|---:|
| Receipt PDFs | 3 |
| Discharge summary PDFs | 3 |
| Lab report PDFs | 2 |
| Prescription PDFs | 2 |
| Tổng PDFs | 10 |
| Ground-truth JSON | 10 |
| Actual OpenRouter extraction JSON | 10 |
| Khớp ground truth (live) | 10/10 |

## Các sửa đổi chính

### Pipeline và models

- Sửa factory classifier nhận shared client.
- Typed field models được validate trước khi tạo `ExtractionResult`.
- Missing value tự động có confidence `0.0`.
- Parser errors được đưa vào `validation_errors`.
- Overall confidence kết hợp classification/field confidence và validation penalty.
- Directory CLI và batch failure hoạt động đúng.

### Validation

- Date format, year range, future date và admission/discharge relationship.
- Amount, quantity, unit price và total phải dương.
- Item calculation tolerance 1%.
- Item sum so với grand total tolerance 5%, kể cả trường hợp tổng bằng 0.
- Warning cho classification dưới 0.7 và field confidence dưới 0.5.

### Documents

- PDF generation bằng PyMuPDF, portable và không cần native GTK/Pango.
- PDF có text layer audit được.
- PDF và expected JSON dùng chung source data.
- Chạy generator lại giữ nguyên SHA-256 của toàn bộ 20 artifacts.

### Tests

54 tests bao phủ:

- Models và serialization.
- 4 classification types.
- 4 type-specific extractors và null handling.
- Date/amount/sum validation.
- OpenRouter config, image data URL và request payload.
- PDF/image preprocessing.
- Pipeline single-page, multi-page và batch failure.
- Batch result writer.
- Số lượng/type của 10 documents và expected JSON.

## Đối chiếu yêu cầu

| Tiêu chí | Đánh giá | Ghi chú |
|---|---|---|
| PDF và image input | PASS | PyMuPDF + Pillow |
| 4 document types | PASS | Live 10/10 + mocked tests |
| Field schemas cho 4 types | PASS | Typed models + parser tests |
| Confidence mỗi field | PASS | Range/low confidence validation |
| Date validation | PASS | Unit + pipeline tests |
| Positive amount validation | PASS | Unit + pipeline tests |
| Sum mismatch > 5% | PASS | Unit + pipeline tests |
| Missing field null + 0.0 | PASS | Model/extractor tests |
| Multi-page PDF | PASS | Toàn bộ pages gửi cùng request |
| 10 sample documents | PASS | Đúng tỷ lệ 3/3/2/2 |
| Ground truth | PASS | 10 expected JSON |
| 10 actual extraction results | PASS | 10 JSON trong results/extractions/ |
| Classification đúng 10/10 live | PASS | 10/10 đúng type |
| Extraction accuracy live | PASS | 10/10 khớp tuyệt đối ground truth |
| Prompt engineering writeup | PASS | README |
| Timeline estimate | PASS | PLAN.md |
| Reusable/non-hardcoded pipeline | PASS | Live 10/10 + mocked end-to-end tests |
| GitHub repository | CHƯA XÁC MINH | Workspace không nằm trong Git repo |

## Gia cố độ bền (2026-06-14)

Sửa trong `src/utils/llm.py` để chịu được vision model yếu/không ổn định:

- `choices` rỗng/null → báo lỗi rõ ràng thay vì `'NoneType' object is not subscriptable`.
- `finish_reason == "length"` → báo "truncated" rõ ràng.
- Retry (mặc định 3, cấu hình `OPENROUTER_MAX_ATTEMPTS`) cho lỗi rỗng/cắt/JSON hỏng.
- Escalation: từ lần retry thứ 2 bỏ `response_format=json_object` — nguyên nhân khiến
  model nhỏ loop và truncate; response parse lenient qua parser fenced/plain sẵn có.

Trước khi sửa: 6/10 live. Sau khi sửa: 10/10 live. Thêm 2 unit test cho retry và
empty-choices.

## Bước còn lại trước khi nộp

1. Commit artifacts (`documents/`, `results/extractions/`) và push GitHub.

Không có extraction JSON giả được tạo khi thiếu API key; script trả exit code `1` và
thông báo cấu hình cần thiết.
