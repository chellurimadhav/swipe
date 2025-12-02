from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import Customer, Order, OrderItem, Product, Invoice, InvoiceItem
from database import db
from bson import ObjectId
from datetime import datetime, timedelta
import uuid

admin_bp = Blueprint('admin', __name__)

# Customer Management Routes
@admin_bp.route('/customers', methods=['GET'])
@login_required
def get_customers():
    """Get all customers for the current admin (both active and inactive)"""
    try:
        # Debug: Check authentication status
        print(f"[DEBUG] Current user: {current_user}")
        print(f"[DEBUG] Current user type: {type(current_user)}")
        print(f"[DEBUG] Has id attr: {hasattr(current_user, 'id') if current_user else False}")
        
        # Check if user is authenticated
        if not current_user:
            print("[DEBUG] No current_user - returning 401")
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        if not hasattr(current_user, 'id'):
            print("[DEBUG] current_user has no id attribute - returning 401")
            return jsonify({'success': False, 'error': 'User not authenticated - missing id'}), 401
        
        print(f"[DEBUG] User ID: {current_user.id}")
        
        # Get database connection
        from models import get_db
        database = get_db()
        if database is None:
            return jsonify({'success': False, 'error': 'Database not initialized'}), 500
        
        # Show ALL customers so admin can see everyone, including those who registered via customer login
        # This includes customers created by admin and customers who registered through customer login
        try:
            # Get ALL customers - no filtering by user_id so admin can see all customers
            query = {}
            
            # Limit to prevent performance issues
            customers_docs = list(database['customers'].find(query).sort('name', 1).limit(1000))
            customers = []
            for doc in customers_docs:
                if not isinstance(doc, dict):
                    print(f"Warning: Skipping non-dict customer document: {doc}")
                    continue
                customer = Customer.from_dict(doc)
                if customer:
                    customers.append(customer)
                else:
                    print(f"Warning: Customer.from_dict returned None for document: {doc}")
        except Exception as query_error:
            import traceback
            print(f"Query error: {str(query_error)}")
            traceback.print_exc()
            customers = []
        
        customers_data = []
        
        # Process customers with error handling to prevent one failure from blocking all
        for customer in customers:
            try:
                # Safely access all fields with null checks
                customer_id = customer.id if hasattr(customer, 'id') and customer.id else None
                if not customer_id:
                    print(f"Warning: Skipping customer with no ID: {customer}")
                    continue
                
                # Skip counting for list view - it's too slow. Counts are available in detail view.
                # This makes the list load much faster
                customers_data.append({
                    'id': str(customer_id),  # Ensure ID is string for frontend
                    'name': getattr(customer, 'name', '') or '',
                    'email': getattr(customer, 'email', '') or '',
                    'phone': getattr(customer, 'phone', '') or '',
                    'billing_address': getattr(customer, 'billing_address', '') or '',
                    'shipping_address': getattr(customer, 'shipping_address', '') or '',
                    'state': getattr(customer, 'state', '') or '',
                    'pincode': getattr(customer, 'pincode', '') or '',
                    'gstin': getattr(customer, 'gstin', '') or '',
                    'company_name': getattr(customer, 'company_name', '') or '',
                    'created_at': customer.created_at.isoformat() if hasattr(customer, 'created_at') and customer.created_at else datetime.utcnow().isoformat(),
                    'is_active': getattr(customer, 'is_active', True) if getattr(customer, 'is_active', None) is not None else True
                })
            except Exception as customer_error:
                print(f"Error processing customer {getattr(customer, 'id', 'unknown')}: {str(customer_error)}")
                import traceback
                traceback.print_exc()
                continue
        
        return jsonify({'success': True, 'customers': customers_data})
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error getting customers: {str(e)}")
        print(f"Full traceback:\n{error_trace}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/customers', methods=['POST'])
@login_required
def create_customer():
    """Create a new customer"""
    try:
        # Debug: Check authentication
        print(f"[CREATE CUSTOMER] Current user: {current_user}")
        print(f"[CREATE CUSTOMER] User ID: {current_user.id if current_user and hasattr(current_user, 'id') else 'N/A'}")
        
        # Get request data
        data = request.get_json()
        print(f"[CREATE CUSTOMER] Received data: {data}")
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'success': False, 'error': 'Name is required'}), 400
        if not data.get('email'):
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
        # Check if customer with same email already exists
        existing_customer = Customer.find_by_email(data['email'])
        if existing_customer:
            return jsonify({'success': False, 'error': 'Customer with this email already exists'}), 400
        
        # Get phone - handle both with and without country code
        # Use empty string instead of None to handle databases where phone is NOT NULL
        phone = data.get('phone', '') or ''
        
        # Ensure user_id is set
        user_id = current_user.id if current_user and hasattr(current_user, 'id') else None
        if not user_id:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        print(f"[CREATE CUSTOMER] Creating customer with user_id: {user_id}")
        
        # Create new customer with all fields - use safe defaults
        try:
            customer = Customer(
                user_id=user_id,
                name=data.get('name', '').strip(),
                email=data.get('email', '').strip(),
                phone=phone or '',  # Use empty string to handle NOT NULL constraint in some databases
                gstin=data.get('gstin', '').strip() or None,
                company_name=data.get('company_name', '').strip() or None,
                billing_address=data.get('billing_address', '').strip() or None,
                shipping_address=data.get('shipping_address', '').strip() or data.get('billing_address', '').strip() or None,
                state=data.get('state', '').strip() or None,
                pincode=data.get('pincode', '').strip() or None,
                bank_name=data.get('bank_name', '').strip() or None,
                bank_account_number=data.get('bank_account_number', '').strip() or None,
                bank_ifsc=data.get('bank_ifsc', '').strip() or None,
                opening_balance=float(data.get('opening_balance', 0)) if data.get('opening_balance') else 0.0,
                opening_balance_type=data.get('opening_balance_type', 'debit') or 'debit',
                credit_limit=float(data.get('credit_limit', 0)) if data.get('credit_limit') else 0.0,
                discount=float(data.get('discount', 0)) if data.get('discount') else 0.0,
                notes=data.get('notes', '').strip() or None,
                tags=data.get('tags', '').strip() or None,
                cc_emails=data.get('cc_emails', '').strip() or None
            )
            
            # Set password (required field)
            password = data.get('password', 'default123')
            customer.set_password(password)
            
            print(f"[CREATE CUSTOMER] Customer object created, saving...")
            customer.save()
            print(f"[CREATE CUSTOMER] Customer ID: {customer.id}")
            print(f"[CREATE CUSTOMER] Customer saved successfully")
            
        except Exception as create_error:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[CREATE CUSTOMER] Error creating customer object: {str(create_error)}")
            print(f"[CREATE CUSTOMER] Full traceback:\n{error_trace}")
            return jsonify({'success': False, 'error': f'Database error: {str(create_error)}'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Customer created successfully',
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone or ''
            }
        })
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[CREATE CUSTOMER] Error creating customer: {str(e)}")
        print(f"[CREATE CUSTOMER] Full traceback:\n{error_trace}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/customers/<customer_id>', methods=['GET'])
@login_required
def get_customer(customer_id):
    """Get specific customer details - admins can view all customers"""
    try:
        # Convert customer_id to string if needed (MongoDB uses string ObjectIds)
        customer_id_str = str(customer_id)
        # Allow admins to view all customers, not just their own
        customer = Customer.find_by_id(customer_id_str)
        
        if not customer:
            return jsonify({'success': False, 'message': 'Customer not found'}), 404
        
        # Get customer's orders
        from models import get_db
        database = get_db()
        try:
            customer_id_obj = ObjectId(customer_id_str) if ObjectId.is_valid(customer_id_str) else customer_id_str
        except:
            customer_id_obj = customer_id_str
        
        orders = list(database['orders'].find({'customer_id': customer_id_obj}).sort('created_at', -1).limit(20))
        orders_data = []
        for order_doc in orders:
            try:
                order = Order.from_dict(order_doc)
                if order:
                    orders_data.append({
                        'id': str(order.id),
                        'order_number': order.order_number,
                        'order_date': order.order_date.isoformat() if order.order_date else '',
                        'status': order.status,
                        'total_amount': float(order.total_amount) if order.total_amount else 0,
                        'created_at': order.created_at.isoformat() if order.created_at else ''
                    })
            except Exception as order_error:
                print(f"Error processing order: {order_error}")
                continue
        
        # Get products visible to this customer
        visible_products = []
        if hasattr(customer, 'user_id') and customer.user_id:
            admin_user_id = customer.user_id
            try:
                admin_user_id_obj = ObjectId(admin_user_id) if isinstance(admin_user_id, str) and ObjectId.is_valid(admin_user_id) else admin_user_id
                products_docs = list(database['products'].find({
                    'user_id': admin_user_id_obj,
                    '$or': [
                        {'is_active': True},
                        {'is_active': {'$exists': False}},
                        {'is_active': None}
                    ]
                }).sort('name', 1).limit(100))  # Limit to 100 for performance
                
                for product_doc in products_docs:
                    try:
                        product = Product.from_dict(product_doc)
                        if product:
                            visible_products.append({
                                'id': str(product.id),
                                'name': product.name or 'Unnamed Product',
                                'price': float(product.price or 0),
                                'stock_quantity': product.stock_quantity or 0,
                                'sku': product.sku or ''
                            })
                    except Exception as product_error:
                        print(f"Error processing product: {product_error}")
                        continue
            except Exception as products_error:
                print(f"Error getting visible products for customer {customer_id}: {products_error}")
        
        return jsonify({
            'success': True,
            'customer': {
                'id': str(customer.id),
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone,
                'gstin': customer.gstin or '',
                'billing_address': customer.billing_address,
                'shipping_address': customer.shipping_address or customer.billing_address,
                'state': customer.state,
                'pincode': customer.pincode,
                'created_at': customer.created_at.isoformat() if customer.created_at else '',
                'is_active': customer.is_active,
                'orders': orders_data,
                'orders_count': len(orders_data),
                'visible_products': visible_products,
                'visible_products_count': len(visible_products)
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/customers/<int:customer_id>', methods=['PUT'])
@login_required
def update_customer(customer_id):
    """Update customer details - admins can edit any customer"""
    try:
        # Allow admins to edit any customer, not just their own
        customer = Customer.find_by_id(customer_id)
        
        if not customer:
            return jsonify({'success': False, 'error': 'Customer not found'}), 404
        
        data = request.get_json()
        
        # Check if email is changed and already exists
        if data.get('email') and data['email'] != customer.email:
            existing_customer = Customer.find_by_email(data['email'])
            if existing_customer:
                return jsonify({'success': False, 'error': 'Email already registered'}), 400
        
        # Update customer data
        if 'name' in data:
            customer.name = data['name']
        if 'email' in data:
            customer.email = data['email']
        if 'phone' in data:
            customer.phone = data['phone']
        if 'gstin' in data:
            customer.gstin = data.get('gstin', '')
        if 'billing_address' in data:
            customer.billing_address = data['billing_address']
        if 'shipping_address' in data:
            customer.shipping_address = data.get('shipping_address', '')
        if 'state' in data:
            customer.state = data['state']
        if 'pincode' in data:
            customer.pincode = data['pincode']
        if 'is_active' in data:
            customer.is_active = data['is_active']
        
        # Update password if provided
        if data.get('password') and data['password'].strip():
            customer.set_password(data['password'])
        
        customer.save()
        
        return jsonify({
            'success': True,
            'message': 'Customer updated successfully',
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone,
                'gstin': customer.gstin or '',
                'billing_address': customer.billing_address,
                'shipping_address': customer.shipping_address or customer.billing_address,
                'state': customer.state,
                'pincode': customer.pincode,
                'is_active': customer.is_active
            }
        })
    
    except Exception as e:
        print(f"Error updating customer: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/customers/<int:customer_id>', methods=['DELETE'])
@login_required
def delete_customer(customer_id):
    """Delete a customer (hard delete)"""
    try:
        # Allow admins to delete any customer
        customer = Customer.find_by_id(customer_id)
        
        if not customer:
            return jsonify({'success': False, 'error': 'Customer not found'}), 404
        
        # Check if customer has invoices
        invoice_count = db['invoices'].count_documents({'customer_id': ObjectId(customer_id) if isinstance(customer_id, str) else customer_id})
        if invoice_count > 0:
            return jsonify({
                'success': False, 
                'message': 'Cannot delete customer with existing invoices. Please delete related invoices first.'
            }), 400
        
        # Check if customer has orders
        order_count = db['orders'].count_documents({'customer_id': ObjectId(customer_id) if isinstance(customer_id, str) else customer_id})
        if order_count > 0:
            return jsonify({
                'success': False, 
                'message': 'Cannot delete customer with existing orders. Please delete related orders first.'
            }), 400
        
        # Delete customer product prices first
        db['customer_product_prices'].delete_many({'customer_id': ObjectId(customer_id) if isinstance(customer_id, str) else customer_id})
        
        # Hard delete the customer
        db['customers'].delete_one({'_id': ObjectId(customer_id) if isinstance(customer_id, str) else customer_id})
        
        return jsonify({'success': True, 'message': 'Customer deleted successfully'})
    
    except Exception as e:
        print(f"Error deleting customer: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/customers/<int:customer_id>/toggle-status', methods=['POST'])
@login_required
def toggle_customer_status(customer_id):
    """Toggle customer active/inactive status"""
    try:
        # Allow admins to toggle status of any customer
        customer = Customer.find_by_id(customer_id)
        
        if not customer:
            return jsonify({'success': False, 'error': 'Customer not found'}), 404
        
        # Toggle is_active
        customer.is_active = not customer.is_active
        customer.save()
        
        return jsonify({
            'success': True,
            'message': f'Customer {"activated" if customer.is_active else "deactivated"} successfully',
            'is_active': customer.is_active
        })
    
    except Exception as e:
        print(f"Error toggling customer status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Order Management Routes
@admin_bp.route('/orders', methods=['GET'])
@login_required
def get_orders():
    """Get all orders - admins see ALL orders from ALL customers"""
    try:
        # Get database connection
        from models import get_db
        database = get_db()
        if database is None:
            return jsonify({'success': False, 'error': 'Database not initialized'}), 500
        
        customer_id = request.args.get('customer_id', type=int)
        
        # Get ALL orders - no filtering by admin assignment
        query = {}
        
        # Filter by customer if customer_id is provided
        if customer_id:
            query['customer_id'] = ObjectId(customer_id) if isinstance(customer_id, str) else customer_id
        
        # Convert query customer_id to ObjectId if it's a string
        if 'customer_id' in query and isinstance(query['customer_id'], str):
            if ObjectId.is_valid(query['customer_id']):
                query['customer_id'] = ObjectId(query['customer_id'])
        
        # Limit orders to prevent performance issues
        # Query all orders - no filtering needed, admins see all customer orders
        orders_docs = list(database['orders'].find(query).sort('created_at', -1).limit(500))
        print(f"[ADMIN ORDERS] Admin {current_user.id} requesting orders. Query: {query}")
        print(f"[ADMIN ORDERS] Found {len(orders_docs)} total orders in database")
        
        # Also check total count without limit for debugging
        total_count = database['orders'].count_documents(query)
        print(f"[ADMIN ORDERS] Total orders in database (no limit): {total_count}")
        
        # List all order numbers for debugging
        if total_count > 0:
            sample_orders = list(database['orders'].find({}, {'order_number': 1, 'customer_id': 1, 'created_at': 1}).limit(10))
            print(f"[ADMIN ORDERS] Sample orders: {[(o.get('order_number'), str(o.get('customer_id')), o.get('created_at')) for o in sample_orders]}")
        else:
            # If no orders found, check if collection exists and list all collections
            collections = database.list_collection_names()
            print(f"[ADMIN ORDERS] Available collections: {collections}")
            if 'orders' in collections:
                # Check if collection is empty
                order_count_check = database['orders'].count_documents({})
                print(f"[ADMIN ORDERS] Orders collection exists but has {order_count_check} documents")
            else:
                print(f"[ADMIN ORDERS] WARNING: 'orders' collection does not exist!")
        
        orders_data = []
        
        for order_doc in orders_docs:
            try:
                # Debug: print raw document
                print(f"[ADMIN ORDERS] Raw order doc: {order_doc.get('_id')}, customer_id: {order_doc.get('customer_id')}, order_number: {order_doc.get('order_number')}")
                
                order = Order.from_dict(order_doc)
                if not order:
                    print(f"[ADMIN ORDERS] Order.from_dict returned None for doc: {order_doc.get('_id')}")
                    continue
                    
                print(f"[ADMIN ORDERS] Processing order {order.id}: customer_id={order.customer_id} (type: {type(order.customer_id)}), order_number={order.order_number}")
                # Get customer details - handle both string and ObjectId customer_id
                customer = None
                if order.customer_id:
                    try:
                        # Try to find customer by ID (handles both string and ObjectId)
                        customer = Customer.find_by_id(str(order.customer_id))
                        if not customer:
                            print(f"[ADMIN ORDERS] Customer not found for customer_id: {order.customer_id}")
                    except Exception as customer_error:
                        print(f"[ADMIN ORDERS] Error finding customer {order.customer_id}: {customer_error}")
                
                # Get order items
                items_data = []
                order_id_obj = ObjectId(order.id) if isinstance(order.id, str) and ObjectId.is_valid(order.id) else order.id
                order_items = [OrderItem.from_dict(doc) for doc in database['order_items'].find(
                    {'order_id': order_id_obj}
                )]
                for item in order_items:
                    product = Product.find_by_id(item.product_id)
                    items_data.append({
                        'id': str(item.id) if item.id else None,
                        'product_id': str(item.product_id) if item.product_id else None,
                        'product_name': product.name if product else 'Unknown Product',
                        'quantity': item.quantity,
                        'unit_price': float(item.unit_price) if item.unit_price else 0,
                        'total': float(item.total) if item.total else 0
                    })
                
                # Ensure IDs are strings - use _id from document if order.id is None
                order_id_str = str(order.id) if order.id else str(order_doc.get('_id', ''))
                customer_id_str = str(order.customer_id) if order.customer_id else None
                
                # Validate that we have a valid order ID
                if not order_id_str or order_id_str == 'None':
                    print(f"[ADMIN ORDERS] Skipping order with invalid ID. Order doc _id: {order_doc.get('_id')}, order.id: {order.id}")
                    continue
                
                orders_data.append({
                    'id': order_id_str,
                    'order_number': order.order_number or f'ORD-{order_id_str[:8]}',
                    'customer_id': customer_id_str,
                    'customer_name': customer.name if customer else 'Unknown Customer',
                    'customer_email': customer.email if customer else '',
                    'customer_phone': customer.phone if customer else '',
                    'order_date': order.order_date.isoformat() if order.order_date else '',
                    'status': order.status or 'pending',
                    'total_amount': float(order.total_amount) if order.total_amount else 0,
                    'notes': order.notes or '',
                    'items': items_data,
                    'created_at': order.created_at.isoformat() if order.created_at else ''
                })
            except Exception as order_error:
                print(f"[ADMIN ORDERS] Error processing order: {order_error}")
                import traceback
                traceback.print_exc()
                continue
        
        return jsonify({'success': True, 'orders': orders_data})
    
    except Exception as e:
        print(f"Error getting orders: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/orders/<order_id>/status', methods=['PUT'])
@login_required
def update_order_status(order_id):
    """Update order status"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'success': False, 'error': 'Status is required'}), 400
        
        # Convert order_id to string (MongoDB uses string ObjectIds)
        order_id_str = str(order_id)
        print(f"[UPDATE ORDER STATUS] Updating order {order_id_str} to status: {new_status}")
        
        # Get database connection
        from models import get_db
        database = get_db()
        if database is None:
            return jsonify({'success': False, 'error': 'Database not initialized'}), 500
        
        # Try to find order directly from database
        try:
            order_id_obj = ObjectId(order_id_str) if ObjectId.is_valid(order_id_str) else order_id_str
            order_doc = database['orders'].find_one({'_id': order_id_obj})
            
            if not order_doc:
                print(f"[UPDATE ORDER STATUS] Order not found in database: {order_id_str}")
                return jsonify({'success': False, 'error': 'Order not found'}), 404
            
            order = Order.from_dict(order_doc)
            if not order:
                print(f"[UPDATE ORDER STATUS] Failed to parse order document: {order_id_str}")
                return jsonify({'success': False, 'error': 'Order not found'}), 404
        except Exception as find_error:
            print(f"[UPDATE ORDER STATUS] Error finding order: {find_error}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': f'Error finding order: {str(find_error)}'}), 500
        
        order.status = new_status
        order.updated_at = datetime.utcnow()
        order.save()
        
        print(f"[UPDATE ORDER STATUS] Order {order_id_str} status updated to {new_status}")
        return jsonify({'success': True, 'message': 'Order status updated successfully'})
    
    except Exception as e:
        print(f"Error updating order status: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/orders/<order_id>/generate-invoice', methods=['POST'])
@login_required
def generate_invoice_from_order(order_id):
    """Generate an invoice from an order"""
    try:
        # Get database connection
        from models import get_db
        database = get_db()
        if database is None:
            return jsonify({'success': False, 'error': 'Database not initialized'}), 500
        
        # Convert order_id to string (MongoDB uses string ObjectIds)
        order_id_str = str(order_id)
        print(f"[GENERATE INVOICE] Generating invoice for order: {order_id_str}")
        
        # Try to find order directly from database
        try:
            order_id_obj = ObjectId(order_id_str) if ObjectId.is_valid(order_id_str) else order_id_str
            order_doc = database['orders'].find_one({'_id': order_id_obj})
            
            if not order_doc:
                print(f"[GENERATE INVOICE] Order not found in database: {order_id_str}")
                return jsonify({'success': False, 'error': 'Order not found'}), 404
            
            order = Order.from_dict(order_doc)
            if not order:
                print(f"[GENERATE INVOICE] Failed to parse order document: {order_id_str}")
                return jsonify({'success': False, 'error': 'Order not found'}), 404
        except Exception as find_error:
            print(f"[GENERATE INVOICE] Error finding order: {find_error}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': f'Error finding order: {str(find_error)}'}), 500
        
        # Check if invoice already exists for this order
        order_id_obj = ObjectId(order_id_str) if ObjectId.is_valid(order_id_str) else order_id_str
        existing_invoice_doc = database['invoices'].find_one({'order_id': order_id_obj})
        if existing_invoice_doc:
            existing_invoice = Invoice.from_dict(existing_invoice_doc)
            if existing_invoice:
                return jsonify({
                    'success': True,
                    'message': 'Invoice already exists for this order',
                    'invoice': {
                        'id': str(existing_invoice.id),
                        'invoice_number': existing_invoice.invoice_number
                    }
                })
            return jsonify({'success': False, 'error': 'Invoice already exists for this order'}), 400
        
        # Get customer details to verify it exists
        customer = Customer.find_by_id(str(order.customer_id))
        if not customer:
            return jsonify({'success': False, 'error': 'Customer not found for this order'}), 404
        
        # Generate invoice number
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Create invoice
        invoice = Invoice(
            user_id=current_user.id,
            customer_id=str(order.customer_id),
            invoice_number=invoice_number,
            invoice_date=datetime.now().date(),
            due_date=(datetime.now() + timedelta(days=30)).date(),  # 30 days from now
            subtotal=order.total_amount,
            total_amount=order.total_amount,
            status='pending',
            notes=f"Invoice generated from order {order.order_number}",
            order_id=str(order.id)  # Link to the original order
        )
        invoice.save()
        print(f"[GENERATE INVOICE] Invoice saved. ID: {invoice.id}")
        
        # Add invoice items from order items
        order_items = [OrderItem.from_dict(doc) for doc in database['order_items'].find(
            {'order_id': order_id_obj}
        )]
        invoice_items_list = []
        for order_item in order_items:
            # Calculate GST (assuming 18% for now)
            gst_rate = 18.0
            item_total = order_item.quantity * order_item.unit_price
            gst_amount = item_total * (gst_rate / 100)
            
            invoice_item = InvoiceItem(
                invoice_id=invoice.id,
                product_id=order_item.product_id,
                quantity=order_item.quantity,
                unit_price=order_item.unit_price,
                gst_rate=gst_rate,
                gst_amount=gst_amount,
                total=item_total
            )
            invoice_item.save()
            invoice_items_list.append(invoice_item.to_dict())
        
        # Update invoice with items and calculate totals
        invoice.items = invoice_items_list
        invoice.calculate_totals()
        invoice.save()
        
        print(f"[GENERATE INVOICE] Invoice created successfully. Invoice ID: {invoice.id}, Invoice Number: {invoice.invoice_number}")
        return jsonify({
            'success': True,
            'message': 'Invoice generated successfully',
            'invoice': {
                'id': str(invoice.id),
                'invoice_number': invoice.invoice_number,
                'total_amount': float(invoice.total_amount)
            }
        })
    
    except Exception as e:
        print(f"Error generating invoice: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
