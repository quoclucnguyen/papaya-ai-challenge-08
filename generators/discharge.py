"""Discharge summary generator - HTML template to PDF."""



def generate_discharge_html(
    hospital_name: str,
    patient_name: str,
    admission_date: str,
    discharge_date: str,
    diagnosis: dict,
    procedures: list,
    attending_physician: str,
    discharge_instructions: str,
    patient_id: str,
) -> str:
    """Generate HTML for a discharge summary."""
    diagnosis_html = f"""
    <tr>
        <td><strong>Primary Diagnosis:</strong></td>
        <td>{diagnosis.get('primary', 'N/A')}</td>
    </tr>
    """

    if diagnosis.get('secondary'):
        for i, sec in enumerate(diagnosis['secondary'], 1):
            diagnosis_html += f"""
    <tr>
        <td><strong>Secondary Diagnosis {i}:</strong></td>
        <td>{sec}</td>
    </tr>
    """

    procedures_html = ""
    for proc in procedures:
        date_str = proc.get('date', 'N/A')
        code_str = proc.get('code', '')
        code_display = f" ({code_str})" if code_str else ""
        procedures_html += f"<li>{proc['name']}{code_display} - {date_str}</li>"

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
            line-height: 1.6;
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #2c5282;
            padding-bottom: 20px;
            margin-bottom: 20px;
        }}
        .hospital-name {{
            font-size: 26px;
            font-weight: bold;
            color: #2c5282;
            margin-bottom: 10px;
        }}
        .doc-title {{
            font-size: 20px;
            color: #4a5568;
            margin-bottom: 5px;
        }}
        .patient-info {{
            background-color: #f7fafc;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .section {{
            margin-bottom: 25px;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: bold;
            color: #2d3748;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 5px;
            margin-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        td {{
            padding: 8px;
            border-bottom: 1px solid #e2e8f0;
        }}
        td:first-child {{
            width: 40%;
            font-weight: 500;
        }}
        ul {{
            margin: 5px 0;
            padding-left: 20px;
        }}
        .instructions {{
            background-color: #fffaf0;
            border-left: 4px solid #ed8936;
            padding: 15px;
            margin-top: 20px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e2e8f0;
            text-align: right;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="hospital-name">{hospital_name}</div>
        <div class="doc-title">DISCHARGE SUMMARY</div>
    </div>

    <div class="patient-info">
        <table>
            <tr>
                <td><strong>Patient Name:</strong></td>
                <td>{patient_name}</td>
                <td><strong>Patient ID:</strong></td>
                <td>{patient_id}</td>
            </tr>
            <tr>
                <td><strong>Admission Date:</strong></td>
                <td>{admission_date}</td>
                <td><strong>Discharge Date:</strong></td>
                <td>{discharge_date}</td>
            </tr>
            <tr>
                <td><strong>Attending Physician:</strong></td>
                <td colspan="3">{attending_physician}</td>
            </tr>
        </table>
    </div>

    <div class="section">
        <div class="section-title">DIAGNOSIS</div>
        <table>
            {diagnosis_html}
        </table>
    </div>

    <div class="section">
        <div class="section-title">PROCEDURES PERFORMED</div>
        <ul>{procedures_html}</ul>
    </div>

    <div class="instructions">
        <div class="section-title">DISCHARGE INSTRUCTIONS</div>
        <p>{discharge_instructions}</p>
    </div>

    <div class="footer">
        <p><strong>{attending_physician}</strong></p>
        <p>Attending Physician</p>
        <p><em>This document serves as medical record. Follow all instructions carefully.</em></p>
    </div>
</body>
</html>
    """
    return html


# Sample discharge summaries
SAMPLE_DISCHARGES = [
    {
        "hospital_name": "Bangkok Hospital",
        "patient_name": "Suphanat Wong",
        "admission_date": "2024-06-01",
        "discharge_date": "2024-06-05",
        "diagnosis": {
            "primary": "Community-acquired pneumonia (J18.9)",
            "secondary": ["Hypertension (I10)", "Type 2 Diabetes Mellitus (E11.9)"]
        },
        "procedures": [
            {"name": "Chest X-Ray", "code": "X001", "date": "2024-06-01"},
            {"name": "CBC with Differential", "code": "LAB02", "date": "2024-06-01"},
            {"name": "IV Antibiotics Administration", "code": "N123", "date": "2024-06-01"},
            {"name": "Oxygen Therapy", "code": "N045", "date": "2024-06-01"},
        ],
        "attending_physician": "Dr. Narumon Sookprasert",
        "discharge_instructions": "Complete 7-day course of Azithromycin. Rest at home for 3-5 days. Follow up in outpatient clinic in 1 week. Monitor temperature twice daily. Return if fever > 38.5°C or breathing difficulty worsens. Continue home blood pressure and blood sugar monitoring.",
        "patient_id": "PT-2024-45212",
    },
    {
        "hospital_name": "Bumrungrad International Hospital",
        "patient_name": "Jane Doe",
        "admission_date": "2024-07-10",
        "discharge_date": "2024-07-15",
        "diagnosis": {
            "primary": "Acute appendicitis (K35.8)",
            "secondary": ["Peritonitis (K65.9)"]
        },
        "procedures": [
            {"name": "Laparoscopic Appendectomy", "code": "CPT-44950", "date": "2024-07-10"},
            {"name": "Pre-op CBC & Metabolic Panel", "code": "LAB-800", "date": "2024-07-10"},
            {"name": "Anesthesia - General", "code": "CPT-00540", "date": "2024-07-10"},
            {"name": "Post-operative Pain Management", "code": "N-099", "date": "2024-07-10"},
        ],
        "attending_physician": "Dr. Peter Chen",
        "discharge_instructions": "Wound care: Keep incision dry for 48 hours. No driving for 1 week. No heavy lifting > 10 lbs for 2 weeks. Diet: Advance as tolerated, low fat initially. Medications: Take prescribed pain meds as needed. Follow up in clinic in 7 days to check wound. Return to ER if fever > 38°C, severe abdominal pain, or redness/swelling at wound site.",
        "patient_id": "PT-2024-55891",
    },
    {
        "hospital_name": "Siriraj Hospital",
        "patient_name": "Malee Raks",
        "admission_date": "2024-09-20",
        "discharge_date": "2024-09-23",
        "diagnosis": {
            "primary": "Acute myocardial infarction (I21.9)",
            "secondary": ["Hyperlipidemia (E78.5)"]
        },
        "procedures": [
            {"name": "Cardiac Catheterization", "code": "CPT-93458", "date": "2024-09-20"},
            {"name": "PCI with Stent Placement", "code": "CPT-92928", "date": "2024-09-20"},
            {"name": "Echocardiogram", "code": "CPT-93306", "date": "2024-09-21"},
        ],
        "attending_physician": "Dr. Suda Rattana",
        "discharge_instructions": "Take dual antiplatelet therapy (Aspirin + Clopidogrel) for at least 12 months. Do NOT stop medications without consulting cardiologist. Low salt, low fat diet. No smoking. Cardiac rehabilitation recommended. Follow up with cardiologist in 2 weeks. Call emergency if chest pain returns, shortness of breath, or excessive bleeding.",
        "patient_id": "PT-2024-60452",
    },
]
