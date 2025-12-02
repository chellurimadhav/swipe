from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os
from datetime import datetime
from models import Invoice, Customer, Product, User
from database import db

def generate_invoice_pdf(invoice):
    """Generate PDF for invoice using ReportLab"""
    # Create PDF file
    filename = f"invoice_{invoice.invoice_number}.pdf"
    filepath = os.path.join('static', 'uploads', filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    story = []
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#007bff')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#333333')
    )
    
    normal_style = styles['Normal']
    
    # Title
    story.append(Paragraph("TAX INVOICE", title_style))
    story.append(Spacer(1, 20))
    
    # Business and Invoice Info
    business_data = [
        [Paragraph(f"<b>{invoice.user.business_name or 'My Business'}</b>", normal_style), 
         Paragraph(f"<b>Invoice No:</b> {invoice.invoice_number}", normal_style)],
        [Paragraph(f"GST: {invoice.user.gst_number or 'N/A'}", normal_style),
         Paragraph(f"<b>Date:</b> {invoice.invoice_date.strftime('%d/%m/%Y')}", normal_style)],
        [Paragraph(f"Address: {invoice.user.business_address or 'N/A'}", normal_style),
         Paragraph(f"<b>Due Date:</b> {invoice.due_date.strftime('%d/%m/%Y') if invoice.due_date else 'N/A'}", normal_style)],
        [Paragraph(f"Phone: {invoice.user.business_phone or 'N/A'}", normal_style), ""],
        [Paragraph(f"Email: {invoice.user.business_email or 'N/A'}", normal_style), ""]
    ]
    
    business_table = Table(business_data, colWidths=[4*inch, 3*inch])
    business_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(business_table)
    story.append(Spacer(1, 20))
    
    # Customer Info
    story.append(Paragraph("Bill To:", heading_style))
    customer_data = [
        [f"Name: {invoice.customer.name}"],
        [f"GSTIN: {invoice.customer.gstin or 'N/A'}"],
        [f"Address: {invoice.customer.billing_address}"],
        [f"Phone: {invoice.customer.phone}"],
        [f"Email: {invoice.customer.email or 'N/A'}"],
        [f"State: {invoice.customer.state} - {invoice.customer.pincode}"]
    ]
    
    customer_table = Table(customer_data, colWidths=[7*inch])
    customer_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('ROUNDEDCORNERS', [6]),
    ]))
    story.append(customer_table)
    story.append(Spacer(1, 20))
    
    # Invoice Items Table
    story.append(Paragraph("Invoice Items:", heading_style))
    
    # Table headers
    headers = ['S.No', 'Item', 'HSN', 'Qty', 'Rate', 'GST %', 'GST Amt', 'Total']
    table_data = [headers]
    
    # Add items
    for i, item in enumerate(invoice.items, 1):
        # Calculate item totals if not already calculated
        if not hasattr(item, 'total') or item.total == 0:
            item_total = item.quantity * item.unit_price
            item_gst = item_total * (item.gst_rate / 100)
            item.total = item_total + item_gst
            item.gst_amount = item_gst
        
        table_data.append([
            str(i),
            item.product.name if item.product else 'Unknown Product',
            item.product.hsn_code if item.product else 'N/A',
            str(item.quantity),
            f"₹{item.unit_price:.2f}",
            f"{item.gst_rate}%",
            f"₹{item.gst_amount:.2f}",
            f"₹{item.total:.2f}"
        ])
    
    # Create table
    item_table = Table(table_data, colWidths=[0.5*inch, 2*inch, 0.8*inch, 0.6*inch, 1*inch, 0.6*inch, 1*inch, 1*inch])
    item_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Headers
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),   # Data
        ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),  # Numbers
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    story.append(item_table)
    story.append(Spacer(1, 20))
    
    # Calculate totals
    subtotal = sum(item.quantity * item.unit_price for item in invoice.items)
    total_gst = sum(item.gst_amount for item in invoice.items)
    
    # Determine GST split based on customer state vs business state
    if invoice.customer.state == invoice.user.business_state:
        # Same state - CGST + SGST
        cgst = total_gst / 2
        sgst = total_gst / 2
    else:
        # Different state - IGST
        cgst = 0
        sgst = 0
    
    total_amount = subtotal + total_gst
    
    # Totals
    totals_data = [
        ['Subtotal:', f"₹{subtotal:.2f}"],
        ['CGST:', f"₹{cgst:.2f}"],
        ['SGST:', f"₹{sgst:.2f}"],
        ['Total Amount:', f"₹{total_amount:.2f}"]
    ]
    
    totals_table = Table(totals_data, colWidths=[2*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 14),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#007bff')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(totals_table)
    
    # Add notes if available
    if invoice.notes:
        story.append(Spacer(1, 20))
        story.append(Paragraph("Notes:", heading_style))
        story.append(Paragraph(invoice.notes, normal_style))
    
    # Add footer
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    story.append(Paragraph(f"Thank you for your business! | {invoice.user.business_name or 'My Business'}", footer_style))
    
    # Build PDF
    doc.build(story)
    return filepath

def generate_gst_report_pdf(report):
    """Generate PDF for GST report using ReportLab"""
    filename = f"gst_report_{report.report_type}_{report.period_month}_{report.period_year}.pdf"
    filepath = os.path.join('static', 'uploads', filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    story = []
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#007bff')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#333333')
    )
    
    normal_style = styles['Normal']
    
    # Title
    story.append(Paragraph(f"GST {report.report_type.upper()} Report", title_style))
    story.append(Spacer(1, 20))
    
    # Report Info
    info_data = [
        [Paragraph("<b>Report Type:</b>", normal_style), report.report_type.upper()],
        [Paragraph("<b>Period:</b>", normal_style), f"{report.period_month}/{report.period_year}"],
        [Paragraph("<b>Generated On:</b>", normal_style), report.created_at.strftime('%d/%m/%Y %H:%M')],
        [Paragraph("<b>Business:</b>", normal_style), report.user.business_name],
        [Paragraph("<b>GST Number:</b>", normal_style), report.user.gst_number]
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))
    
    # Summary
    story.append(Paragraph("Summary:", heading_style))
    summary_data = [
        ['Total Taxable Value:', f"₹{report.total_taxable_value:.2f}"],
        ['Total CGST:', f"₹{report.total_cgst:.2f}"],
        ['Total SGST:', f"₹{report.total_sgst:.2f}"],
        ['Total IGST:', f"₹{report.total_igst:.2f}"],
        ['Total Tax:', f"₹{report.total_cgst + report.total_sgst + report.total_igst:.2f}"]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#007bff')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(summary_table)
    
    # Build PDF
    doc.build(story)
    return filepath

def generate_sales_report_pdf(report_data, report_type, start_date, end_date):
    """Generate PDF for sales report using ReportLab"""
    filename = f"sales_report_{report_type}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"
    filepath = os.path.join('static', 'uploads', filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    story = []
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#007bff')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#333333')
    )
    
    normal_style = styles['Normal']
    
    # Title
    story.append(Paragraph(f"Sales Report - {report_type.title()}", title_style))
    story.append(Spacer(1, 20))
    
    # Report Info
    info_data = [
        [Paragraph("<b>Report Type:</b>", normal_style), report_type.title()],
        [Paragraph("<b>Period:</b>", normal_style), f"{start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}"],
        [Paragraph("<b>Generated On:</b>", normal_style), datetime.now().strftime('%d/%m/%Y %H:%M')]
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))
    
    # Summary
    story.append(Paragraph("Summary:", heading_style))
    summary_data = [
        ['Total Sales:', f"₹{report_data.get('total_sales', 0):.2f}"],
        ['Total Invoices:', str(report_data.get('total_invoices', 0))],
        ['Average Order Value:', f"₹{report_data.get('avg_order_value', 0):.2f}"],
        ['Total Tax Collected:', f"₹{report_data.get('total_tax', 0):.2f}"]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(summary_table)
    
    # Build PDF
    doc.build(story)
    return filepath
