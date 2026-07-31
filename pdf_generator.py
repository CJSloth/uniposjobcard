from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os

def generate_jobcard_pdf(record, filename="jobcard_output.pdf"):
    """
    Generates a clean, professional A4 PDF document for a Job Card record.
    `record` is a dictionary containing all form fields and stock line items.
    """
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

    # Custom Paragraph Styles
    title_style = ParagraphStyle(
        'CompanyTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=20,
        textColor=colors.HexColor('#0056b3')
    )

    jc_no_style = ParagraphStyle(
        'JCNoStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=16,
        alignment=2, # Right aligned
        textColor=colors.HexColor('#dc3545')
    )

    cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10
    )

    cell_normal = ParagraphStyle(
        'CellNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10
    )

    # 1. HEADER BRANDING & JC NUMBER
    header_data = [
        [
            Paragraph("<b>UNIPOS RETAIL SOLUTIONS</b><br/><font size=7 color='#555555'>Head Office | P.O. Box 28405, Danhof 9310<br/>info@unipos.co.za | Tel: 086 110 2320</font>", title_style),
            Paragraph(f"<b>Jobcard No:</b><br/><b>{record.get('jc_no', 'JC-0000')}</b><br/><font size=8 color='#555555'>Date: {record.get('date', '')}</font>", jc_no_style)
        ]
    ]
    
    header_table = Table(header_data, colWidths=[340, 200])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#0056b3'), spaceBefore=2, spaceAfter=8))

    # 2. METADATA MATRIX
    meta_data = [
        [
            Paragraph("<b>To (Client):</b> " + str(record.get('client', '')), cell_normal),
            Paragraph("<b>Called By:</b> " + str(record.get('called_by', '')), cell_normal)
        ],
        [
            Paragraph("<b>Technician:</b> " + str(record.get('tech', '')), cell_normal),
            Paragraph("<b>Reg No (Vehicle):</b> " + str(record.get('vehicle', '')), cell_normal)
        ]
    ]
    
    meta_table = Table(meta_data, colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8f9fa')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e9ecef')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # 3. FAULT & ACTIONS LOG
    fault_data = [
        [Paragraph("<b>Details of Fault:</b> " + str(record.get('fault', '')), cell_normal)],
        [Paragraph("<b>Actions Taken Log:</b><br/>" + str(record.get('actions', '')).replace('\n', '<br/>'), cell_normal)]
    ]
    fault_table = Table(fault_data, colWidths=[540])
    fault_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e9ecef')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(fault_table)
    story.append(Spacer(1, 10))

    # 4. STOCK & LINE ITEMS TABLE
    stock_headers = [
        Paragraph("<b>Description / Item Name</b>", cell_bold),
        Paragraph("<b>Serial Numbers (S/N)</b>", cell_bold),
        Paragraph("<b>Qty</b>", cell_bold),
        Paragraph("<b>Price (Ex)</b>", cell_bold),
        Paragraph("<b>Total (Ex)</b>", cell_bold)
    ]
    
    stock_table_data = [stock_headers]
    
    for item in record.get('items', []):
        serials_str = ", ".join(item.get('serials', [])) if item.get('serials') else "N/A"
        qty = item.get('qty', 1)
        price = item.get('price', 0.0)
        row_tot = qty * price
        
        stock_table_data.append([
            Paragraph(str(item.get('item', '')), cell_normal),
            Paragraph(serials_str, cell_normal),
            Paragraph(str(qty), cell_normal),
            Paragraph(f"R{price:.2f}", cell_normal),
            Paragraph(f"R{row_tot:.2f}", cell_normal)
        ])

    stock_table = Table(stock_table_data, colWidths=[200, 140, 40, 80, 80])
    stock_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e9ecef')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e9ecef')),
        ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(stock_table)
    story.append(Spacer(1, 10))

    # 5. FINANCIAL CALCULATIONS SUMMARY
    subtotal = record.get('subtotal', 0.0)
    vat = record.get('vat', 0.0)
    total = record.get('total', 0.0)

    fin_data = [
        [Paragraph("<b>Sub Total (Ex):</b>", cell_normal), Paragraph(f"R{subtotal:.2f}", cell_normal)],
        [Paragraph("<b>15% VAT Value:</b>", cell_normal), Paragraph(f"R{vat:.2f}", cell_normal)],
        [Paragraph("<b>Grand Total (Inc):</b>", cell_bold), Paragraph(f"<b>R{total:.2f}</b>", cell_bold)]
    ]
    fin_table = Table(fin_data, colWidths=[420, 120])
    fin_table.setStyle(TableStyle([
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('LINEABOVE', (0,2), (1,2), 1, colors.HexColor('#000000')),
        ('BACKGROUND', (0,2), (1,2), colors.HexColor('#f8f9fa')),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(fin_table)

    # Build document
    doc.build(story)
    return filenames