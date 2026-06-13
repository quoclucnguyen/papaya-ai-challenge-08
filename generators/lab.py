"""Lab report generator - HTML template to PDF."""



def generate_lab_html(
    lab_name: str,
    patient_name: str,
    date: str,
    tests: list[dict],
    patient_id: str,
    doctor: str,
) -> str:
    """Generate HTML for a lab report."""
    tests_html = ""
    for test in tests:
        flag_color = "#2f855a"  # green for normal
        flag_text = "NORMAL"
        if test.get("flag") == "high":
            flag_color = "#c53030"  # red for high
            flag_text = "HIGH"
        elif test.get("flag") == "low":
            flag_color = "#dd6b20"  # orange for low
            flag_text = "LOW"

        tests_html += f"""
        <tr>
            <td>{test['test_name']}</td>
            <td style="text-align: center;">{test['result']}</td>
            <td style="text-align: center;">{test.get('unit', '-')}</td>
            <td style="text-align: center;">{test.get('reference_range', '-')}</td>
            <td style="text-align: center; color: {flag_color}; font-weight: bold;">{flag_text}</td>
        </tr>
        """

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Courier New', monospace;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
            line-height: 1.4;
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #1a365d;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }}
        .lab-name {{
            font-size: 28px;
            font-weight: bold;
            color: #1a365d;
            margin-bottom: 5px;
        }}
        .doc-title {{
            font-size: 18px;
            color: #4a5568;
        }}
        .patient-info {{
            background-color: #ebf8ff;
            padding: 15px;
            border: 1px solid #bee3f8;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th {{
            background-color: #2c5282;
            color: white;
            padding: 10px;
            text-align: left;
        }}
        th:nth-child(2), th:nth-child(3), th:nth-child(4), th:nth-child(5) {{
            text-align: center;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #e2e8f0;
        }}
        td:nth-child(2), td:nth-child(3), td:nth-child(4), td:nth-child(5) {{
            text-align: center;
        }}
        tr:nth-child(even) {{
            background-color: #f7fafc;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 15px;
            border-top: 2px solid #e2e8f0;
            text-align: right;
        }}
        .flag {{
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="lab-name">{lab_name}</div>
        <div class="doc-title">LABORATORY REPORT</div>
    </div>

    <div class="patient-info">
        <table style="margin: 0; background: transparent;">
            <tr>
                <td><strong>Patient Name:</strong> {patient_name}</td>
                <td><strong>Patient ID:</strong> {patient_id}</td>
            </tr>
            <tr>
                <td><strong>Report Date:</strong> {date}</td>
                <td><strong>Ordering Physician:</strong> {doctor}</td>
            </tr>
        </table>
    </div>

    <table>
        <thead>
            <tr>
                <th>Test Name</th>
                <th>Result</th>
                <th>Unit</th>
                <th>Reference Range</th>
                <th>Flag</th>
            </tr>
        </thead>
        <tbody>
            {tests_html}
        </tbody>
    </table>

    <div class="footer">
        <p><em>This report is for medical professional use only.</em></p>
        <p>Report generated: {date} | {lab_name}</p>
    </div>
</body>
</html>
    """
    return html


# Sample lab reports
SAMPLE_LABS = [
    {
        "lab_name": "Bangkok Hospital Laboratory",
        "patient_name": "Nattapon Wong",
        "date": "2024-04-15",
        "patient_id": "PT-2024-33421",
        "doctor": "Dr. Sombat T.",
        "tests": [
            {"test_name": "White Blood Cell Count", "result": "12.5", "unit": "x10^3/uL", "reference_range": "4.5-11.0", "flag": "high"},
            {"test_name": "Hemoglobin", "result": "14.2", "unit": "g/dL", "reference_range": "13.5-17.5", "flag": "normal"},
            {"test_name": "Hematocrit", "result": "42.1", "unit": "%", "reference_range": "38.8-50.0", "flag": "normal"},
            {"test_name": "Platelet Count", "result": "245", "unit": "x10^3/uL", "reference_range": "150-400", "flag": "normal"},
            {"test_name": "Neutrophils %", "result": "78", "unit": "%", "reference_range": "40-74", "flag": "high"},
            {"test_name": "Lymphocytes %", "result": "18", "unit": "%", "reference_range": "20-50", "flag": "low"},
            {"test_name": "Red Blood Cell Count", "result": "4.9", "unit": "x10^6/uL", "reference_range": "4.3-5.9", "flag": "normal"},
        ]
    },
    {
        "lab_name": "MedAsia Laboratory",
        "patient_name": "Suda Meesuk",
        "date": "2024-07-22",
        "patient_id": "PT-2024-47891",
        "doctor": "Dr. Apichart K.",
        "tests": [
            {"test_name": "Fasting Blood Glucose", "result": "142", "unit": "mg/dL", "reference_range": "70-100", "flag": "high"},
            {"test_name": "HbA1c", "result": "7.8", "unit": "%", "reference_range": "4.0-5.6", "flag": "high"},
            {"test_name": "Total Cholesterol", "result": "268", "unit": "mg/dL", "reference_range": "<200", "flag": "high"},
            {"test_name": "HDL Cholesterol", "result": "38", "unit": "mg/dL", "reference_range": ">40", "flag": "low"},
            {"test_name": "LDL Cholesterol", "result": "189", "unit": "mg/dL", "reference_range": "<130", "flag": "high"},
            {"test_name": "Triglycerides", "result": "205", "unit": "mg/dL", "reference_range": "<150", "flag": "high"},
            {"test_name": "Creatinine", "result": "0.9", "unit": "mg/dL", "reference_range": "0.6-1.2", "flag": "normal"},
        ]
    },
]
