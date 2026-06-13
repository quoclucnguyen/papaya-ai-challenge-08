"""Receipt generator - HTML template to PDF."""



def generate_receipt_html(
    hospital_name: str,
    patient_name: str,
    date: str,
    items: list[dict],
    grand_total: float,
    payment_method: str,
    receipt_number: str,
) -> str:
    """Generate HTML for a hospital receipt."""
    items_html = ""
    for item in items:
        items_html += f"""
        <tr>
            <td>{item['description']}</td>
            <td style="text-align: center;">{item['quantity']}</td>
            <td style="text-align: right;">${item['unit_price']:.2f}</td>
            <td style="text-align: right;">${item['total']:.2f}</td>
        </tr>
        """

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
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #333;
            padding-bottom: 20px;
            margin-bottom: 20px;
        }}
        .hospital-name {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .receipt-title {{
            font-size: 18px;
            color: #666;
        }}
        .info-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th {{
            background-color: #f5f5f5;
            padding: 10px;
            text-align: left;
            border-bottom: 2px solid #333;
        }}
        th:last-child, td:last-child {{
            text-align: right;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        .total-row {{
            font-weight: bold;
            font-size: 16px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="hospital-name">{hospital_name}</div>
        <div class="receipt-title">HOSPITAL RECEIPT / INVOICE</div>
    </div>

    <div class="info-row">
        <span><strong>Receipt No:</strong> {receipt_number}</span>
        <span><strong>Date:</strong> {date}</span>
    </div>
    <div class="info-row">
        <span><strong>Patient:</strong> {patient_name}</span>
        <span><strong>Payment:</strong> {payment_method}</span>
    </div>

    <table>
        <thead>
            <tr>
                <th>Description</th>
                <th style="text-align: center;">Qty</th>
                <th style="text-align: right;">Unit Price</th>
                <th style="text-align: right;">Total</th>
            </tr>
        </thead>
        <tbody>
            {items_html}
            <tr class="total-row">
                <td colspan="3" style="text-align: right;">GRAND TOTAL</td>
                <td style="text-align: right;">${grand_total:.2f}</td>
            </tr>
        </tbody>
    </table>

    <div class="footer">
        <p>Thank you for your payment.</p>
        <p>This document serves as official receipt.</p>
    </div>
</body>
</html>
    """
    return html


# Sample receipt data for testing
SAMPLE_RECEIPTS = [
    {
        "hospital_name": "Bangkok Hospital",
        "patient_name": "Somchai Wong",
        "date": "2024-03-15",
        "items": [
            {"description": "Emergency Room Visit", "quantity": 1, "unit_price": 2500.00, "total": 2500.00},
            {"description": "X-Ray - Chest", "quantity": 1, "unit_price": 1200.00, "total": 1200.00},
            {"description": "Blood Test - CBC", "quantity": 1, "unit_price": 800.00, "total": 800.00},
            {"description": "Medication - Antibiotics", "quantity": 1, "unit_price": 450.00, "total": 450.00},
            {"description": "Doctor Consultation", "quantity": 1, "unit_price": 1500.00, "total": 1500.00},
        ],
        "grand_total": 6450.00,
        "payment_method": "Credit Card",
        "receipt_number": "RCP-2024-00342",
    },
    {
        "hospital_name": "Bumrungrad International Hospital",
        "patient_name": "John Smith",
        "date": "2024-05-22",
        "items": [
            {"description": "Room & Board - Private (3 nights)", "quantity": 3, "unit_price": 8500.00, "total": 25500.00},
            {"description": "Surgery - Appendectomy", "quantity": 1, "unit_price": 45000.00, "total": 45000.00},
            {"description": "Anesthesia", "quantity": 1, "unit_price": 8000.00, "total": 8000.00},
            {"description": "Nursing Care", "quantity": 3, "unit_price": 2000.00, "total": 6000.00},
            {"description": "Medications", "quantity": 1, "unit_price": 3500.00, "total": 3500.00},
        ],
        "grand_total": 88000.00,
        "payment_method": "Insurance - Thai PA",
        "receipt_number": "INV-2024-11891",
    },
    {
        "hospital_name": "Siriraj Hospital",
        "patient_name": "Somchai Jaidee",
        "date": "2024-08-10",
        "items": [
            {"description": "Outpatient Consultation", "quantity": 1, "unit_price": 500.00, "total": 500.00},
            {"description": "Ultrasound - Abdomen", "quantity": 1, "unit_price": 1800.00, "total": 1800.00},
            {"description": "Urinalysis", "quantity": 1, "unit_price": 250.00, "total": 250.00},
        ],
        "grand_total": 2550.00,
        "payment_method": "Cash",
        "receipt_number": "OP-2024-45221",
    },
]
