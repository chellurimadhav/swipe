from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from models import Customer, User, Product, CustomerProductPrice, Order, OrderItem, Invoice, InvoiceItem
from forms import CustomerRegistrationForm, CustomerLoginForm, ForgotPasswordForm, ResetPasswordForm
from database import db
from bson import ObjectId
from datetime import datetime
import uuid
import re
import secrets
import string

customer_auth_bp = Blueprint('customer_auth', __name__)

@customer_auth_bp.route('/register', methods=['POST'])
def register():
    """Customer registration - automatically links to first available admin"""
    try:
        data = request.get_json()
        
        # Check if email already exists
        if Customer.find_by_email(data['email']):
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        # Get database connection
        from models import get_db
        database = get_db()
        if database is None:
            return jsonify({'success': False, 'message': 'Database not initialized'}), 500
        
        # Get first admin user as default (customers register independently and are linked to first admin)
        # In a multi-admin system, you might want to allow customers to choose or assign them later
        admin_users_docs = list(database['users'].find().limit(1))
        default_user_id = None
        
        if admin_users_docs:
            admin_user = User.from_dict(admin_users_docs[0])
            if admin_user:
                default_user_id = admin_user.id
        
        if not default_user_id:
            return jsonify({'success': False, 'message': 'No admin user found. Please create an admin user first.'}), 500
        
        # Create new customer - automatically linked to admin so they can see all products
        customer = Customer(
            user_id=default_user_id,
            name=data['name'],
            email=data['email'],
            phone=data.get('phone', ''),
            gstin=data.get('gstin'),
            billing_address=data.get('billing_address'),
            shipping_address=data.get('shipping_address'),
            state=data.get('state'),
            pincode=data.get('pincode')
        )
        customer.set_password(data['password'])
        customer.save()
        
        # Ensure ID is a string (convert ObjectId if needed)
        customer_id = str(customer.id) if customer.id else None
        
        return jsonify({
            'success': True,
            'message': 'Registration successful! Please login.',
            'customer': {
                'id': customer_id,
                'name': customer.name,
                'email': customer.email
            }
        })
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Registration error: {error_msg}'}), 500

@customer_auth_bp.route('/login', methods=['POST'])
def login():
    """Customer login"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        if 'email' not in data or 'password' not in data:
            return jsonify({'success': False, 'message': 'Email and password are required'}), 400
        
        customer = Customer.find_by_email(data['email'])
        if customer and customer.check_password(data['password']):
            login_user(customer, remember=data.get('remember_me', False))
            session.permanent = True
            # Force session to be saved immediately
            session.modified = True
            
            # Ensure ID is a string (convert ObjectId if needed)
            customer_id = str(customer.id) if customer.id else None
            
            return jsonify({
                'success': True,
                'message': 'Login successful!',
                'customer': {
                    'id': customer_id,
                    'name': customer.name,
                    'email': customer.email
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
            
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Login error: {error_msg}'}), 500

@customer_auth_bp.route('/logout')
@login_required
def logout():
    """Customer logout"""
    logout_user()
    return jsonify({'success': True, 'message': 'Logout successful'})

@customer_auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Forgot password - send reset email"""
    try:
        data = request.get_json()
        email = data['email']
        
        customer = Customer.find_by_email(email)
        if not customer:
            return jsonify({'success': False, 'message': 'Email not found'}), 404
        
        # Generate reset token (in production, send email with reset link)
        reset_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        session['reset_token'] = reset_token
        session['reset_email'] = email
        
        # For now, just return success (in production, send email)
        return jsonify({
            'success': True,
            'message': 'Password reset instructions sent to your email',
            'reset_token': reset_token  # Remove this in production
        })
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Registration error: {error_msg}'}), 500

@customer_auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password with token"""
    try:
        data = request.get_json()
        reset_token = data.get('reset_token')
        new_password = data['password']
        
        # Verify reset token
        if reset_token != session.get('reset_token'):
            return jsonify({'success': False, 'message': 'Invalid reset token'}), 400
        
        email = session.get('reset_email')
        customer = Customer.find_by_email(email)
        
        if not customer:
            return jsonify({'success': False, 'message': 'Customer not found'}), 404
        
        # Update password
        customer.set_password(new_password)
        customer.save()
        
        # Clear session
        session.pop('reset_token', None)
        session.pop('reset_email', None)
        
        return jsonify({'success': True, 'message': 'Password reset successful'})
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Registration error: {error_msg}'}), 500

@customer_auth_bp.route('/profile')
def profile():
    """Get customer profile - also used for session verification"""
    try:
        if current_user.is_authenticated:
            # Ensure ID is a string (convert ObjectId if needed)
            customer_id = str(current_user.id) if hasattr(current_user, 'id') and current_user.id else None
            
            return jsonify({
                'success': True,
                'authenticated': True,
                'customer': {
                    'id': customer_id,
                    'name': current_user.name,
                    'email': current_user.email,
                    'phone': current_user.phone,
                    'gstin': current_user.gstin,
                    'billing_address': current_user.billing_address,
                    'shipping_address': current_user.shipping_address,
                    'state': current_user.state,
                    'pincode': current_user.pincode
                }
            })
        else:
            return jsonify({
                'success': False,
                'authenticated': False,
                'message': 'Not authenticated'
            }), 401
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'authenticated': False,
            'error': str(e)
        }), 500

@customer_auth_bp.route('/products', methods=['GET'])
@login_required
def get_customer_products():
    """Get all active products for the logged-in customer with customer-specific prices"""
    try:
        if not current_user or not hasattr(current_user, 'id'):
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        customer_id = current_user.id
        search = request.args.get('search', '').strip()
        
        # Get the admin user_id that this customer belongs to
        customer = Customer.find_by_id(customer_id)
        if not customer:
            return jsonify({'success': False, 'error': 'Customer not found'}), 404
        
        admin_user_id = customer.user_id
        print(f"[CUSTOMER PRODUCTS] Customer ID: {customer_id}, Admin User ID: {admin_user_id}")
        
        # Get database connection
        from models import get_db
        database = get_db()
        if database is None:
            return jsonify({'success': False, 'error': 'Database not initialized'}), 500
        
        # Build query - if customer has admin_user_id, filter by it; otherwise show all products
        if admin_user_id:
            # Convert admin_user_id to ObjectId if it's a string
            try:
                if isinstance(admin_user_id, str):
                    admin_user_id_obj = ObjectId(admin_user_id) if ObjectId.is_valid(admin_user_id) else None
                else:
                    admin_user_id_obj = admin_user_id
            except Exception as e:
                print(f"[CUSTOMER PRODUCTS] Error converting user_id to ObjectId: {e}")
                admin_user_id_obj = admin_user_id
            
            if admin_user_id_obj:
                # Query products for this specific admin
                query = {
                    'user_id': admin_user_id_obj,
                    '$or': [
                        {'is_active': True},
                        {'is_active': {'$exists': False}},
                        {'is_active': None}
                    ]
                }
            else:
                # Invalid admin_user_id, show all products
                print(f"[CUSTOMER PRODUCTS] Invalid admin_user_id, showing all products")
                query = {
                    '$or': [
                        {'is_active': True},
                        {'is_active': {'$exists': False}},
                        {'is_active': None}
                    ]
                }
        else:
            # Customer not linked to admin, show ALL products from ALL admins
            print(f"[CUSTOMER PRODUCTS] Customer not linked to admin, showing all products")
            query = {
                '$or': [
                    {'is_active': True},
                    {'is_active': {'$exists': False}},
                    {'is_active': None}
                ]
            }
        
        # Apply search filter if provided
        if search:
            search_query = {
                '$or': [
                    {'name': {'$regex': search, '$options': 'i'}},
                    {'sku': {'$regex': search, '$options': 'i'}},
                    {'description': {'$regex': search, '$options': 'i'}}
                ]
            }
            # Combine with existing query
            if 'user_id' in query:
                # Query has user_id filter
                query = {
                    '$and': [
                        {
                            'user_id': query['user_id'],
                            '$or': query['$or']
                        },
                        search_query
                    ]
                }
            else:
                # Query doesn't have user_id, just add search
                query = {
                    '$and': [
                        {
                            '$or': query['$or']
                        },
                        search_query
                    ]
                }
        
        print(f"[CUSTOMER PRODUCTS] Query: {query}")
        
        # Get all products from inventory (including those with 0 stock)
        products_docs = list(database['products'].find(query).sort('name', 1))
        print(f"[CUSTOMER PRODUCTS] Found {len(products_docs)} products with query")
        
        # If no products found and we filtered by user_id, try showing all products
        if len(products_docs) == 0 and admin_user_id:
            print(f"[CUSTOMER PRODUCTS] No products found for admin, trying all products")
            fallback_query = {
                '$or': [
                    {'is_active': True},
                    {'is_active': {'$exists': False}},
                    {'is_active': None}
                ]
            }
            if search:
                fallback_query = {
                    '$and': [
                        {
                            '$or': [
                                {'is_active': True},
                                {'is_active': {'$exists': False}},
                                {'is_active': None}
                            ]
                        },
                        {
                            '$or': [
                                {'name': {'$regex': search, '$options': 'i'}},
                                {'sku': {'$regex': search, '$options': 'i'}},
                                {'description': {'$regex': search, '$options': 'i'}}
                            ]
                        }
                    ]
                }
            products_docs = list(database['products'].find(fallback_query).sort('name', 1))
            print(f"[CUSTOMER PRODUCTS] Found {len(products_docs)} products with fallback query")
        
        products = []
        for doc in products_docs:
            if not isinstance(doc, dict):
                continue
            try:
                product = Product.from_dict(doc)
                if product:
                    products.append(product)
            except Exception as parse_error:
                print(f"[CUSTOMER PRODUCTS] Error parsing product document: {parse_error}")
                continue
        
        # Return products with customer-specific prices
        products_data = []
        for product in products:
            try:
                # Ensure product ID is a string
                product_id = str(product.id) if product.id else None
                if not product_id:
                    print(f"[CUSTOMER PRODUCTS] Skipping product with no ID: {product.name}")
                    continue
                
                # Get customer-specific price if available
                customer_price = None
                try:
                    customer_price = CustomerProductPrice.find_by_customer_and_product(customer_id, product_id)
                except Exception as price_error:
                    print(f"[CUSTOMER PRODUCTS] Error getting customer price for product {product_id}: {price_error}")
                
                # Use customer-specific price if available, otherwise use default price
                price = float(customer_price.price) if customer_price and customer_price.price else float(product.price or 0)
                has_custom_price = customer_price is not None
                default_price = float(product.price or 0)
                
                products_data.append({
                    'id': product_id,
                    'name': product.name or 'Unnamed Product',
                    'description': product.description or '',
                    'image_url': product.image_url or '',
                    'price': price,
                    'default_price': default_price,
                    'stock_quantity': product.stock_quantity or 0,
                    'has_custom_price': has_custom_price,
                    'sku': product.sku or '',
                    'category': product.category or ''
                })
            except Exception as product_error:
                import traceback
                print(f"[CUSTOMER PRODUCTS] Error processing product {getattr(product, 'id', 'unknown')}: {str(product_error)}")
                traceback.print_exc()
                continue
        
        print(f"[CUSTOMER PRODUCTS] Returning {len(products_data)} products to customer")
        
        return jsonify({
            'success': True,
            'products': products_data,
            'count': len(products_data)
        })
    
    except Exception as e:
        print(f"Error getting customer products: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@customer_auth_bp.route('/orders', methods=['GET'])
@login_required
def get_customer_orders():
    """Get all orders for the logged-in customer"""
    try:
        if not current_user or not hasattr(current_user, 'id'):
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        # Check if current_user is a Customer by checking for user_id attribute (only Customer has this)
        if not hasattr(current_user, 'user_id'):
            # Try to verify by querying the database
            customer = Customer.find_by_id(current_user.id)
            if not customer:
                return jsonify({'success': False, 'error': 'Invalid user type'}), 403
            customer_id = customer.id
        else:
            customer_id = current_user.id
        
        orders = [Order.from_dict(doc) for doc in db['orders'].find(
            {'customer_id': ObjectId(customer_id) if isinstance(customer_id, str) else customer_id}
        ).sort('created_at', -1)]
        orders_data = []
        
        for order in orders:
            # Get order items
            items_data = []
            order_items = [OrderItem.from_dict(doc) for doc in db['order_items'].find(
                {'order_id': ObjectId(order.id) if isinstance(order.id, str) else order.id}
            )]
            for item in order_items:
                product = Product.find_by_id(item.product_id)
                items_data.append({
                    'id': item.id,
                    'product_id': item.product_id,
                    'product_name': product.name if product else 'Unknown Product',
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'total': float(item.total)
                })
            
            orders_data.append({
                'id': order.id,
                'order_number': order.order_number,
                'order_date': order.order_date.isoformat() if order.order_date else '',
                'status': order.status,
                'total_amount': float(order.total_amount),
                'notes': order.notes or '',
                'items': items_data,
                'created_at': order.created_at.isoformat() if order.created_at else ''
            })
        
        return jsonify({'success': True, 'orders': orders_data})
    
    except Exception as e:
        print(f"Error getting customer orders: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@customer_auth_bp.route('/orders', methods=['POST'])
@login_required
def create_customer_order():
    """Create a new order for the logged-in customer"""
    try:
        if not current_user or not hasattr(current_user, 'id'):
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        # Check if current_user is a Customer by checking for user_id attribute (only Customer has this)
        if not hasattr(current_user, 'user_id'):
            # Try to verify by querying the database
            customer = Customer.find_by_id(current_user.id)
            if not customer:
                return jsonify({'success': False, 'error': 'Invalid user type'}), 403
            customer_id = customer.id
        else:
            customer_id = current_user.id
        
        data = request.get_json()
        
        # Generate order number
        order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Ensure customer_id is a string (MongoDB will convert to ObjectId in to_dict)
        customer_id_str = str(customer_id)
        print(f"[CREATE ORDER] Creating order for customer_id: {customer_id_str} (type: {type(customer_id_str)})")
        
        # Create order
        order = Order(
            order_number=order_number,
            customer_id=customer_id_str,
            order_date=datetime.now(),
            status='pending',
            total_amount=data.get('total_amount', 0),
            notes=data.get('notes', '')
        )
        order.save()
        print(f"[CREATE ORDER] Order saved successfully. Order ID: {order.id}, Order Number: {order.order_number}")
        
        # Add order items
        items = data.get('items', [])
        order_items_list = []
        for item_data in items:
            product_id = item_data.get('product_id')
            if not product_id:
                continue
            
            # Get product details
            product = Product.find_by_id(product_id)
            if not product:
                continue
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=product_id,
                quantity=item_data.get('quantity', 0),
                unit_price=item_data.get('unit_price', 0),
                total=item_data.get('quantity', 0) * item_data.get('unit_price', 0)
            )
            order_item.save()
            order_items_list.append(order_item)
        
        # Update order with items
        order.items = [item.to_dict() for item in order_items_list]
        order.calculate_totals()
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
        print(f"Error creating customer order: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@customer_auth_bp.route('/invoices', methods=['GET'])
@login_required
def get_customer_invoices():
    """Get all invoices for the logged-in customer"""
    try:
        if not current_user or not hasattr(current_user, 'id'):
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        # Check if current_user is a Customer by checking for user_id attribute (only Customer has this)
        if not hasattr(current_user, 'user_id'):
            # Try to verify by querying the database
            customer = Customer.find_by_id(current_user.id)
            if not customer:
                return jsonify({'success': False, 'error': 'Invalid user type'}), 403
            customer_id = customer.id
        else:
            customer_id = current_user.id
        
        invoices = [Invoice.from_dict(doc) for doc in db['invoices'].find(
            {'customer_id': ObjectId(customer_id) if isinstance(customer_id, str) else customer_id}
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
                'status': invoice.status or 'pending',
                'subtotal': float(invoice.subtotal) if invoice.subtotal else 0,
                'cgst_amount': float(invoice.cgst_amount) if invoice.cgst_amount else 0,
                'sgst_amount': float(invoice.sgst_amount) if invoice.sgst_amount else 0,
                'igst_amount': float(invoice.igst_amount) if invoice.igst_amount else 0,
                'total_amount': float(invoice.total_amount) if invoice.total_amount else 0,
                'notes': invoice.notes or '',
                'items': items_data,
                'order_id': invoice.order_id,
                'created_at': invoice.created_at.isoformat() if invoice.created_at else ''
            })
        
        return jsonify({'success': True, 'invoices': invoices_data})
    
    except Exception as e:
        print(f"Error getting customer invoices: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

