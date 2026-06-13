"""Extraction prompts for each document type."""

# Base system prompt for all extractions
BASE_EXTRACTION_SYSTEM_PROMPT = """You are a medical document data extraction expert. Your task is to accurately extract structured information from medical documents.

CRITICAL RULES:
1. Extract ONLY information that is clearly visible in the document
2. If a field is not found or cannot be read, set value to null and confidence to 0.0
3. DO NOT fabricate or guess any values - this is critical for patient safety
4. Assign confidence scores based on:
   - 0.9-1.0: Clear, unambiguous text in expected location
   - 0.7-0.9: Visible but minor ambiguity (slight blur, unusual formatting)
   - 0.5-0.7: Partially readable or somewhat uncertain
   - 0.3-0.5: Difficult to read, low confidence extraction
   - 0.0-0.3: Not found or highly uncertain
5. For numeric values, extract exactly as shown (preserve decimals)
6. For dates, use YYYY-MM-DD format if possible, otherwise as shown
7. Return ONLY valid JSON, no markdown blocks, no explanations"""

# Receipt extraction prompt
RECEIPT_EXTRACTION_PROMPT = """Extract all fields from this hospital receipt/invoice.

Extract the following fields:
- hospital_name: Name of hospital/medical facility
- patient_name: Patient's full name
- date: Document date (YYYY-MM-DD format if clear)
- items: List of line items, each with:
  - description: Service/item description
  - quantity: Number of units (integer)
  - unit_price: Price per unit (float)
  - total: Line item total (float)
- grand_total: Total amount due (float)
- payment_method: How payment was made (cash, card, insurance, etc.)

For each field, assign a confidence score 0.0-1.0.

Return EXACTLY this JSON structure:
{
  "hospital_name": {"value": "extracted or null", "confidence": 0.0-1.0},
  "patient_name": {"value": "extracted or null", "confidence": 0.0-1.0},
  "date": {"value": "YYYY-MM-DD or null", "confidence": 0.0-1.0},
  "items": {"value": [{"description": "...", "quantity": 0, "unit_price": 0.0, "total": 0.0}], "confidence": 0.0-1.0},
  "grand_total": {"value": 0.0 or null, "confidence": 0.0-1.0},
  "payment_method": {"value": "extracted or null", "confidence": 0.0-1.0}
}

Remember: If any field is not visible, use null with confidence 0.0 - DO NOT fabricate."""

# Discharge summary extraction prompt
DISCHARGE_EXTRACTION_PROMPT = """Extract all fields from this discharge summary.

Extract the following fields:
- hospital_name: Name of hospital/medical facility
- patient_name: Patient's full name
- admission_date: Date of admission (YYYY-MM-DD)
- discharge_date: Date of discharge (YYYY-MM-DD)
- diagnosis: Object with:
  - primary: Primary diagnosis (main reason for admission)
  - secondary: Array of secondary diagnoses (comorbidities, complications)
- procedures_performed: List of procedures, each with:
  - code: Procedure code if shown (CPT, ICD, etc.) or null
  - name: Procedure description
  - date: Date of procedure (YYYY-MM-DD) or null
- attending_physician: Name of attending/primary physician
- discharge_instructions: Patient instructions for home care

For each field, assign a confidence score 0.0-1.0.

Return EXACTLY this JSON structure:
{
  "hospital_name": {"value": "extracted or null", "confidence": 0.0-1.0},
  "patient_name": {"value": "extracted or null", "confidence": 0.0-1.0},
  "admission_date": {"value": "YYYY-MM-DD or null", "confidence": 0.0-1.0},
  "discharge_date": {"value": "YYYY-MM-DD or null", "confidence": 0.0-1.0},
  "diagnosis": {"value": {"primary": "... or null", "secondary": ["...", "..."]}, "confidence": 0.0-1.0},
  "procedures_performed": {"value": [{"code": "..." or null, "name": "...", "date": "YYYY-MM-DD" or null}], "confidence": 0.0-1.0},
  "attending_physician": {"value": "extracted or null", "confidence": 0.0-1.0},
  "discharge_instructions": {"value": "extracted or null", "confidence": 0.0-1.0}
}

Remember: If any field is not visible, use null with confidence 0.0 - DO NOT fabricate."""

# Lab report extraction prompt
LAB_EXTRACTION_PROMPT = """Extract all fields from this laboratory report.

Extract the following fields:
- lab_name: Name of laboratory or testing facility
- patient_name: Patient's full name
- date: Report date (YYYY-MM-DD)
- tests: List of test results, each with:
  - test_name: Name of the test
  - result: The test result value (preserve units in result if shown)
  - unit: Unit of measurement (mg/dL, etc.) or null
  - reference_range: Normal range shown or null
  - flag: One of "normal", "high", or "low" (based on indicator in document)

For each field, assign a confidence score 0.0-1.0.

Return EXACTLY this JSON structure:
{
  "lab_name": {"value": "extracted or null", "confidence": 0.0-1.0},
  "patient_name": {"value": "extracted or null", "confidence": 0.0-1.0},
  "date": {"value": "YYYY-MM-DD or null", "confidence": 0.0-1.0},
  "tests": {"value": [{"test_name": "...", "result": "...", "unit": "..." or null, "reference_range": "..." or null, "flag": "normal|high|low"}], "confidence": 0.0-1.0}
}

Remember: If any field is not visible, use null with confidence 0.0 - DO NOT fabricate."""

# Prescription extraction prompt
PRESCRIPTION_EXTRACTION_PROMPT = """Extract all fields from this medical prescription.

Extract the following fields:
- doctor_name: Prescribing physician's name
- patient_name: Patient's full name
- date: Prescription date (YYYY-MM-DD)
- medications: List of prescribed medications, each with:
  - name: Medication name (brand or generic)
  - dosage: Dosage strength (e.g., "500mg", "10mg/mL") or null
  - frequency: How often to take (e.g., "twice daily", "every 8 hours") or null
  - duration: How long to take (e.g., "7 days", "2 weeks") or null
  - quantity: Total quantity dispensed (integer) or null

For each field, assign a confidence score 0.0-1.0.

Return EXACTLY this JSON structure:
{
  "doctor_name": {"value": "extracted or null", "confidence": 0.0-1.0},
  "patient_name": {"value": "extracted or null", "confidence": 0.0-1.0},
  "date": {"value": "YYYY-MM-DD or null", "confidence": 0.0-1.0},
  "medications": {"value": [{"name": "...", "dosage": "..." or null, "frequency": "..." or null, "duration": "..." or null, "quantity": 0 or null}], "confidence": 0.0-1.0}
}

Remember: If any field is not visible, use null with confidence 0.0 - DO NOT fabricate."""


def get_extraction_prompt(document_type: str) -> str:
    """Get extraction prompt for document type."""
    prompts = {
        "receipt": RECEIPT_EXTRACTION_PROMPT,
        "discharge_summary": DISCHARGE_EXTRACTION_PROMPT,
        "lab_report": LAB_EXTRACTION_PROMPT,
        "prescription": PRESCRIPTION_EXTRACTION_PROMPT,
    }
    return prompts.get(document_type, "")
