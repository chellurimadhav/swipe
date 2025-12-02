from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import Customer
from database import db
from bson import ObjectId
from forms import CustomerForm

admin_customer_bp = Blueprint('admin_customer', __name__)

@admin_customer_bp.route('/customers')
@login_required
def get_customers():
    """Get all customers for admin"""
    try:
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
        
        customer_list = []
        for customer in customers.items:
            customer_list.append({
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone,
                'gstin': customer.gstin,
                'state': customer.state,
                'billing_address': customer.billing_address,
                'created_at': customer.created_at.isoformat(),
                'is_active': customer.is_active
            })
        
        return jsonify({
            'success': True,
            'customers': customer_list,
            'pagination': {
                'page': customers.page,
                'pages': customers.pages,
                'per_page': customers.per_page,
                'total': customers.total,
                'has_next': customers.has_next,
                'has_prev': customers.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_customer_bp.route('/customers', methods=['POST'])
@login_required
def create_customer():
    """Create new customer"""
    try:
        data = request.get_json()
        
        # Check if email already exists
        if Customer.find_by_email(data['email']):
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        customer = Customer(
            user_id=current_user.id,
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            gstin=data.get('gstin'),
            billing_address=data['billing_address'],
            shipping_address=data.get('shipping_address', data['billing_address']),
            state=data['state'],
            pincode=data['pincode']
        )
        
        # Set password if provided
        if data.get('password'):
            customer.set_password(data['password'])
        
        customer.save()
        
        return jsonify({
            'success': True,
            'message': 'Customer created successfully!',
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_customer_bp.route('/customers/<int:customer_id>')
@login_required
def get_customer(customer_id):
    """Get specific customer details"""
    try:
        customer = Customer.find_by_id(customer_id)
        if customer and str(customer.user_id) != str(current_user.id):
            customer = None
        if customer and not customer.is_active:
            customer = None
        
        if not customer:
            return jsonify({'success': False, 'message': 'Customer not found'}), 404
        
        return jsonify({
            'success': True,
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone,
                'gstin': customer.gstin,
                'billing_address': customer.billing_address,
                'shipping_address': customer.shipping_address,
                'state': customer.state,
                'pincode': customer.pincode,
                'created_at': customer.created_at.isoformat(),
                'is_active': customer.is_active
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_customer_bp.route('/customers/<int:customer_id>', methods=['PUT'])
@login_required
def update_customer(customer_id):
    """Update customer"""
    try:
        customer = Customer.find_by_id(customer_id)
        if customer and str(customer.user_id) != str(current_user.id):
            customer = None
        if customer and not customer.is_active:
            customer = None
        
        if not customer:
            return jsonify({'success': False, 'message': 'Customer not found'}), 404
        
        data = request.get_json()
        
        # Check if email is changed and already exists
        if data.get('email') and data['email'] != customer.email:
            if Customer.find_by_email(data['email']):
                return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        # Update customer data
        customer.name = data.get('name', customer.name)
        customer.email = data.get('email', customer.email)
        customer.phone = data.get('phone', customer.phone)
        customer.gstin = data.get('gstin', customer.gstin)
        customer.billing_address = data.get('billing_address', customer.billing_address)
        customer.shipping_address = data.get('shipping_address', customer.shipping_address)
        customer.state = data.get('state', customer.state)
        customer.pincode = data.get('pincode', customer.pincode)
        
        # Update password if provided
        if data.get('password'):
            customer.set_password(data['password'])
        
        customer.save()
        
        return jsonify({
            'success': True,
            'message': 'Customer updated successfully!',
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_customer_bp.route('/customers/<int:customer_id>', methods=['DELETE'])
@login_required
def delete_customer(customer_id):
    """Delete customer (soft delete)"""
    try:
        customer = Customer.find_by_id(customer_id)
        if customer and str(customer.user_id) != str(current_user.id):
            customer = None
        if customer and not customer.is_active:
            customer = None
        
        if not customer:
            return jsonify({'success': False, 'message': 'Customer not found'}), 404
        
        # Check if customer has orders
        customer_id_obj = ObjectId(customer_id) if isinstance(customer_id, str) else customer_id
        order_count = db['orders'].count_documents({'customer_id': customer_id_obj})
        if order_count > 0:
            return jsonify({'success': False, 'message': 'Cannot delete customer with existing orders'}), 400
        
        customer.is_active = False
        customer.save()
        
        return jsonify({'success': True, 'message': 'Customer deleted successfully!'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_customer_bp.route('/customers/search')
@login_required
def search_customers():
    """Search customers"""
    try:
        search_term = request.args.get('q', '').strip()
        
        if len(search_term) < 2:
            return jsonify({'success': True, 'customers': []})
        
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
        
        return jsonify({'success': True, 'customers': results})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

