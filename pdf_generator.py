from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os
import base64
import io

def generate_jobcard_pdf(record, filename="jobcard.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=17,
        textColor=colors.HexColor('#0056b3')
    )
    
    sub_title_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=10,
        textColor=colors.HexColor('#4a5568')
    )
    
    normal_style = ParagraphStyle(
        'DocNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#2d3748')
    )
    
    bold_style = ParagraphStyle(
        'DocNormalBold',
        parent=normal_style,
        fontName='Helvetica-Bold'
    )

    # --- HEADER BLOCK ---
    header_data = [
        [
            Paragraph("<b>UNIPOS RETAIL SOLUTIONS</b>", title_style),
            Paragraph(f"<b>Jobcard No:</b> {record.get('jc_no', 'N/A')}", ParagraphStyle('JCRight', parent=sub_title_style, alignment=2, fontSize=11, textColor=colors.HexColor('#dc2626')))
        ],
        [
            Paragraph("Head Office | P.O. Box 28405, Danhof 9310<br/>info@unipos.co.za | Tel: 086 110 2320", normal_style),
            Paragraph(f"<b>Date:</b> {record.get('date', record.get('date_str', 'N/A'))}", ParagraphStyle('DateRight', parent=sub_title_style, alignment=2))
        ]
    ]
    header_table = Table(header_data, colWidths=[310, 245])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6))

    # --- CLIENT & TECH META INFO ---
    meta_data = [
        [
            Paragraph(f"<b>Client (To):</b> {record.get('client', 'N/A')}", normal_style),
            Paragraph(f"<b>Primary Tech:</b> {record.get('tech', 'N/A')}", normal_style)
        ],
        [
            Paragraph(f"<b>Called By:</b> {record.get('called_by', 'N/A')}", normal_style),
            Paragraph(f"<b>Additional On Site:</b> {record.get('additional_techs', record.get('on_site_crew', 'None'))}", normal_style)
        ],
        [
            Paragraph(f"<b>Vehicle Reg:</b> {record.get('vehicle', 'N/A')}", normal_style),
            Paragraph(f"<b>Payment Method:</b> {record.get('payment_method', 'N/A')}", normal_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[277, 278])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6))

    # --- FAULT & ACTIONS LOG ---
    actions_text = record.get('actions', 'N/A').replace(chr(10), '<br/>')
    fault_actions_data = [
        [Paragraph(f"<b>Details of Fault:</b> {record.get('fault', 'N/A')}", normal_style)],
        [Paragraph(f"<b>Actions Log & Work History:</b><br/>{actions_text}", normal_style)]
    ]
    fa_table = Table(fault_actions_data, colWidths=[555])
    fa_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(fa_table)
    story.append(Spacer(1, 6))

    # --- STOCK / SPARES TABLE ---
    story.append(Paragraph("<b>Stock / Spares / Line Items & Serial Numbers:</b>", sub_title_style))
    story.append(Spacer(1, 2))

    stock_table_data = [[
        Paragraph("<b>Description / Item Name</b>", bold_style),
        Paragraph("<b>Serial Numbers (S/N)</b>", bold_style),
        Paragraph("<b>Qty</b>", bold_style),
        Paragraph("<b>Price (Ex)</b>", bold_style),
        Paragraph("<b>Total (Ex)</b>", bold_style)
    ]]

    items = record.get('items', []) or record.get('stock_items', [])
    if items:
        for itm in items:
            serials_list = itm.get('serials', [])
            serials_str = ", ".join([str(s) for s in serials_list if s]) if serials_list else "N/A"
            qty = float(itm.get('qty', 1) or 1)
            price = float(itm.get('price', 0.0) or 0.0)
            line_total = qty * price
            
            stock_table_data.append([
                Paragraph(str(itm.get('item', '')), normal_style),
                Paragraph(serials_str, normal_style),
                Paragraph(str(int(qty)), normal_style),
                Paragraph(f"R{price:.2f}", normal_style),
                Paragraph(f"R{line_total:.2f}", normal_style)
            ])
    else:
        stock_table_data.append([
            Paragraph("No stock items added.", normal_style),
            Paragraph("N/A", normal_style),
            Paragraph("0", normal_style),
            Paragraph("R0.00", normal_style),
            Paragraph("R0.00", normal_style)
        ])

    stock_table = Table(stock_table_data, colWidths=[175, 175, 35, 85, 85])
    stock_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e2e8f0')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(stock_table)
    story.append(Spacer(1, 6))

    # --- TIME & TRAVEL METRICS ---
    km_driven = float(record.get('km_driven', 0.0) or 0.0)
    rate_per_km = float(record.get('rate_per_km', 7.50) or 7.50)
    km_total = km_driven * rate_per_km

    time_travel_data = [
        [
            Paragraph(f"<b>Time Started:</b> {record.get('time_start', '00:00')}", normal_style),
            Paragraph(f"<b>KM Travelled:</b> {km_driven} km (Rate: R{rate_per_km:.2f}/km $\rightarrow$ Total: R{km_total:.2f})", normal_style)
        ],
        [
            Paragraph(f"<b>Time Completed:</b> {record.get('time_end', '00:00')}", normal_style),
            Paragraph(f"<b>Billable Hours:</b> {record.get('billable_hrs', 1.0)} hrs @ R{record.get('hourly_rate', 650.0):.2f}/hr", normal_style)
        ]
    ]
    tt_table = Table(time_travel_data, colWidths=[277, 278])
    tt_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(tt_table)
    story.append(Spacer(1, 6))

    # --- CUSTOMER COMMENTS & COMPLETION STATUS ---
    is_completed = record.get('is_completed', True)
    status_str = "YES" if is_completed else f"NO (Incomplete / Outstanding Reason: {record.get('incomplete_reason', 'Not specified')})"
    
    comments_data = [
        [Paragraph(f"<b>Customer Comments:</b> {record.get('customer_comments', 'None provided.')}", normal_style)],
        [Paragraph(f"<b>Job Successfully Completed:</b> {status_str}", normal_style)]
    ]
    comm_table = Table(comments_data, colWidths=[555])
    comm_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(comm_table)
    story.append(Spacer(1, 6))

    # --- FINANCIAL TOTALS SUMMARY ---
    callout_fee = float(record.get('callout_fee', 0.0) or 0.0)
    fin_data = [
        [Paragraph(f"<b>Call-Out Fee:</b>", normal_style), Paragraph(f"R{callout_fee:.2f}", ParagraphStyle('R0', parent=normal_style, alignment=2))],
        [Paragraph("<b>Sub Total (Ex):</b>", normal_style), Paragraph(f"R{record.get('subtotal', 0.0):.2f}", ParagraphStyle('R1', parent=normal_style, alignment=2))],
        [Paragraph("<b>15% VAT Value:</b>", normal_style), Paragraph(f"R{record.get('vat', 0.0):.2f}", ParagraphStyle('R2', parent=normal_style, alignment=2))],
        [Paragraph("<b>Total Due (Inc):</b>", bold_style), Paragraph(f"<b>R{record.get('total', 0.0):.2f}</b>", ParagraphStyle('R3', parent=bold_style, alignment=2, textColor=colors.HexColor('#0056b3')))]
    ]
    fin_table = Table(fin_data, colWidths=[420, 135])
    fin_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f1f5f9')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(fin_table)
    story.append(Spacer(1, 8))

    # --- SIGNATURES SECTION ---
    def decode_base64_sig(b64_str):
        if not b64_str or ',' not in b64_str:
            return None
        try:
            img_data = base64.b64decode(b64_str.split(',')[1])
            return Image(io.BytesIO(img_data), width=160, height=45)
        except Exception:
            return None

    tech_sig_img = decode_base64_sig(record.get('tech_signature'))
    client_sig_img = decode_base64_sig(record.get('client_signature'))

    tech_sig_content = tech_sig_img if tech_sig_img else Paragraph("<br/><br/>___________________________<br/>Signed on Site", normal_style)
    client_sig_content = client_sig_img if client_sig_img else Paragraph("<br/><br/>___________________________<br/>Accepted & Verified", normal_style)

    sig_data = [
        [
            Paragraph("<b>Technician Signature:</b>", sub_title_style),
            Paragraph("<b>Authorized Client Signature:</b>", sub_title_style)
        ],
        [
            tech_sig_content,
            client_sig_content
        ]
    ]
    sig_table = Table(sig_data, colWidths=[277, 278])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(sig_table)

    doc.build(story)
    return filename