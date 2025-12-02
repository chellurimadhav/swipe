from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import Customer, Product, Order, OrderItem
from database import db
from bson import ObjectId
from forms import CustomerForm
from datetime import datetime
import uuid

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/customers')
@login_required
def index():
    """List all customers"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
    query = {'user_id': user_id_obj, 'is_active': True}
    
    if search:
        query['$or'] = [
            {'name': {'$regex': search, '$options': 'i'}},
            {'gstin': {'$regex': search, '$options': 'i'}},
            {'email': {'$regex': search, '$options': 'i'}},
            {'phone': {'$regex': search, '$options': 'i'}}
        ]
    
    # Manual pagination for MongoDB
    skip = (page - 1) * 20
    all_customers = [Customer.from_dict(doc) for doc in db['customers'].find(query).sort('name', 1).skip(skip).limit(20)]
    total_count = db['customers'].count_documents(query)
    
    # Create pagination-like object
    class Pagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page < self.pages
    
    customers = Pagination(all_customers, page, 20, total_count)
    
    return render_template('customers/index.html', customers=customers, search=search)

@customer_bp.route('/customers/new', methods=['GET', 'POST'])
@login_required
def new():
    """Create new customer"""
    form = CustomerForm()
    
    if form.validate_on_submit():
        customer = Customer(
            user_id=current_user.id,
            name=form.name.data,
            gstin=form.gstin.data,
            email=form.email.data,
            phone=form.phone.data,
            billing_address=form.billing_address.data,
            shipping_address=form.shipping_address.data or form.billing_address.data,
            state=form.state.data,
            pincode=form.pincode.data
        )
        
        customer.save()
        
        flash('Customer created successfully!', 'success')
        return redirect(url_for('customer.index'))
    
    return render_template('customers/new.html', form=form)

@customer_bp.route('/customers/<int:id>')
@login_required
def show(id):
    """Show customer details"""
    customer = Customer.find_by_id(id)
    if not customer or str(customer.user_id) != str(current_user.id) or not customer.is_active:
        from flask import abort
        abort(404)
    
    # Get customer's invoices
    from models import Invoice
    customer_id_obj = ObjectId(customer.id) if isinstance(customer.id, str) else customer.id
    invoices = [Invoice.from_dict(doc) for doc in db['invoices'].find(
        {'customer_id': customer_id_obj}
    ).sort('created_at', -1).limit(10)]
    
    return render_template('customers/show.html', customer=customer, invoices=invoices)

@customer_bp.route('/customers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit customer"""
    customer = Customer.find_by_id(id)
    if not customer or str(customer.user_id) != str(current_user.id) or not customer.is_active:
        from flask import abort
        abort(404)
    
    form = CustomerForm(obj=customer)
    
    if form.validate_on_submit():
        customer.name = form.name.data
        customer.gstin = form.gstin.data
        customer.email = form.email.data
        customer.phone = form.phone.data
        customer.billing_address = form.billing_address.data
        customer.shipping_address = form.shipping_address.data or form.billing_address.data
        customer.state = form.state.data
        customer.pincode = form.pincode.data
        
        customer.save()
        
        flash('Customer updated successfully!', 'success')
        return redirect(url_for('customer.show', id=customer.id))
    
    return render_template('customers/edit.html', form=form, customer=customer)

@customer_bp.route('/customers/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete customer (soft delete)"""
    customer = Customer.find_by_id(id)
    if not customer or str(customer.user_id) != str(current_user.id) or not customer.is_active:
        from flask import abort
        abort(404)
    
    # Check if customer has invoices
    if customer.invoices:
        flash('Cannot delete customer with existing invoices. Please delete invoices first.', 'error')
        return redirect(url_for('customer.show', id=customer.id))
    
    customer.is_active = False
    customer.save()
    
    flash('Customer deleted successfully!', 'success')
    return redirect(url_for('customer.index'))

@customer_bp.route('/api/customers/search')
@login_required
def search():
    """API endpoint for customer search (for invoice creation)"""
    search_term = request.args.get('q', '')
    
    if len(search_term) < 2:
        return jsonify([])
    
    user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
    customers = [Customer.from_dict(doc) for doc in db['customers'].find({
        'user_id': user_id_obj,
        'is_active': True,
        '$or': [
            {'name': {'$regex': search_term, '$options': 'i'}},
            {'gstin': {'$regex': search_term, '$options': 'i'}},
            {'phone': {'$regex': search_term, '$options': 'i'}}
        ]
    }).limit(10)]
    
    results = []
    for customer in customers:
        results.append({
            'id': customer.id,
            'name': customer.name,
            'gstin': customer.gstin,
            'phone': customer.phone,
            'state': customer.state,
            'billing_address': customer.billing_address
        })
    
    return jsonify(results)

@customer_bp.route('/api/customers/<int:id>')
@login_required
def get_customer(id):
    """API endpoint to get customer details"""
    customer = Customer.find_by_id(id)
    if not customer or str(customer.user_id) != str(current_user.id) or not customer.is_active:
        from flask import abort
        abort(404)
    
    return jsonify({
        'id': customer.id,
        'name': customer.name,
        'gstin': customer.gstin,
        'email': customer.email,
        'phone': customer.phone,
        'billing_address': customer.billing_address,
        'shipping_address': customer.shipping_address,
        'state': customer.state,
        'pincode': customer.pincode
    })

@customer_bp.route('/orders', methods=['POST'])
@login_required
def create_order():
    """Create a new order for the current customer"""
    try:
        data = request.get_json()
        
        # Generate order number
        order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Create order
        order = Order(
            order_number=order_number,
            customer_id=current_user.id,
            order_date=datetime.now(),
            status='pending',
            total_amount=data.get('total_amount', 0),
            notes=data.get('notes', '')
        )
        
        order.save()
        
        # Add order items
        items = data.get('items', [])
        order_items_list = []
        for item_data in items:
            # Get product details
            product = Product.find_by_id(item_data.get('product_id'))
            if not product:
                continue
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data.get('product_id'),
                quantity=item_data.get('quantity', 0),
                unit_price=item_data.get('unit_price', 0),
                total=item_data.get('quantity', 0) * item_data.get('unit_price', 0)
            )
            order_item.save()
            order_items_list.append(order_item.to_dict())
        
        # Update order with items
        order.items = order_items_list
        order.save()
        
        return jsonify({
            'success': True,
            'message': 'Order placed successfully',
            'order': {
                'id': order.id,
                'order_number': order.order_number
            }
        })
    
    except Exception as e:
        print(f"Error creating order: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@customer_bp.route('/orders', methods=['GET'])
@login_required
def get_customer_orders():
    """Get all orders for the current customer"""
    try:
        customer_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
        orders = [Order.from_dict(doc) for doc in db['orders'].find(
            {'customer_id': customer_id_obj}
        ).sort('created_at', -1)]
        orders_data = []
        
        for order in orders:
            # Get order items
            items_data = []
            order_items = order.items if order.items else []
            for item_data in order_items:
                if isinstance(item_data, dict):
                    product = Product.find_by_id(item_data.get('product_id'))
                    items_data.append({
                        'id': item_data.get('id'),
                        'product_id': item_data.get('product_id'),
                        'product_name': product.name if product else 'Unknown Product',
                        'quantity': item_data.get('quantity', 0),
                        'unit_price': float(item_data.get('unit_price', 0)),
                        'total': float(item_data.get('total', 0))
                    })
            
            orders_data.append({
                'id': order.id,
                'order_number': order.order_number,
                'order_date': order.order_date.isoformat() if order.order_date else '',
                'status': order.status,
                'total_amount': float(order.total_amount),
                'notes': order.notes,
                'items': items_data,
                'created_at': order.created_at.isoformat()
            })
        
        return jsonify({'success': True, 'orders': orders_data})
    
    except Exception as e:
        print(f"Error getting customer orders: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@customer_bp.route('/invoices', methods=['GET'])
@login_required
def get_customer_invoices():
    """Get all invoices for the current customer"""
    try:
        # Get invoices for the current customer
        from models import Invoice, InvoiceItem, Product
        customer_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
        invoices = [Invoice.from_dict(doc) for doc in db['invoices'].find(
            {'customer_id': customer_id_obj}
        ).sort('created_at', -1)]
        invoices_data = []
        
        for invoice in invoices:
            # Get invoice items
            items_data = []
            invoice_items = invoice.items if invoice.items else []
            for item_data in invoice_items:
                if isinstance(item_data, dict):
                    product = Product.find_by_id(item_data.get('product_id'))
                    items_data.append({
                        'id': item_data.get('id'),
                        'product_id': item_data.get('product_id'),
                        'product_name': product.name if product else 'Unknown Product',
                        'quantity': item_data.get('quantity', 0),
                        'unit_price': float(item_data.get('unit_price', 0)),
                        'gst_rate': float(item_data.get('gst_rate', 0)),
                        'gst_amount': float(item_data.get('gst_amount', 0)),
                        'total': float(item_data.get('total', 0))
                    })
            
            invoices_data.append({
                'id': invoice.id,
                'invoice_number': invoice.invoice_number,
                'invoice_date': invoice.invoice_date.isoformat() if invoice.invoice_date else '',
                'due_date': invoice.due_date.isoformat() if invoice.due_date else '',
                'status': invoice.status,
                'subtotal': float(invoice.subtotal),
                'cgst_amount': float(invoice.cgst_amount),
                'sgst_amount': float(invoice.sgst_amount),
                'igst_amount': float(invoice.igst_amount),
                'total_amount': float(invoice.total_amount),
                'notes': invoice.notes,
                'items': items_data,
                'order_id': invoice.order_id,  # Link to order if generated from order
                'created_at': invoice.created_at.isoformat()
            })
        
        return jsonify({'success': True, 'invoices': invoices_data})
    
    except Exception as e:
        print(f"Error getting customer invoices: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

