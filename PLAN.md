# AI Challenge 08 — Medical Document Extractor: Phân tích & Plan triển khai

> Đề bài: `AI_Challenge_08.md` trong thư mục pumpkin.
> Công nghệ chọn: **Python** + **OpenRouter Vision API** + **Pydantic** + **pytest**.
> Tài liệu này lưu phân tích, quyết định nghiệp vụ và kế hoạch triển khai.

---

## 1. Phân tích bài toán

### 1.1. Bản chất bài toán

Đây là bài toán **document intelligence với vision LLM** — trích xuất structured data từ medical documents (PDF/image) chưa có structure chuẩn. Độ khó nằm ở **5 trục**:

1. **Document classification** — phân loại 4 loại document (receipt, discharge_summary, lab_report, prescription) với confidence score. LLM có thể nhầm lẫn giữa các loại có layout tương tự.
2. **Field extraction với confidence** — trích xuất 6-8 fields khác nhau tùy loại document, mỗi field kèm confidence score 0-1. Challenge: LLM thường overconfident, cần kỹ thuật prompt để ra confidence thực.
3. **Validation nghiệp vụ** — kiểm tra date valid, amount positive, item totals ≈ grand_total (±5%), catch hallucinated data.
4. **Anti-hallucination** — field không có trong document → null + low confidence, **không được fabrication**. Đây là tiêu chí chấm nặng.
5. **Reusability** — pipeline hoạt động với document bất kỳ theo 4 type trên, không hardcode cho test data.

### 1.2. Phân rã yêu cầu

| Khối | Yêu cầu | Ghi chú kỹ thuật |
|---|---|---|
| **Input** | PDF hoặc image (PNG/JPG) | Support cả 2 format; PDF multi-page cần handle |
| **Classification** | 1 trong 4 loại + confidence 0-1 | Binary classification? Multi-class? |
| **Receipt fields** | hospital_name, patient_name, date, items[], grand_total, payment_method | items: {description, quantity, unit_price, total} |
| **Discharge Summary** | hospital_name, patient_name, dates, diagnosis[], procedures[], physician, instructions | primary + secondary diagnosis |
| **Lab Report** | lab_name, patient_name, date, tests[] | tests: {test_name, result, unit, reference_range, flag} |
| **Prescription** | doctor_name, patient_name, date, medications[] | medications: {name, dosage, frequency, duration, quantity} |
| **Output format** | JSON structure với nested confidence per field | `{"value": ..., "confidence": ...}` |
| **Validation** | Dates valid, amounts positive, sums match ±5% | Post-processing, không rely LLM |
| **Test data** | 10 documents (3 receipts, 3 discharge, 2 lab, 2 prescription) | Generate mock documents |

### 1.3. Quy ước nghiệp vụ — chốt trước khi implement

1. **Document classification confidence**: LLM trả về score 0-1 cho class "chính". Nếu không confident → score < 0.7, flag để review.
2. **Missing field handling**: Field không có trong document → `value: null, confidence: 0.0`. **KHÔNG fabricate**.
3. **Confidence score per field**: LLM estimate confidence based on:
   - Clarity of text in document
   - Ambiguity of field location
   - OCR quality issues
   Low confidence (< 0.5) → flag in `validation_errors`.
4. **Date validation**: Check format YYYY-MM-DD, within reasonable range (1950-2030), not future.
5. **Amount validation**: All amounts >= 0; `grand_total >= 0`; item totals sum should match grand_total within ±5%.
6. **Item quantity/price**: Should be positive numbers; `quantity * unit_price ≈ total` (±1% for rounding).
7. **Items list**: Nếu document có items nhưng LLM miss một số → count mismatch flag.
8. **Confidence aggregation**: Document-level confidence = min(field confidences) để conservative.
9. **Multi-page PDF**: Process từng page, merge results. Fields có thể span multiple pages.
10. **Low confidence threshold**: < 0.5 → warning in `validation_errors`.

### 1.4. Thiết kế LLM pipeline

**Architecture:**

```
Document (PDF/Image)
    ↓
[Preprocessing] OCR / Extract images from PDF
    ↓
[Classification LLM Call] → document_type + confidence
    ↓
[Extraction LLM Call] → Structured fields with confidence (type-specific prompt)
    ↓
[Validation Layer] → Post-process: dates, amounts, sums, confidence checks
    ↓
[Output] → JSON format spec
```

**LLM Provider: OpenRouter**

- Một OpenAI-compatible endpoint cho nhiều vision models.
- Model mặc định: `google/gemini-2.5-flash`.
- Có thể đổi model qua `OPENROUTER_MODEL` mà không sửa pipeline.
- JSON mode và base64 image input phù hợp với output schema của bài.

**Prompt Strategy:**
1. **Two-stage approach**: First classify, then extract with type-specific prompt
2. **Schema-constrained output**: JSON-only shape cho classification và từng extractor
3. **Confidence elicitation**: Explicitly ask confidence per field
4. **Negative constraints**: "If field not visible, return null with 0.0 confidence"
5. **Code validation**: Normalize date/number và kiểm tra nghiệp vụ ngoài LLM

### 1.5. Các quyết định thiết kế chính

- **Language**: Python 3.11+ — easy LLM integration, good type hints with Pydantic
- **LLM Client**: OpenAI SDK trỏ tới OpenRouter-compatible endpoint
- **PDF Processing**: `PyMuPDF` + `PIL` — không cần Poppler
- **Schema Validation**: `Pydantic` models cho từng document type + confidence wrapper
- **Test Framework**: `pytest` + fixtures
- **Confidence Scoring**: LLM tự estimate + post-processing adjustment based on field presence
- **Mock Documents**: PDF trực tiếp bằng PyMuPDF
- **Output Format**: Typed models → `model_dump_json()` để đảm bảo schema đúng

---

## 2. Kiến trúc

```
answers/challenge-08/
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py                 # ConfidenceField, ExtractionResult base
│   │   ├── receipt.py              # Receipt model
│   │   ├── discharge.py            # DischargeSummary model
│   │   ├── lab.py                  # LabReport model
│   │   └── prescription.py         # Prescription model
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── classifier.py           # DocumentClassifier
│   │   ├── receipt.py              # ReceiptExtractor
│   │   ├── discharge.py            # DischargeExtractor
│   │   ├── lab.py                  # LabExtractor
│   │   └── prescription.py         # PrescriptionExtractor
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseValidator
│   │   ├── dates.py                # DateValidator
│   │   ├── amounts.py              # AmountValidator
│   │   └── sums.py                 # SumValidator
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── preprocessor.py         # PDF → images, image handling
│   │   └── extractor.py            # Main extraction pipeline
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── classification.py       # Classification prompts
│   │   └── extraction.py           # Extraction prompts per type
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── llm.py                  # LLM client wrapper
│   │   └── image.py                # Image utilities
│   └── __init__.py
├── tests/
│   ├── fixtures/
│   │   └── documents/              # 10 test documents
│   ├── expected/                   # Expected extraction results
│   ├── test_classifiers.py
│   ├── test_extractors.py         # Per document type
│   ├── test_validators.py
│   ├── test_pipeline.py           # End-to-end
│   └── conftest.py
├── generators/
│   ├── __init__.py
│   ├── receipt.py                 # HTML → PDF generator for receipts
│   ├── discharge.py               # HTML → PDF for discharge summaries
│   ├── lab.py                     # HTML → PDF for lab reports
│   ├── prescription.py            # HTML → PDF for prescriptions
│   └── main.py                    # Generate all 10 documents
├── results/
│   └── extractions/               # JSON results for each test document
├── AI_Challenge_08.md             # Đề (copy)
├── PLAN.md                        # File này
├── CHECKLIST.md                   # Nghiệm thu
├── README.md                      # Hướng dẫn
├── pyproject.toml                 # Python dependencies
└── .env.example                   # API key template
```

---

## 3. Chiến lược test — test-first phần nào?

### 3.1. Unit Tests

1. **Classification Tests**:
   - Correct type for each document
   - Confidence scores meaningful (clear docs > 0.8, ambiguous 0.5-0.8)
   - Edge cases: blurry, partial, wrong type input

2. **Extraction Tests (per type)**:
   - All required fields present with correct structure
   - Confidence scores per field non-null
   - Missing fields return null + 0.0 confidence (not hallucinated)

3. **Validator Tests**:
   - Date validation: format, range, not future
   - Amount validation: positive, numeric
   - Sum validation: ±5% tolerance
   - Flag generation for errors

4. **Model Tests**:
   - Pydantic models serialize to correct JSON format
   - Required fields enforced
   - Confidence structure valid

### 3.2. Integration Tests

1. **End-to-end pipeline**:
   - Input document → Output JSON
   - All 10 test documents produce valid output
   - Results saved to `results/extractions/`

2. **LLM Mock Tests**:
   - Mock LLM responses to test error handling
   - Test timeout, rate limiting, API errors

### 3.3. Manual Verification Checklist

- Visual inspection of each extraction against source document
- Confidence scores make sense (low for unclear fields)
- No hallucinated data (null where absent)
- Sums match within tolerance
- All validation errors are legitimate

---

## 4. Chiến lược generate test documents

**Approach**: Structured sample data → PDF + ground-truth JSON

**Why direct PDF generation?**
- Easy to programmatically vary content
- Consistent layout per document type
- Realistic appearance (fonts, spacing, borders)
- Portable trên Windows/Linux, không cần GTK/Pango
- Ground truth được sinh từ cùng source data

**Tools**: `PyMuPDF`

**Document Templates**:

1. **Receipt (3 variations)**:
   - Standard hospital receipt
   - Detailed receipt with many line items
   - Simple receipt with minimal info

2. **Discharge Summary (3 variations)**:
   - Standard discharge with primary + secondary diagnosis
   - Complex with multiple procedures
   - Minimal info discharge

3. **Lab Report (2 variations)**:
   - Normal results (all flags = normal)
   - Abnormal results (mix of high/low flags)

4. **Prescription (2 variations)**:
   - Multiple medications
   - Single medication

**Content Generation**:
- Hospital/lab/doctor names: realistic but fictional
- Patient names: varied
- Dates: within 2024
- Amounts: realistic ranges
- Medical codes: ICD-10, CPT (realistic but fictional context)

---

## 5. Các bước triển khai & timeline ước tính

| # | Bước | Sản phẩm | Ước tính |
|---|---|---|---|
| 1 | Setup: Python project, dependencies, OpenRouter API key, basic structure | repo runnable | 30′ |
| 2 | **Pydantic models**: Define base + 4 document type models with confidence wrapper | models pass schema validation | 45′ |
| 3 | **Prompt engineering**: Classification + type-specific extraction schemas | prompts ready for testing | 60′ |
| 4 | **LLM integration**: Client wrapper, structured output calls | successful LLM calls | 30′ |
| 5 | **Classifier implementation**: Two-stage or single-shot classification | classifier works | 30′ |
| 6 | **Extractor implementation**: Per-type extractors with prompts | extractors produce valid output | 60′ |
| 7 | **Validator implementation**: Date, amount, sum validation | validators catch errors | 45′ |
| 8 | **Pipeline assembly**: Preprocessing → Classify → Extract → Validate | end-to-end working | 30′ |
| 9 | **Document generators**: PyMuPDF templates + ground truth | 10 realistic test docs | 60′ |
| 10 | **Testing**: Unit + integration tests, manual verification | all tests pass | 60′ |
| 11 | **Results generation**: Run extraction on all 10 docs, save JSON outputs | ready for submission | 30′ |
| 12 | **README + writeup**: Prompt engineering approach, setup instructions, results analysis | submission-ready docs | 30′ |

**Tổng: ~7–8.5 hours** — khớp "Advanced · 4–6 hours" với allowance cho learning/debugging LLM.

### Thứ tự quan trọng

- **Models (bước 2) trước prompts**: Schema rõ ràng giúp design prompts tốt hơn.
- **Prompts (bước 3) trước implementation**: Iterate prompts nhanh với manual test trước khi code.
- **Simple test doc trước generator**: Tạo 1-2 docs bằng tay để test pipeline, rồi mới automate.
- **Deployment không cần**: Đây là pure Python script, không có web app.

---

## 6. Prompt Engineering Approach (cho README/writeup)

### 6.1. Classification Prompt Strategy

- **System prompt**: Define task, 4 document types with characteristics
- **Output format**: JSON with `type` and `confidence`
- **Negative constraint**: "If unsure, assign lower confidence"

### 6.2. Extraction Prompt Strategy

- **Type-specific prompts**: Different prompt per document type
- **Field-by-field elicitation**: Ask for each field with confidence
- **Missing field handling**: Explicit instruction for null + 0.0
- **Formatting requirements**: Date formats, number formats

### 6.3. Confidence Elicitation

- Ask LLM to consider: text clarity, ambiguity, OCR quality
- Scale: 0.0 (missing/unclear) → 1.0 (clear and unambiguous)
- Post-processing adjustment: If field not found, force confidence to 0.0

---

## 7. Rủi ro & mitigation

| Rủi ro | Mitigation |
|---|---|
| LLM hallucinates fields | Explicit negative prompts + validation layer + manual review |
| OCR fails on poor quality | Preprocessing: contrast enhancement, deskewing |
| API rate limits | Caching, batch processing, retry logic |
| Cost overruns | Use Haiku (cheaper), cache results, limit test runs |
| Confidence scores unreliable | Post-processing heuristics, manual verification set |

---

## 8. Submission checklist

- [x] GitHub repository với code
- [ ] 10 test documents
- [ ] Extraction results JSON
- [ ] README với prompt engineering writeup
- [ ] Tests pass
- [ ] No hardcoded test data assumptions

> Plan này được thiết kế để implement theo test-first approach với Pydantic models và LLM integration.
> Key success factors: prompt quality, anti-hallucination, và validation robust.
