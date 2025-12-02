from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models import Invoice, Product, Customer, StockMovement
from database import db
from bson import ObjectId
from datetime import datetime, timedelta
import calendar

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Main dashboard page"""
    # Get current month and year
    now = datetime.now()
    current_month = now.month
    current_year = now.year
    
    user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
    
    # Sales summary for current month
    monthly_sales_pipeline = [
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
            'total_sales': {'$sum': '$total_amount'},
            'total_invoices': {'$sum': 1},
            'total_gst': {'$sum': {'$add': ['$cgst_amount', '$sgst_amount', '$igst_amount']}}
        }}
    ]
    monthly_sales_result = list(db['invoices'].aggregate(monthly_sales_pipeline))
    monthly_sales = monthly_sales_result[0] if monthly_sales_result else {'total_sales': 0, 'total_invoices': 0, 'total_gst': 0}
    
    # Inventory summary
    inventory_pipeline = [
        {'$match': {
            'user_id': user_id_obj,
            'is_active': True
        }},
        {'$group': {
            '_id': None,
            'total_products': {'$sum': 1},
            'stock_value': {'$sum': {'$multiply': ['$stock_quantity', '$price']}},
            'low_stock_count': {
                '$sum': {
                    '$cond': [
                        {'$lte': ['$stock_quantity', '$min_stock_level']},
                        1,
                        0
                    ]
                }
            }
        }}
    ]
    inventory_result = list(db['products'].aggregate(inventory_pipeline))
    inventory_summary = inventory_result[0] if inventory_result else {'total_products': 0, 'stock_value': 0, 'low_stock_count': 0}
    
    # Customer count
    customer_count = db['customers'].count_documents({
        'user_id': user_id_obj,
        'is_active': True
    })
    
    # Recent invoices
    recent_invoices = [Invoice.from_dict(doc) for doc in db['invoices'].find(
        {'user_id': user_id_obj}
    ).sort('created_at', -1).limit(5)]
    
    # Low stock products
    low_stock_products = [Product.from_dict(doc) for doc in db['products'].find({
        'user_id': user_id_obj,
        'is_active': True,
        '$expr': {'$lte': ['$stock_quantity', '$min_stock_level']}
    }).limit(5)]
    
    # Top selling products (last 30 days)
    thirty_days_ago = now - timedelta(days=30)
    top_products_pipeline = [
        {'$match': {
            'user_id': user_id_obj,
            'invoice_date': {'$gte': thirty_days_ago},
            'status': 'paid'
        }},
        {'$unwind': '$items'},
        {'$group': {
            '_id': '$items.product_id',
            'total_sold': {'$sum': '$items.quantity'},
            'product_name': {'$first': '$items.product_name'}
        }},
        {'$sort': {'total_sold': -1}},
        {'$limit': 5}
    ]
    top_products_result = list(db['invoices'].aggregate(top_products_pipeline))
    top_products = [{'name': p.get('product_name', 'Unknown'), 'total_sold': p.get('total_sold', 0)} for p in top_products_result]
    
    dashboard_data = {
        'monthly_sales': monthly_sales.get('total_sales', 0) or 0,
        'total_invoices': monthly_sales.get('total_invoices', 0) or 0,
        'total_gst': monthly_sales.get('total_gst', 0) or 0,
        'total_products': inventory_summary.get('total_products', 0) or 0,
        'stock_value': inventory_summary.get('stock_value', 0) or 0,
        'low_stock_count': inventory_summary.get('low_stock_count', 0) or 0,
        'customer_count': customer_count,
        'recent_invoices': recent_invoices,
        'low_stock_products': low_stock_products,
        'top_products': top_products
    }
    
    return render_template('dashboard/index.html', data=dashboard_data)

@dashboard_bp.route('/api/sales-chart')
@login_required
def sales_chart():
    """API endpoint for sales chart data"""
    # Get sales data for last 12 months
    now = datetime.now()
    sales_data = []
    
    for i in range(12):
        month = now.month - i
        year = now.year
        if month <= 0:
            month += 12
            year -= 1
        
        user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
        sales_pipeline = [
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
                'total_sales': {'$sum': '$total_amount'}
            }}
        ]
        sales_result = list(db['invoices'].aggregate(sales_pipeline))
        sales = sales_result[0].get('total_sales', 0) if sales_result else 0
        
        sales_data.append({
            'month': calendar.month_abbr[month],
            'sales': float(sales)
        })
    
    # Reverse to show oldest to newest
    sales_data.reverse()
    
    return jsonify(sales_data)

@dashboard_bp.route('/api/inventory-chart')
@login_required
def inventory_chart():
    """API endpoint for inventory chart data"""
    # Get products with their stock values
    user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
    products = [Product.from_dict(doc) for doc in db['products'].find(
        {'user_id': user_id_obj, 'is_active': True}
    )]
    
    inventory_data = []
    for product in products:
        inventory_data.append({
            'name': product.name,
            'stock_value': float(product.stock_quantity * product.price),
            'stock_quantity': product.stock_quantity
        })
    
    # Sort by stock value and take top 10
    inventory_data.sort(key=lambda x: x['stock_value'], reverse=True)
    inventory_data = inventory_data[:10]
    
    return jsonify(inventory_data)

@dashboard_bp.route('/api/recent-activity')
@login_required
def recent_activity():
    """API endpoint for recent activity"""
    # Get recent invoices
    user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
    recent_invoices = [Invoice.from_dict(doc) for doc in db['invoices'].find(
        {'user_id': user_id_obj}
    ).sort('created_at', -1).limit(10)]
    
    # Get recent stock movements
    # First get product IDs for this user
    product_ids = [ObjectId(doc['_id']) for doc in db['products'].find(
        {'user_id': user_id_obj},
        {'_id': 1}
    )]
    recent_movements = [StockMovement.from_dict(doc) for doc in db['stock_movements'].find(
        {'product_id': {'$in': product_ids}}
    ).sort('created_at', -1).limit(10)]
    
    activity_data = []
    
    # Add invoices to activity
    for invoice in recent_invoices:
        customer = Customer.find_by_id(invoice.customer_id)
        activity_data.append({
            'type': 'invoice',
            'message': f'Invoice {invoice.invoice_number} created for {customer.name if customer else "Unknown"}',
            'amount': float(invoice.total_amount) if invoice.total_amount else 0,
            'date': invoice.created_at.strftime('%Y-%m-%d %H:%M') if invoice.created_at else '',
            'status': invoice.status or 'pending'
        })
    
    # Add stock movements to activity
    for movement in recent_movements:
        product = Product.find_by_id(movement.product_id)
        activity_data.append({
            'type': 'stock',
            'message': f'{movement.movement_type.title()} {movement.quantity} units of {product.name if product else "Unknown"}',
            'quantity': movement.quantity,
            'date': movement.created_at.strftime('%Y-%m-%d %H:%M') if movement.created_at else '',
            'reference': movement.reference or ''
        })
    
    # Sort by date and take most recent 15
    activity_data.sort(key=lambda x: x['date'], reverse=True)
    activity_data = activity_data[:15]
    
    return jsonify(activity_data)

