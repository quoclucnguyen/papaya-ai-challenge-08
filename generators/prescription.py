"""Prescription generator - HTML template to PDF."""



def generate_prescription_html(
    doctor_name: str,
    patient_name: str,
    date: str,
    medications: list[dict],
    patient_id: str,
    clinic_name: str,
) -> str:
    """Generate HTML for a medical prescription."""
    meds_html = ""
    for i, med in enumerate(medications, 1):
        med_html = f"""
        <div class="medication">
            <div class="med-number">{i}.</div>
            <div class="med-details">
                <div class="med-name"><strong>{med['name']}</strong></div>
                <div class="med-info">
                    <span>Sig: {med.get('dosage', 'N/A')}</span>
                    {f" - {med.get('frequency', 'N/A')}" if med.get('frequency') else ""}
                </div>
                <div class="med-info">
                    <span>Duration: {med.get('duration', 'N/A')}</span>
                    {f" | Qty: {med.get('quantity', 'N/A')}" if med.get('quantity') else ""}
                </div>
            </div>
        </div>
        """
        meds_html += med_html

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 700px;
            margin: 0 auto;
            padding: 30px;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .paper {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #667eea;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }}
        .clinic-name {{
            font-size: 22px;
            font-weight: bold;
            color: #5a67d8;
            margin-bottom: 5px;
        }}
        .doc-title {{
            font-size: 16px;
            color: #718096;
        }}
        .patient-info {{
            background-color: #f7fafc;
            padding: 15px;
            border-left: 4px solid #667eea;
            margin-bottom: 20px;
        }}
        .info-row {{
            margin: 5px 0;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: bold;
            color: #2d3748;
            margin: 20px 0 10px 0;
            padding-bottom: 5px;
            border-bottom: 1px solid #e2e8f0;
        }}
        .medication {{
            display: flex;
            margin-bottom: 20px;
        }}
        .med-number {{
            font-size: 18px;
            font-weight: bold;
            color: #667eea;
            margin-right: 15px;
            min-width: 30px;
        }}
        .med-details {{
            flex: 1;
        }}
        .med-name {{
            font-size: 16px;
            margin-bottom: 5px;
        }}
        .med-info {{
            color: #4a5568;
            margin: 3px 0;
        }}
        .rx-symbol {{
            text-align: right;
            font-size: 48px;
            color: #5a67d8;
            margin-top: 10px;
            font-family: 'Times New Roman', serif;
            font-style: italic;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #e2e8f0;
            text-align: center;
        }}
        .signature {{
            text-align: right;
            margin-top: 40px;
            padding-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="paper">
        <div class="header">
            <div class="clinic-name">{clinic_name}</div>
            <div class="doc-title">MEDICAL PRESCRIPTION</div>
        </div>

        <div class="patient-info">
            <div class="info-row"><strong>Patient:</strong> {patient_name}</div>
            <div class="info-row"><strong>Patient ID:</strong> {patient_id}</div>
            <div class="info-row"><strong>Date:</strong> {date}</div>
            <div class="info-row"><strong>Prescribing Physician:</strong> {doctor_name}</div>
        </div>

        <div class="rx-symbol">℞</div>

        <div class="section-title">MEDICATIONS</div>
        {meds_html}

        <div class="footer">
            <p><em>Please take medications as prescribed.</em></p>
            <p><em>Complete the full course even if symptoms improve.</em></p>
        </div>

        <div class="signature">
            <div style="margin-bottom: 50px;"></div>
            <div style="border-top: 1px solid #333; display: inline-block; padding-top: 5px; min-width: 200px; text-align: center;">
                <strong>{doctor_name}</strong>, MD
            </div>
        </div>
    </div>
</body>
</html>
    """
    return html


# Sample prescriptions
SAMPLE_PRESCRIPTIONS = [
    {
        "doctor_name": "Dr. Suchart Kanok",
        "patient_name": "Malee S.",
        "date": "2024-05-18",
        "patient_id": "PT-2024-38921",
        "clinic_name": "Bangkok Medical Clinic",
        "medications": [
            {
                "name": "Amoxicillin 500mg",
                "dosage": "500mg",
                "frequency": "Every 8 hours",
                "duration": "7 days",
                "quantity": 21
            },
            {
                "name": "Ibuprofen 400mg",
                "dosage": "400mg",
                "frequency": "Every 6-8 hours as needed for pain",
                "duration": "5 days",
                "quantity": 20
            },
            {
                "name": "Omeprazole 20mg",
                "dosage": "20mg",
                "frequency": "Once daily before breakfast",
                "duration": "14 days",
                "quantity": 14
            },
        ]
    },
    {
        "doctor_name": "Dr. Kanjana Suk",
        "patient_name": "Chati Trakun",
        "date": "2024-08-30",
        "patient_id": "PT-2024-52110",
        "clinic_name": "Phatthanakan Clinic",
        "medications": [
            {
                "name": "Metformin 500mg",
                "dosage": "500mg",
                "frequency": "Twice daily with meals",
                "duration": "30 days",
                "quantity": 60
            },
            {
                "name": "Losartan 50mg",
                "dosage": "50mg",
                "frequency": "Once daily in the morning",
                "duration": "30 days",
                "quantity": 30
            },
            {
                "name": "Atorvastatin 20mg",
                "dosage": "20mg",
                "frequency": "Once daily at bedtime",
                "duration": "30 days",
                "quantity": 30
            },
            {
                "name": "Aspirin 81mg",
                "dosage": "81mg",
                "frequency": "Once daily",
                "duration": "30 days",
                "quantity": 30
            },
        ]
    },
]
