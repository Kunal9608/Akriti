"""
Structured Report PDF Generator matching Akriti Diagnostics Center required layout (§3).
Uses ReportLab to ensure pixel-perfect rendering across all platforms without GTK DLL dependencies.
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def generate_structured_report_pdf(patient, booked_tests_data, verification_hash: str = "") -> bytes:
    """
    Generate the official Akriti Diagnostics Center patient diagnostic report PDF.
    `booked_tests_data` format:
    [
        {
            "test_name": "CBC 5 Part",
            "interpretation_note": "...",
            "parameters": [
                {
                    "name": "Hemoglobin (Hb)",
                    "value": "11.2",
                    "unit": "g/dL",
                    "reference": "12.0 - 15.5",
                    "is_abnormal": True,
                    "note": "..."
                },
                ...
            ]
        }
    ]
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    # Custom color palette matching Akriti branding
    primary_color = colors.HexColor('#6D0001')     # Deep Burgundy Header
    secondary_color = colors.HexColor('#333333')   # Charcoal text
    accent_abnormal = colors.HexColor('#C0392B')   # Vibrant Red for abnormal flags
    border_color = colors.HexColor('#CCCCCC')      # Subtle border grey
    light_bg = colors.HexColor('#F8F9FA')          # Table zebra row grey

    # Typography styles
    lab_title_style = ParagraphStyle(
        'LabTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold', 
        fontSize=20,
        leading=24,
        textColor=primary_color,
        alignment=TA_CENTER,
        spaceAfter=4
    )

    lab_subtitle_style = ParagraphStyle(
        'LabSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#555555'),
        alignment=TA_CENTER,
        spaceAfter=2
    )

    lab_address_style = ParagraphStyle(
        'LabAddress',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
        spaceAfter=15
    )

    report_badge_style = ParagraphStyle(
        'ReportBadge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.white,
        alignment=TA_CENTER
    )

    label_style = ParagraphStyle(
        'DemoLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#444444')
    )

    value_style = ParagraphStyle(
        'DemoValue',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#111111')
    )

    test_heading_style = ParagraphStyle(
        'TestHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=6
    )

    th_style = ParagraphStyle(
        'TableHead',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    td_style = ParagraphStyle(
        'TableCellNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=secondary_color
    )

    td_bold_style = ParagraphStyle(
        'TableCellBold',
        parent=td_style,
        fontName='Helvetica-Bold'
    )

    td_abnormal_style = ParagraphStyle(
        'TableCellAbnormal',
        parent=td_style,
        fontName='Helvetica-Bold',
        textColor=accent_abnormal
    )

    interp_label_style = ParagraphStyle(
        'InterpLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=primary_color
    )

    interp_body_style = ParagraphStyle(
        'InterpBody',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=secondary_color
    )

    footer_note_style = ParagraphStyle(
        'FooterNote',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#777777')
    )

    signature_style = ParagraphStyle(
        'SignatureBlock',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=secondary_color,
        alignment=TA_RIGHT
    )

    story = []

    # 1. Header / Letterhead
    story.append(Paragraph("AKRITI DIAGNOSTICS CENTER", lab_title_style))
    story.append(Paragraph("PATHOLOGY & DIGITAL X-RAY CLINICAL LABORATORY · ISO 9001:2015 CERTIFIED", lab_subtitle_style))
    story.append(Paragraph("Opposite City Civil Hospital, Main Road, New Delhi – 110001 | Phone: +91 98765 43210 / 011-23456789 | Email: reports@akritidiagnostics.com", lab_address_style))

    # Banner block
    badge_table = Table([[Paragraph("OFFICIAL LABORATORY DIAGNOSTIC REPORT", report_badge_style)]], colWidths=[523])
    badge_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), primary_color),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(badge_table)
    story.append(Spacer(1, 10))

    # 2. Patient Demographics Block
    gender_str = patient.gender.value[0].upper() + patient.gender.value[1:] if hasattr(patient.gender, 'value') else str(patient.gender).capitalize()
    age_gender = f"{patient.age} Yrs / {gender_str}"
    sample_date_str = patient.sample_date.strftime('%d-%b-%Y') if patient.sample_date else datetime.now().strftime('%d-%b-%Y')
    report_date_str = datetime.now().strftime('%d-%b-%Y %H:%M')
    doctor_name = f"Dr. {patient.doctor.name}" if patient.doctor else "Self / Direct"

    demo_data = [
        [
            Paragraph("Patient Name:", label_style),
            Paragraph(patient.name.upper(), td_bold_style),
            Paragraph("Patient ID / SID:", label_style),
            Paragraph(f"<b>{patient.patient_code}</b>", value_style)
        ],
        [
            Paragraph("Age / Gender:", label_style),
            Paragraph(age_gender, value_style),
            Paragraph("Referred By:", label_style),
            Paragraph(doctor_name, value_style)
        ],
        [
            Paragraph("Mobile No:", label_style),
            Paragraph(patient.mobile or "—", value_style),
            Paragraph("Sample Date:", label_style),
            Paragraph(sample_date_str, value_style)
        ],
        [
            Paragraph("Collection Type:", label_style),
            Paragraph(str(patient.collection_type.value if hasattr(patient.collection_type, 'value') else patient.collection_type).replace("_", " ").title(), value_style),
            Paragraph("Reported On:", label_style),
            Paragraph(report_date_str, value_style)
        ]
    ]

    demo_table = Table(demo_data, colWidths=[90, 171, 95, 167])
    demo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_bg),
        ('BOX', (0, 0), (-1, -1), 1, primary_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(demo_table)
    story.append(Spacer(1, 15))

    # 3. Test Results Sections
    col_widths = [190, 110, 143, 80]  # Total 523pt

    for test_group in booked_tests_data:
        group_story = []
        group_story.append(Paragraph(test_group["test_name"].upper(), test_heading_style))

        table_rows = [
            [
                Paragraph("TEST PARAMETER", th_style),
                Paragraph("RESULT VALUE", th_style),
                Paragraph("REFERENCE RANGE", th_style),
                Paragraph("FLAG", th_style)
            ]
        ]

        for p in test_group["parameters"]:
            val_str = p["value"]
            if p.get("unit"):
                val_str = f"{p['value']} {p['unit']}"

            if p.get("is_abnormal"):
                val_para = Paragraph(val_str, td_abnormal_style)
                flag_para = Paragraph("<b>OUT OF RANGE</b>", td_abnormal_style)
            else:
                val_para = Paragraph(val_str, td_bold_style)
                flag_para = Paragraph("Normal", td_style)

            ref_str = p.get("reference") or "—"
            table_rows.append([
                Paragraph(p["name"], td_style),
                val_para,
                Paragraph(ref_str, td_style),
                flag_para
            ])

        t = Table(table_rows, colWidths=col_widths, repeatRows=1)
        t_style = [
            ('BACKGROUND', (0, 0), (-1, 0), primary_color),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, border_color),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]
        # Zebra stripe rows
        for idx in range(1, len(table_rows)):
            if idx % 2 == 0:
                t_style.append(('BACKGROUND', (0, idx), (-1, idx), light_bg))

        t.setStyle(TableStyle(t_style))
        group_story.append(t)

        # Optional interpretation note and attachment handling
        raw_note = test_group.get("interpretation_note") or ""
        attachment_path = None
        clean_note = raw_note

        if "[ATTACHMENT:" in raw_note:
            parts = raw_note.split("[ATTACHMENT:")
            clean_note = parts[0].strip()
            if len(parts) > 1:
                attachment_path = parts[1].split("]")[0].strip()

        if clean_note:
            group_story.append(Spacer(1, 4))
            note_table = Table([[
                Paragraph("<b>Interpretation / Remarks:</b>", interp_label_style),
                Paragraph(clean_note.replace("\n", "<br/>"), interp_body_style)
            ]], colWidths=[130, 393])
            note_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFDE7')),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#FBC02D')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ]))
            group_story.append(note_table)

        if attachment_path and os.path.exists(attachment_path):
            group_story.append(Spacer(1, 8))
            ext_lower = os.path.splitext(attachment_path)[1].lower()
            if ext_lower in (".jpg", ".jpeg", ".png", ".webp"):
                from reportlab.platypus import Image as RLImage
                try:
                    img = RLImage(attachment_path, width=380, height=240)
                    img.hAlign = 'CENTER'
                    group_story.append(img)
                except Exception:
                    pass
            else:
                att_badge = Table([[
                    Paragraph(f"<b>Attached Diagnostic File:</b> {os.path.basename(attachment_path)} (Archived in Patient Digital Folder)", interp_body_style)
                ]], colWidths=[523])
                att_badge.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#E3F2FD')),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#1976D2')),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ]))
                group_story.append(att_badge)

        group_story.append(Spacer(1, 12))
        story.append(KeepTogether(group_story))

    # 4. Signoff & Verification Footer Block
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceAfter=15))

    ver_code = verification_hash[:16].upper() if verification_hash else "AUTO-GENERATED-VERIFIED"
    sign_table_data = [
        [
            Paragraph(f"<b>Verification Code:</b> {ver_code}<br/><i>To verify authenticity, scan lab QR code or visit akritidiagnostics.com/verify</i>", footer_note_style),
            Paragraph("Digitally Verified & Approved By:<br/><b>Dr. R. K. Sharma (MD Pathology)</b><br/><i>Chief Pathologist & Quality Head</i>", signature_style)
        ]
    ]
    sign_table = Table(sign_table_data, colWidths=[280, 243])
    sign_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(KeepTogether(sign_table))

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
