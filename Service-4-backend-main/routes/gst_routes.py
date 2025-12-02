from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_file
from flask_login import login_required, current_user
from models import Invoice, InvoiceItem, GSTReport
from database import db
from bson import ObjectId
from datetime import datetime, date
import calendar
import json
from pdf_generator import generate_gst_report_pdf

gst_bp = Blueprint('gst', __name__)

@gst_bp.route('/gst')
@login_required
def index():
    """GST dashboard"""
    # Get current month and year
    now = datetime.now()
    current_month = now.month
    current_year = now.year
    
    user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
    
    # Get GST summary for current month
    gst_summary_pipeline = [
        {'$match': {
            'user_id': user_id_obj,
            'status': 'paid',
            '$expr': {
                '$and': [
                    {'$eq': [{'$month': '$invoice_date'}, current_month]},
                    {'$eq': [{'$year': '$invoice_date'}, current_year]}
                ]
            }
        }},
        {'$group': {
            '_id': None,
            'total_taxable_value': {'$sum': '$subtotal'},
            'total_cgst': {'$sum': '$cgst_amount'},
            'total_sgst': {'$sum': '$sgst_amount'},
            'total_igst': {'$sum': '$igst_amount'},
            'total_invoices': {'$sum': 1}
        }}
    ]
    gst_summary_result = list(db['invoices'].aggregate(gst_summary_pipeline))
    gst_summary = gst_summary_result[0] if gst_summary_result else {
        'total_taxable_value': 0, 'total_cgst': 0, 'total_sgst': 0, 'total_igst': 0, 'total_invoices': 0
    }
    
    # Get GST summary by rate
    gst_by_rate_pipeline = [
        {'$match': {
            'user_id': user_id_obj,
            'status': 'paid',
            '$expr': {
                '$and': [
                    {'$eq': [{'$month': '$invoice_date'}, current_month]},
                    {'$eq': [{'$year': '$invoice_date'}, current_year]}
                ]
            }
        }},
        {'$unwind': '$items'},
        {'$group': {
            '_id': '$items.gst_rate',
            'taxable_value': {'$sum': '$items.total'},
            'gst_amount': {'$sum': '$items.gst_amount'},
            'item_count': {'$sum': 1}
        }},
        {'$project': {
            'gst_rate': '$_id',
            'taxable_value': 1,
            'gst_amount': 1,
            'item_count': 1,
            '_id': 0
        }}
    ]
    gst_by_rate = list(db['invoices'].aggregate(gst_by_rate_pipeline))
    
    # Get recent GST reports
    recent_reports = [GSTReport.from_dict(doc) for doc in db['gst_reports'].find(
        {'user_id': user_id_obj}
    ).sort('created_at', -1).limit(5)]
    
    return render_template('gst/index.html', 
                         gst_summary=gst_summary,
                         gst_by_rate=gst_by_rate,
                         recent_reports=recent_reports,
                         current_month=current_month,
                         current_year=current_year)

@gst_bp.route('/gst/gstr1')
@login_required
def gstr1():
    """Generate GSTR-1 report"""
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    
    # Get invoices for the specified month
    user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
    invoices = [Invoice.from_dict(doc) for doc in db['invoices'].find({
        'user_id': user_id_obj,
        'status': 'paid',
        '$expr': {
            '$and': [
                {'$eq': [{'$month': '$invoice_date'}, month]},
                {'$eq': [{'$year': '$invoice_date'}, year]}
            ]
        }
    })]
    
    # Group by GST rate
    gst_data = {}
    for invoice in invoices:
        invoice_items = invoice.items if invoice.items else []
        for item_data in invoice_items:
            if isinstance(item_data, dict):
                rate = item_data.get('gst_rate', 0)
            rate = item.gst_rate
            if rate not in gst_data:
                gst_data[rate] = {
                    'taxable_value': 0,
                    'cgst': 0,
                    'sgst': 0,
                    'igst': 0,
                    'invoices': []
                }
            
                gst_data[rate]['taxable_value'] += item_data.get('total', 0)
                gst_data[rate]['cgst'] += (item_data.get('gst_amount', 0) / 2) if invoice.cgst_amount and invoice.cgst_amount > 0 else 0
                gst_data[rate]['sgst'] += (item_data.get('gst_amount', 0) / 2) if invoice.sgst_amount and invoice.sgst_amount > 0 else 0
                gst_data[rate]['igst'] += item_data.get('gst_amount', 0) if invoice.igst_amount and invoice.igst_amount > 0 else 0
                
                customer = Customer.find_by_id(invoice.customer_id)
                if invoice.id not in [inv.get('id') for inv in gst_data[rate]['invoices']]:
                    gst_data[rate]['invoices'].append({
                        'id': invoice.id,
                        'invoice_number': invoice.invoice_number,
                        'invoice_date': invoice.invoice_date.isoformat() if invoice.invoice_date else '',
                        'customer_name': customer.name if customer else 'Unknown',
                        'customer_gstin': customer.gstin if customer else '',
                        'total_amount': invoice.total_amount or 0
                    })
    
    return render_template('gst/gstr1.html', 
                         gst_data=gst_data,
                         month=month,
                         year=year,
                         month_name=calendar.month_name[month])

@gst_bp.route('/gst/gstr3b')
@login_required
def gstr3b():
    """Generate GSTR-3B report"""
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    
    # Get invoices for the specified month
    user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
    invoices = [Invoice.from_dict(doc) for doc in db['invoices'].find({
        'user_id': user_id_obj,
        'status': 'paid',
        '$expr': {
            '$and': [
                {'$eq': [{'$month': '$invoice_date'}, month]},
                {'$eq': [{'$year': '$invoice_date'}, year]}
            ]
        }
    })]
    
    # Calculate totals
    total_taxable_value = sum(invoice.subtotal or 0 for invoice in invoices)
    total_cgst = sum(invoice.cgst_amount or 0 for invoice in invoices)
    total_sgst = sum(invoice.sgst_amount or 0 for invoice in invoices)
    total_igst = sum(invoice.igst_amount or 0 for invoice in invoices)
    total_gst = total_cgst + total_sgst + total_igst
    
    # Group by GST rate
    gst_by_rate = {}
    for invoice in invoices:
        invoice_items = invoice.items if invoice.items else []
        for item_data in invoice_items:
            if isinstance(item_data, dict):
                rate = item_data.get('gst_rate', 0)
                if rate not in gst_by_rate:
                    gst_by_rate[rate] = {
                        'taxable_value': 0,
                        'gst_amount': 0
                    }
                
                gst_by_rate[rate]['taxable_value'] += item_data.get('total', 0)
                gst_by_rate[rate]['gst_amount'] += item_data.get('gst_amount', 0)
    
    return render_template('gst/gstr3b.html',
                         invoices=invoices,
                         total_taxable_value=total_taxable_value,
                         total_cgst=total_cgst,
                         total_sgst=total_sgst,
                         total_igst=total_igst,
                         total_gst=total_gst,
                         gst_by_rate=gst_by_rate,
                         month=month,
                         year=year,
                         month_name=calendar.month_name[month])

@gst_bp.route('/gst/reports')
@login_required
def reports():
    """List all GST reports"""
    user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
    reports = [GSTReport.from_dict(doc) for doc in db['gst_reports'].find(
        {'user_id': user_id_obj}
    ).sort('created_at', -1)]
    
    return render_template('gst/reports.html', reports=reports)

@gst_bp.route('/gst/reports/generate', methods=['POST'])
@login_required
def generate_report():
    """Generate and save GST report"""
    report_type = request.form.get('report_type')
    month = int(request.form.get('month'))
    year = int(request.form.get('year'))
    
    if report_type not in ['GSTR1', 'GSTR3B']:
        flash('Invalid report type', 'error')
        return redirect(url_for('gst.reports'))
    
    # Check if report already exists
    user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
    existing_report_doc = db['gst_reports'].find_one({
        'user_id': user_id_obj,
        'report_type': report_type,
        'period_month': month,
        'period_year': year
    })
    
    if existing_report_doc:
        flash('Report for this period already exists', 'error')
        return redirect(url_for('gst.reports'))
    
    # Get invoices for the period
    invoices = [Invoice.from_dict(doc) for doc in db['invoices'].find({
        'user_id': user_id_obj,
        'status': 'paid',
        '$expr': {
            '$and': [
                {'$eq': [{'$month': '$invoice_date'}, month]},
                {'$eq': [{'$year': '$invoice_date'}, year]}
            ]
        }
    })]
    
    # Calculate totals
    total_taxable_value = sum(invoice.subtotal or 0 for invoice in invoices)
    total_cgst = sum(invoice.cgst_amount or 0 for invoice in invoices)
    total_sgst = sum(invoice.sgst_amount or 0 for invoice in invoices)
    total_igst = sum(invoice.igst_amount or 0 for invoice in invoices)
    
    # Prepare report data
    from models import Customer
    report_data = {
        'invoices': []
    }
    for invoice in invoices:
        customer = Customer.find_by_id(invoice.customer_id)
        report_data['invoices'].append({
            'invoice_number': invoice.invoice_number,
            'invoice_date': invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else '',
            'customer_name': customer.name if customer else 'Unknown',
            'customer_gstin': customer.gstin if customer else '',
            'subtotal': float(invoice.subtotal or 0),
            'cgst': float(invoice.cgst_amount or 0),
            'sgst': float(invoice.sgst_amount or 0),
            'igst': float(invoice.igst_amount or 0),
            'total': float(invoice.total_amount or 0)
        })
    
    # Create report record
    report = GSTReport(
        user_id=current_user.id,
        report_type=report_type,
        period_month=month,
        period_year=year,
        total_taxable_value=total_taxable_value,
        total_cgst=total_cgst,
        total_sgst=total_sgst,
        total_igst=total_igst,
        report_data=report_data
    )
    
    report.save()
    
    flash(f'{report_type} report generated successfully!', 'success')
    return redirect(url_for('gst.reports'))

@gst_bp.route('/gst/reports/<int:id>')
@login_required
def show_report(id):
    """Show GST report details"""
    report = GSTReport.find_by_id(id)
    if not report or str(report.user_id) != str(current_user.id):
        from flask import abort
        abort(404)
    
    return render_template('gst/show_report.html', report=report)

@gst_bp.route('/gst/reports/<int:id>/pdf')
@login_required
def download_report_pdf(id):
    """Download GST report as PDF"""
    report = GSTReport.find_by_id(id)
    if not report or str(report.user_id) != str(current_user.id):
        from flask import abort
        abort(404)
    
    # Generate PDF
    pdf_path = generate_gst_report_pdf(report)
    
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f'{report.report_type}_{report.period_month:02d}_{report.period_year}.pdf',
        mimetype='application/pdf'
    )

@gst_bp.route('/gst/reports/<int:id>/delete', methods=['POST'])
@login_required
def delete_report(id):
    """Delete GST report"""
    report = GSTReport.find_by_id(id)
    if not report or str(report.user_id) != str(current_user.id):
        from flask import abort
        abort(404)
    
    report_id_obj = ObjectId(id) if isinstance(id, str) else id
    db['gst_reports'].delete_one({'_id': report_id_obj})
    
    flash('Report deleted successfully!', 'success')
    return redirect(url_for('gst.reports'))

@gst_bp.route('/api/gst/summary')
@login_required
def gst_summary():
    """API endpoint for GST summary data"""
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    
    # Get GST summary for the specified month
    user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
    summary_pipeline = [
        {'$match': {
            'user_id': user_id_obj,
            'status': 'paid',
            '$expr': {
                '$and': [
                    {'$eq': [{'$month': '$invoice_date'}, month]},
                    {'$eq': [{'$year': '$invoice_date'}, year]}
                ]
            }
        }},
        {'$group': {
            '_id': None,
            'total_taxable_value': {'$sum': '$subtotal'},
            'total_cgst': {'$sum': '$cgst_amount'},
            'total_sgst': {'$sum': '$sgst_amount'},
            'total_igst': {'$sum': '$igst_amount'},
            'total_invoices': {'$sum': 1}
        }}
    ]
    summary_result = list(db['invoices'].aggregate(summary_pipeline))
    summary = summary_result[0] if summary_result else {
        'total_taxable_value': 0, 'total_cgst': 0, 'total_sgst': 0, 'total_igst': 0, 'total_invoices': 0
    }
    
    return jsonify({
        'total_taxable_value': float(summary.get('total_taxable_value', 0) or 0),
        'total_cgst': float(summary.get('total_cgst', 0) or 0),
        'total_sgst': float(summary.get('total_sgst', 0) or 0),
        'total_igst': float(summary.get('total_igst', 0) or 0),
        'total_invoices': summary.get('total_invoices', 0) or 0
    })

