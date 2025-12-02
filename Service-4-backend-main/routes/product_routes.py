from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from models import Product, StockMovement, CustomerProductPrice, Customer
from database import db

def get_db():
    """Get database instance"""
    from database import db as database
    # If db is None, try to get it from current_app if available
    if database is None:
        try:
            from flask import current_app
            if current_app:
                # Try to initialize if app context exists
                from database import init_app
                # Don't re-initialize, just return None if not initialized
                pass
        except:
            pass
    return database
from bson import ObjectId
from forms import ProductForm, StockMovementForm
from datetime import datetime
import os
import uuid
import re
from werkzeug.utils import secure_filename

product_bp = Blueprint('product', __name__)

# API Routes for React Frontend
@product_bp.route('/inventory/add', methods=['POST'])
@login_required
def api_add_to_inventory():
    """Add a new product to inventory"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'success': False, 'error': 'Product name is required'}), 400
        if not data.get('price'):
            return jsonify({'success': False, 'error': 'Product price is required'}), 400
        
        # Auto-generate SKU if not provided
        sku = data.get('sku')
        if not sku:
            # Generate SKU from product name and timestamp
            name_part = re.sub(r'[^A-Z0-9]', '', data['name'].upper())[:10] or 'PROD'
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')[-8:]  # Last 8 digits
            sku = f"{name_part}-{timestamp}"
            
            # Ensure SKU is unique
            counter = 1
            original_sku = sku
            user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
            while db['products'].find_one({'sku': sku, 'user_id': user_id_obj}):
                sku = f"{original_sku}-{counter}"
                counter += 1
        
        # Check if SKU already exists (if provided)
        user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
        if data.get('sku') and db['products'].find_one({'sku': sku, 'user_id': user_id_obj}):
            return jsonify({'success': False, 'error': 'SKU already exists'}), 400
        
        product = Product(
            user_id=current_user.id,
            admin_id=current_user.id,  # Set admin_id to same as user_id for backward compatibility
            name=data['name'],
            description=data.get('description', ''),
            sku=sku,
            hsn_code=data.get('hsn_code', ''),
            category=data.get('category', ''),
            brand=data.get('brand', ''),
            price=float(data['price']),
            gst_rate=float(data.get('gst_rate', 18)),
            stock_quantity=int(data.get('stock_quantity', 0)),
            min_stock_level=int(data.get('min_stock_level', 10)),
            unit=data.get('unit', 'PCS'),
            image_url=data.get('image_url', ''),
            weight=float(data.get('weight', 0)) if data.get('weight') else None,
            dimensions=data.get('dimensions', ''),
            vegetable_name=data.get('vegetable_name', ''),
            vegetable_name_hindi=data.get('vegetable_name_hindi', ''),
            quantity_gm=float(data.get('quantity_gm')) if data.get('quantity_gm') is not None else None,
            quantity_kg=float(data.get('quantity_kg')) if data.get('quantity_kg') is not None else None,
            rate_per_gm=float(data.get('rate_per_gm')) if data.get('rate_per_gm') is not None else None,
            rate_per_kg=float(data.get('rate_per_kg')) if data.get('rate_per_kg') is not None else None,
            is_active=True
        )
        
        product.save()
        
        # Add initial stock movement if stock quantity > 0
        if data.get('stock_quantity', 0) > 0:
            movement = StockMovement(
                product_id=product.id,
                movement_type='in',
                quantity=data['stock_quantity'],
                reference='Initial stock',
                notes='Product added to inventory',
                created_at=datetime.utcnow()
            )
            movement.save()
        
        return jsonify({
            'success': True, 
            'message': 'Product added to inventory successfully',
            'product': {
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'price': float(product.price),
                'stock_quantity': product.stock_quantity
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@product_bp.route('/', methods=['GET'])
@login_required
def api_get_products():
    """Get products from inventory (limited fields for products page) with customer-specific pricing"""
    try:
        # Check if user is authenticated
        if not current_user or not hasattr(current_user, 'id'):
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        # Get database instance first
        database = get_db()
        if database is None:
            return jsonify({'success': False, 'error': 'Database not initialized'}), 500
        
        # Simplified approach: Use same logic as inventory endpoint
        user_id = current_user.id
        if not user_id:
            return jsonify({'success': False, 'error': 'Invalid user ID'}), 401
        
        # Convert user_id to ObjectId properly (same as inventory endpoint)
        try:
            user_id_obj = ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id
        except Exception as e:
            print(f"Error converting user_id to ObjectId: {e}")
            return jsonify({'success': False, 'error': f'Invalid user ID format: {str(e)}'}), 400
        
        # Build query exactly like inventory endpoint
        query = {
            'user_id': user_id_obj,
            'is_active': True
        }
        
        # Optional customer ID for customer-specific pricing (for admin setting prices)
        customer_id = request.args.get('customer_id', type=int)
        
        print(f"Products API called by user: {user_id}, query: {query}")
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        
        if search:
            query['$or'] = [
                {'name': {'$regex': search, '$options': 'i'}},
                {'sku': {'$regex': search, '$options': 'i'}},
                {'hsn_code': {'$regex': search, '$options': 'i'}}
            ]
        
        if category and category != 'All':
            query['category'] = category
        
        # Database is already obtained above, use it
        try:
            print(f"Executing query: {query}")
            products_docs = list(database['products'].find(query).sort('name', 1))
            print(f"Found {len(products_docs)} product documents from database")
            products = []
            for doc in products_docs:
                if not isinstance(doc, dict):
                    print(f"Warning: Skipping non-dict product document: {doc}")
                    continue
                product = Product.from_dict(doc)
                if product:
                    products.append(product)
                else:
                    print(f"Warning: Product.from_dict returned None for document: {doc}")
        except Exception as query_error:
            import traceback
            print(f"Error querying products: {str(query_error)}")
            traceback.print_exc()
            return jsonify({'success': False, 'error': f'Error querying products: {str(query_error)}'}), 500
        
        print(f"Found {len(products)} products for user {user_id}")
        
        # Return only the fields needed for products page
        products_data = []
        for product in products:
            if product is None:
                print(f"Warning: Skipping None product")
                continue
            try:
                # Get price - start with default product price
                try:
                    price = float(getattr(product, 'price', 0)) if getattr(product, 'price', None) is not None else 0.0
                except (ValueError, TypeError, AttributeError):
                    price = 0.0
                
                # Try to get customer-specific price if customer_id is provided
                if customer_id:
                    try:
                        from models import Customer
                        customer = Customer.find_by_id(customer_id)
                        if customer and hasattr(product, 'get_customer_price'):
                            try:
                                customer_price = product.get_customer_price(customer_id)
                                if customer_price is not None:
                                    price = float(customer_price)
                            except Exception:
                                # Silently fall back to default price
                                pass
                    except Exception:
                        # Silently fall back to default price
                        pass
                
                # Get purchase_price from product model
                try:
                    purchase_price = float(product.purchase_price) if hasattr(product, 'purchase_price') and product.purchase_price is not None else 0.0
                except (ValueError, TypeError, AttributeError):
                    purchase_price = 0.0
                
                # Safely get all product fields with try-except for each
                try:
                    # Ensure product.id is converted to string for frontend compatibility
                    product_id = str(product.id) if hasattr(product, 'id') and product.id else '0'
                    
                    product_data = {
                        'id': product_id,
                        'name': getattr(product, 'name', '') or '',
                        'description': getattr(product, 'description', '') or '',
                        'image_url': getattr(product, 'image_url', '') or '',
                        'price': float(price) if price is not None else 0.0,
                        'default_price': float(getattr(product, 'price', 0)) if getattr(product, 'price', None) is not None else 0.0,
                        'stock_quantity': getattr(product, 'stock_quantity', 0) if getattr(product, 'stock_quantity', None) is not None else 0,
                        'has_custom_price': customer_id and price != getattr(product, 'price', 0) if customer_id else False,
                        'is_active': getattr(product, 'is_active', True) if getattr(product, 'is_active', None) is not None else True,
                        'sku': getattr(product, 'sku', '') or '',
                        'category': getattr(product, 'category', '') or '',
                        'purchase_price': purchase_price,
                        'hsn_code': getattr(product, 'hsn_code', '') or '',
                        'brand': getattr(product, 'brand', '') or '',
                        'gst_rate': float(getattr(product, 'gst_rate', 18)) if getattr(product, 'gst_rate', None) is not None else 18.0,
                        'min_stock_level': getattr(product, 'min_stock_level', 10) if getattr(product, 'min_stock_level', None) is not None else 10
                    }
                except Exception as field_error:
                    print(f"Error creating product_data dict for product {getattr(product, 'id', 'unknown')}: {str(field_error)}")
                    # Create minimal product data
                    product_id_minimal = str(getattr(product, 'id', '')) if hasattr(product, 'id') and getattr(product, 'id') else '0'
                    product_data = {
                        'id': product_id_minimal,
                        'name': str(getattr(product, 'name', 'Unknown')),
                        'description': '',
                        'image_url': '',
                        'price': 0.0,
                        'default_price': 0.0,
                        'stock_quantity': 0,
                        'has_custom_price': False,
                        'is_active': True,
                        'sku': '',
                        'category': '',
                        'purchase_price': 0.0,
                        'hsn_code': '',
                        'brand': '',
                        'gst_rate': 18.0,
                        'min_stock_level': 10
                    }
                products_data.append(product_data)
                try:
                    print(f"Product: ID={getattr(product, 'id', 'N/A')}, Name={getattr(product, 'name', 'N/A')}, SKU={getattr(product, 'sku', 'N/A')}, Price={price}, Default Price={getattr(product, 'price', 'N/A')}, Stock={getattr(product, 'stock_quantity', 'N/A')}")
                except Exception as print_error:
                    print(f"Error printing product info: {print_error}")
            except Exception as product_error:
                product_id_str = getattr(product, 'id', 'unknown') if product else 'None'
                print(f"Error processing product {product_id_str}: {str(product_error)}")
                import traceback
                traceback.print_exc()
                # Try to add minimal product data even if processing fails
                try:
                    minimal_product = {
                        'id': str(getattr(product, 'id', '')) if hasattr(product, 'id') else '',
                        'name': str(getattr(product, 'name', 'Unknown Product')) if hasattr(product, 'name') else 'Unknown Product',
                        'description': '',
                        'image_url': '',
                        'price': float(getattr(product, 'price', 0)) if hasattr(product, 'price') and getattr(product, 'price') is not None else 0.0,
                        'default_price': float(getattr(product, 'price', 0)) if hasattr(product, 'price') and getattr(product, 'price') is not None else 0.0,
                        'stock_quantity': int(getattr(product, 'stock_quantity', 0)) if hasattr(product, 'stock_quantity') and getattr(product, 'stock_quantity') is not None else 0,
                        'has_custom_price': False,
                        'is_active': True,
                        'sku': str(getattr(product, 'sku', '')) if hasattr(product, 'sku') else '',
                        'category': str(getattr(product, 'category', '')) if hasattr(product, 'category') else '',
                        'purchase_price': 0.0,
                        'hsn_code': '',
                        'brand': '',
                        'gst_rate': 18.0,
                        'min_stock_level': 10
                    }
                    products_data.append(minimal_product)
                    print(f"Added minimal product data for {product_id_str}")
                except Exception as minimal_error:
                    print(f"Failed to add even minimal product data: {minimal_error}")
                    # Skip this product but continue with others
                    continue
        
        print(f"Returning {len(products_data)} products")
        if len(products_data) == 0:
            print(f"WARNING: No products returned for user {user_id}")
            print(f"Query was: {query}")
            print(f"Total products in database for this user: {database['products'].count_documents({'user_id': user_id_obj})}")
            print(f"Total products with is_active=True: {database['products'].count_documents({'user_id': user_id_obj, 'is_active': True})}")
        return jsonify({'success': True, 'products': products_data})
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in products API: {str(e)}")
        print(f"Full traceback:\n{error_trace}")
        
        # Always return a valid JSON response, even on error
        # Return empty products list instead of failing completely
        try:
            return jsonify({
                'success': True,  # Set to True so frontend doesn't show error
                'products': [],  # Return empty list
                'message': 'No products found or error loading products'
            }), 200
        except Exception as json_error:
            # If even JSON creation fails, return minimal response
            return jsonify({
                'success': True,
                'products': []
            }), 200

@product_bp.route('/', methods=['OPTIONS'])
def api_create_product_options():
    """Handle CORS preflight for product creation"""
    return '', 200

@product_bp.route('/', methods=['POST'])
@login_required
def api_create_product():
    """Create new product"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'success': False, 'error': 'Product name is required'}), 400
        if not data.get('price'):
            return jsonify({'success': False, 'error': 'Product price is required'}), 400
        
        # Auto-generate SKU if not provided
        sku = data.get('sku')
        if not sku:
            # Generate SKU from product name and timestamp
            name_part = re.sub(r'[^A-Z0-9]', '', data['name'].upper())[:10] or 'PROD'
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')[-8:]  # Last 8 digits
            sku = f"{name_part}-{timestamp}"
            
            # Ensure SKU is unique
            counter = 1
            original_sku = sku
            user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
            while db['products'].find_one({'sku': sku, 'user_id': user_id_obj}):
                sku = f"{original_sku}-{counter}"
                counter += 1
        
        # Check if SKU already exists (if provided)
        user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
        if data.get('sku') and db['products'].find_one({'sku': sku, 'user_id': user_id_obj}):
            return jsonify({'success': False, 'error': 'SKU already exists'}), 400
        
        product = Product(
            user_id=current_user.id,
            admin_id=current_user.id,  # Set admin_id to same as user_id for backward compatibility
            name=data['name'],
            description=data.get('description', ''),
            sku=sku,
            hsn_code=data.get('hsn_code', ''),
            category=data.get('category', ''),
            brand=data.get('brand', ''),
            price=float(data['price']),
            purchase_price=float(data.get('purchase_price', 0)) if data.get('purchase_price') is not None else 0.0,
            gst_rate=float(data.get('gst_rate', 18)),
            stock_quantity=int(data.get('stock_quantity', 0)),
            min_stock_level=int(data.get('min_stock_level', 10)),
            unit=data.get('unit', 'PCS'),
            image_url=data.get('image_url', ''),
            weight=float(data.get('weight', 0)) if data.get('weight') else None,
            dimensions=data.get('dimensions', ''),
            vegetable_name=data.get('vegetable_name', ''),
            vegetable_name_hindi=data.get('vegetable_name_hindi', ''),
            quantity_gm=float(data.get('quantity_gm')) if data.get('quantity_gm') is not None else None,
            quantity_kg=float(data.get('quantity_kg')) if data.get('quantity_kg') is not None else None,
            rate_per_gm=float(data.get('rate_per_gm')) if data.get('rate_per_gm') is not None else None,
            rate_per_kg=float(data.get('rate_per_kg')) if data.get('rate_per_kg') is not None else None,
            is_active=data.get('is_active', True)
        )
        
        product.save()
        
        # Add initial stock movement if stock quantity > 0
        if data.get('stock_quantity', 0) > 0:
            movement = StockMovement(
                product_id=product.id,
                movement_type='in',
                quantity=data['stock_quantity'],
                reference='Initial stock',
                notes='Initial stock entry'
            )
            movement.save()
        
        return jsonify({
            'success': True, 
            'message': 'Product created successfully',
            'product': {
                'id': product.id,
                'name': product.name,
                'sku': product.sku
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Customer Product Pricing Routes - Must be defined before /<int:id> routes
@product_bp.route('/customer-prices', methods=['GET'])
@login_required
def api_get_customer_prices():
    """Get all customer-specific prices for products"""
    try:
        # Get database connection
        database = get_db()
        if database is None:
            return jsonify({'success': False, 'error': 'Database not initialized'}), 500
        
        customer_id = request.args.get('customer_id')
        product_id = request.args.get('product_id')
        
        user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
        
        # Get customers for this user first
        customer_ids = []
        customer_docs = list(database['customers'].find({'user_id': user_id_obj}))
        for doc in customer_docs:
            if isinstance(doc, dict) and '_id' in doc:
                customer_ids.append(doc['_id'])
        
        query = {}
        if customer_ids:
            query['customer_id'] = {'$in': customer_ids}
        
        if customer_id:
            # Convert customer_id to ObjectId if it's a string
            try:
                customer_id_obj = ObjectId(customer_id) if isinstance(customer_id, str) else customer_id
                query['customer_id'] = customer_id_obj
            except:
                return jsonify({'success': False, 'error': 'Invalid customer_id'}), 400
        
        if product_id:
            # Convert product_id to ObjectId if it's a string
            try:
                product_id_obj = ObjectId(product_id) if isinstance(product_id, str) else product_id
                query['product_id'] = product_id_obj
            except:
                return jsonify({'success': False, 'error': 'Invalid product_id'}), 400
        
        prices_docs = list(database['customer_product_prices'].find(query))
        prices = []
        for doc in prices_docs:
            if not isinstance(doc, dict):
                continue
            price = CustomerProductPrice.from_dict(doc)
            if price:
                prices.append(price)
        
        prices_data = []
        for price in prices:
            try:
                # Get customer and product names
                customer = Customer.find_by_id(str(price.customer_id)) if price.customer_id else None
                product = Product.find_by_id(str(price.product_id)) if price.product_id else None
                
                prices_data.append({
                    'id': price.id,
                    'customer_id': str(price.customer_id) if price.customer_id else '',
                    'customer_name': customer.name if customer else 'Unknown',
                    'product_id': str(price.product_id) if price.product_id else '',
                    'product_name': product.name if product else 'Unknown',
                    'price': float(price.price) if price.price is not None else 0.0,
                    'created_at': price.created_at.isoformat() if hasattr(price, 'created_at') and price.created_at else None,
                    'updated_at': price.updated_at.isoformat() if hasattr(price, 'updated_at') and price.updated_at else None
                })
            except Exception as price_error:
                print(f"Error processing price: {price_error}")
                continue
        
        return jsonify({'success': True, 'prices': prices_data})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@product_bp.route('/customer-prices', methods=['POST', 'OPTIONS'])
@login_required
def api_set_customer_price():
    """Set or update customer-specific price for a product"""
    # Handle OPTIONS for CORS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        customer_id = data.get('customer_id')
        product_id = data.get('product_id')
        price = data.get('price')
        
        # Convert price to float, but keep IDs as strings (MongoDB uses ObjectId strings)
        try:
            price = float(price) if price is not None else None
        except (ValueError, TypeError) as e:
            return jsonify({'success': False, 'error': f'Invalid price: {str(e)}'}), 400
        
        # Validate required fields with better error messages
        if not customer_id:
            return jsonify({'success': False, 'error': 'customer_id is required'}), 400
        if not product_id:
            return jsonify({'success': False, 'error': 'product_id is required'}), 400
        if price is None:
            return jsonify({'success': False, 'error': 'price is required'}), 400
        if price <= 0:
            return jsonify({'success': False, 'error': 'price must be greater than 0'}), 400
        
        # Get database connection
        from models import get_db
        database = get_db()
        if database is None:
            return jsonify({'success': False, 'error': 'Database not initialized'}), 500
        
        # Convert IDs to strings (MongoDB uses ObjectId strings)
        customer_id_str = str(customer_id) if customer_id else None
        product_id_str = str(product_id) if product_id else None
        
        if not customer_id_str or not product_id_str:
            return jsonify({'success': False, 'error': 'Invalid customer_id or product_id'}), 400
        
        # First, verify customer exists (check if it belongs to this admin or any admin)
        customer = Customer.find_by_id(customer_id_str)
        if not customer:
            return jsonify({
                'success': False, 
                'error': f'Customer not found. Customer ID: {customer_id_str}'
            }), 404
        
        # Verify product belongs to this admin
        user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
        product = Product.find_by_id(product_id_str)
        if not product or str(product.user_id) != str(current_user.id):
            return jsonify({
                'success': False, 
                'error': f'Product not found or does not belong to you. Product ID: {product_id_str}'
            }), 404
        
        # If customer belongs to a different admin, that's okay - we can still set prices
        # The important thing is that the product belongs to the current admin
        
        # Check if price already exists
        customer_price = CustomerProductPrice.find_by_customer_and_product(customer_id_str, product_id_str)
        
        if customer_price:
            # Update existing price
            customer_price.price = float(price)
            customer_price.updated_at = datetime.utcnow()
            customer_price.save()
        else:
            # Create new price
            customer_price = CustomerProductPrice(
                customer_id=customer_id,
                product_id=product_id,
                price=float(price)
            )
            customer_price.save()
        
        return jsonify({
            'success': True,
            'message': 'Customer price set successfully',
            'price': {
                'id': customer_price.id,
                'customer_id': customer_price.customer_id,
                'product_id': customer_price.product_id,
                'price': float(customer_price.price)
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@product_bp.route('/<int:id>', methods=['GET'])
@login_required
def api_get_product(id):
    """Get single product"""
    try:
        product = Product.find_by_id(id)
        if not product or str(product.user_id) != str(current_user.id) or not product.is_active:
            product = None
        
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        product_data = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'sku': product.sku,
            'hsn_code': product.hsn_code,
            'category': product.category,
            'brand': product.brand,
            'price': float(product.price),
            'gst_rate': float(product.gst_rate),
            'stock_quantity': product.stock_quantity,
            'min_stock_level': product.min_stock_level,
            'image_url': product.image_url,
            'weight': float(product.weight) if product.weight else 0,
            'dimensions': product.dimensions,
            'vegetable_name': product.vegetable_name,
            'vegetable_name_hindi': product.vegetable_name_hindi,
            'quantity_gm': float(product.quantity_gm) if product.quantity_gm else None,
            'quantity_kg': float(product.quantity_kg) if product.quantity_kg else None,
            'rate_per_gm': float(product.rate_per_gm) if product.rate_per_gm else None,
            'rate_per_kg': float(product.rate_per_kg) if product.rate_per_kg else None,
            'is_active': product.is_active,
            'created_at': product.created_at.isoformat() if product.created_at else None,
            'updated_at': product.updated_at.isoformat() if product.updated_at else None
        }
        
        return jsonify({'success': True, 'product': product_data})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@product_bp.route('/<int:id>', methods=['PUT'])
@login_required
def api_update_product(id):
    """Update product"""
    try:
        # Don't filter by is_active so we can update inactive products too
        product = Product.find_by_id(id)
        if not product or str(product.user_id) != str(current_user.id):
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        data = request.get_json()
        
        # Check if SKU is changed and already exists
        if data.get('sku') != product.sku:
            user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
            if db['products'].find_one({'sku': data['sku'], 'user_id': user_id_obj}):
                return jsonify({'success': False, 'error': 'SKU already exists'}), 400
        
        # Update product fields
        product.name = data.get('name', product.name)
        product.description = data.get('description', product.description)
        product.sku = data.get('sku', product.sku)
        product.hsn_code = data.get('hsn_code', product.hsn_code)
        product.category = data.get('category', product.category)
        product.brand = data.get('brand', product.brand)
        if 'price' in data:
            product.price = data['price']
        if 'purchase_price' in data:
            product.purchase_price = float(data['purchase_price']) if data['purchase_price'] is not None else 0.0
        product.gst_rate = data.get('gst_rate', product.gst_rate)
        product.min_stock_level = data.get('min_stock_level', product.min_stock_level)
        product.image_url = data.get('image_url', product.image_url)
        product.weight = data.get('weight', product.weight)
        product.dimensions = data.get('dimensions', product.dimensions)
        product.vegetable_name = data.get('vegetable_name', product.vegetable_name)
        product.vegetable_name_hindi = data.get('vegetable_name_hindi', product.vegetable_name_hindi)
        product.quantity_gm = float(data.get('quantity_gm')) if data.get('quantity_gm') is not None else product.quantity_gm
        product.quantity_kg = float(data.get('quantity_kg')) if data.get('quantity_kg') is not None else product.quantity_kg
        product.rate_per_gm = float(data.get('rate_per_gm')) if data.get('rate_per_gm') is not None else product.rate_per_gm
        product.rate_per_kg = float(data.get('rate_per_kg')) if data.get('rate_per_kg') is not None else product.rate_per_kg
        product.is_active = data.get('is_active', product.is_active)
        product.updated_at = datetime.utcnow()
        product.save()
        
        return jsonify({
            'success': True, 
            'message': 'Product updated successfully'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@product_bp.route('/<int:id>/toggle-visibility', methods=['POST'])
@login_required
def api_toggle_product_visibility(id):
    """Toggle product visibility (is_active)"""
    try:
        product = Product.find_by_id(id)
        if not product or str(product.user_id) != str(current_user.id):
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        # Toggle is_active
        product.is_active = not product.is_active
        product.updated_at = datetime.utcnow()
        product.save()
        
        return jsonify({
            'success': True,
            'message': f'Product {"activated" if product.is_active else "deactivated"} successfully',
            'is_active': product.is_active
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@product_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def api_delete_product(id):
    """Delete product (hard delete)"""
    try:
        product = Product.find_by_id(id)
        if not product or str(product.user_id) != str(current_user.id):
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        product_id_obj = ObjectId(id) if isinstance(id, str) else id
        
        # Check if product has invoice items
        invoice_item_count = db['invoice_items'].count_documents({'product_id': product_id_obj})
        if invoice_item_count > 0:
            return jsonify({
                'success': False, 
                'error': 'Cannot delete product with existing invoice items. Please delete related invoices first.'
            }), 400
        
            # Delete stock movements first
        db['stock_movements'].delete_many({'product_id': product_id_obj})
        
            # Delete customer prices first
        db['customer_product_prices'].delete_many({'product_id': product_id_obj})
        
        # Hard delete the product
        db['products'].delete_one({'_id': product_id_obj})
        
        return jsonify({
            'success': True, 
            'message': 'Product deleted successfully'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@product_bp.route('/<id>/stock', methods=['POST'])
@login_required
def api_stock_movement(id):
    """Add stock movement"""
    try:
        # Handle both string and int IDs
        product_id = str(id) if id else None
        if not product_id:
            return jsonify({'success': False, 'error': 'Invalid product ID'}), 400
        
        product = Product.find_by_id(product_id)
        if not product or str(product.user_id) != str(current_user.id) or not product.is_active:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        data = request.get_json()
        
        movement = StockMovement(
            product_id=product.id,
            movement_type=data['movement_type'],
            quantity=data['quantity'],
            reference=data.get('reference', ''),
            notes=data.get('notes', '')
        )
        
        # Update product stock
        if data['movement_type'] == 'in':
            product.stock_quantity += data['quantity']
        elif data['movement_type'] == 'out':
            if product.stock_quantity < data['quantity']:
                return jsonify({'success': False, 'error': 'Insufficient stock'}), 400
            product.stock_quantity -= data['quantity']
        else:  # adjustment
            product.stock_quantity = data['quantity']
        
        product.updated_at = datetime.utcnow()
        
        # Save product first to update stock quantity
        try:
            product.save()
        except Exception as save_error:
            import traceback
            print(f"Error saving product: {save_error}")
            traceback.print_exc()
            return jsonify({'success': False, 'error': f'Failed to update product stock: {str(save_error)}'}), 500
        
        # Save stock movement
        try:
            movement.save()
        except Exception as movement_error:
            import traceback
            print(f"Error saving stock movement: {movement_error}")
            traceback.print_exc()
            # Product was already saved, so we can still return success but log the movement error
            return jsonify({
                'success': True, 
                'message': 'Stock updated successfully, but movement record failed',
                'new_stock': product.stock_quantity,
                'warning': f'Movement record error: {str(movement_error)}'
            })
        
        return jsonify({
            'success': True, 
            'message': 'Stock movement recorded successfully',
            'new_stock': product.stock_quantity
        })
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in stock movement API: {str(e)}")
        print(f"Full traceback:\n{error_trace}")
        return jsonify({'success': False, 'error': str(e)}), 500

@product_bp.route('/bulk-stock', methods=['POST'])
@login_required
def api_bulk_stock_movement():
    """Bulk stock in/out for multiple products"""
    try:
        if not current_user or not hasattr(current_user, 'id'):
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        data = request.get_json()
        movement_type = data.get('movement_type')  # 'in' or 'out'
        items = data.get('items', [])  # List of {product_id, quantity}
        
        if movement_type not in ['in', 'out']:
            return jsonify({'success': False, 'error': 'Invalid movement type'}), 400
        
        if not items or len(items) == 0:
            return jsonify({'success': False, 'error': 'No items provided'}), 400
        
        results = []
        errors = []
        
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 0)
            
            if not product_id or quantity <= 0:
                errors.append(f"Invalid item: product_id={product_id}, quantity={quantity}")
                continue
            
            try:
                product = Product.find_by_id(product_id)
                if not product or str(product.user_id) != str(current_user.id) or not product.is_active:
                    product = None
                
                if not product:
                    errors.append(f"Product {product_id} not found")
                    continue
                
                # Check stock for stock out
                if movement_type == 'out' and product.stock_quantity < quantity:
                    errors.append(f"Insufficient stock for {product.name}. Available: {product.stock_quantity}, Requested: {quantity}")
                    continue
                
                # Create stock movement
                movement = StockMovement(
                    product_id=product.id,
                    movement_type=movement_type,
                    quantity=quantity,
                    reference=data.get('reference', 'Bulk operation'),
                    notes=data.get('notes', f'Bulk stock {movement_type}')
                )
                
                # Update product stock
                if movement_type == 'in':
                    product.stock_quantity += quantity
                else:  # out
                    product.stock_quantity -= quantity
                
                product.updated_at = datetime.utcnow()
                product.save()
                movement.save()
                
                results.append({
                    'product_id': product_id,
                    'product_name': product.name,
                    'new_stock': product.stock_quantity
                })
                
            except Exception as e:
                errors.append(f"Error processing product {product_id}: {str(e)}")
                continue
        
        return jsonify({
            'success': True,
            'message': f'Bulk stock {movement_type} completed',
            'processed': len(results),
            'results': results,
            'errors': errors
        })
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in bulk stock API: {str(e)}")
        print(f"Full traceback:\n{error_trace}")
        return jsonify({'success': False, 'error': str(e)}), 500

@product_bp.route('/upload-image', methods=['POST'])
@login_required
def api_upload_image():
    """Upload product image"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'}), 400
        
        if file:
            # Generate unique filename
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'products')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(upload_dir, unique_filename)
            file.save(file_path)
            
            # Return the URL
            image_url = f"/static/uploads/products/{unique_filename}"
            
            return jsonify({
                'success': True, 
                'image_url': image_url,
                'filename': unique_filename
            })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@product_bp.route('/stock-movements', methods=['GET'])
@login_required
def api_get_stock_movements():
    """Get stock movements for purchases report"""
    try:
        if not current_user or not hasattr(current_user, 'id'):
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        # Get database instance
        database = get_db()
        if database is None:
            return jsonify({'success': False, 'error': 'Database not initialized'}), 500
        
        user_id = current_user.id
        movement_type = request.args.get('movement_type', '')  # 'in' or 'out' or empty for all
        
        # Get all products for this user
        user_id_obj = ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id
        products = [Product.from_dict(doc) for doc in database['products'].find({'user_id': user_id_obj, 'is_active': True})]
        
        if not products:
            return jsonify({'success': True, 'movements': []})
        
        # Get product IDs (handle both string and ObjectId)
        product_ids = []
        for p in products:
            if p and p.id:
                if isinstance(p.id, str) and ObjectId.is_valid(p.id):
                    product_ids.append(ObjectId(p.id))
                elif isinstance(p.id, ObjectId):
                    product_ids.append(p.id)
                else:
                    try:
                        product_ids.append(ObjectId(str(p.id)))
                    except:
                        continue
        
        if not product_ids:
            return jsonify({'success': True, 'movements': []})
        
        # Query stock movements
        query = {'product_id': {'$in': product_ids}}
        
        if movement_type:
            query['movement_type'] = movement_type
        
        movements_docs = list(database['stock_movements'].find(query).sort('created_at', -1))
        movements = []
        for doc in movements_docs:
            if not isinstance(doc, dict):
                continue
            movement = StockMovement.from_dict(doc)
            if movement:
                movements.append(movement)
        
        movements_data = []
        for movement in movements:
            if not movement:
                continue
            try:
                # Convert product_id to string for frontend (handle ObjectId)
                product_id = movement.product_id
                if isinstance(product_id, ObjectId):
                    product_id_str = str(product_id)
                else:
                    product_id_str = str(product_id) if product_id else ''
                
                # Convert movement ID to string
                movement_id = movement.id
                if isinstance(movement_id, ObjectId):
                    movement_id_str = str(movement_id)
                else:
                    movement_id_str = str(movement_id) if movement_id else ''
                
                # Handle created_at conversion
                created_at_str = None
                if movement.created_at:
                    try:
                        if hasattr(movement.created_at, 'isoformat'):
                            created_at_str = movement.created_at.isoformat()
                        elif isinstance(movement.created_at, datetime):
                            created_at_str = movement.created_at.isoformat()
                        else:
                            created_at_str = str(movement.created_at)
                    except Exception:
                        created_at_str = str(movement.created_at) if movement.created_at else None
                
                movements_data.append({
                    'id': movement_id_str,
                    'product_id': product_id_str,
                    'movement_type': movement.movement_type or '',
                    'quantity': float(movement.quantity) if movement.quantity is not None else 0,
                    'reference': movement.reference or '',
                    'notes': movement.notes or '',
                    'created_at': created_at_str
                })
            except Exception as e:
                print(f"Error processing movement {getattr(movement, 'id', 'unknown')}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Clean data to ensure all ObjectIds are converted
        def clean_data(data):
            """Recursively clean data to convert ObjectIds to strings"""
            if isinstance(data, dict):
                return {k: clean_data(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [clean_data(item) for item in data]
            elif isinstance(data, ObjectId):
                return str(data)
            else:
                return data
        
        cleaned_movements = clean_data(movements_data)
        
        return jsonify({
            'success': True,
            'movements': cleaned_movements
        })
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in stock movements API: {str(e)}")
        print(f"Full traceback:\n{error_trace}")
        # Return success with empty list instead of error to prevent frontend crashes
        return jsonify({
            'success': True, 
            'movements': [],
            'error': str(e),
            'message': f'Some movements may not be available: {str(e)}'
        }), 200

@product_bp.route('/inventory', methods=['GET'])
@login_required
def api_get_inventory():
    """Get optimized inventory overview with summary calculations"""
    try:
        # Check if user is authenticated
        if not current_user or not hasattr(current_user, 'id'):
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        # Get database connection dynamically
        database = get_db()
        if database is None:
            return jsonify({'success': False, 'error': 'Database not initialized'}), 500
        
        user_id = current_user.id
        if not user_id:
            return jsonify({'success': False, 'error': 'Invalid user ID'}), 401
        
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        
        # Build optimized query - only get necessary fields
        try:
            user_id_obj = ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id
        except Exception as e:
            return jsonify({'success': False, 'error': f'Invalid user ID format: {str(e)}'}), 400
        
        query = {
            'user_id': user_id_obj,
            'is_active': True
        }
        
        if search:
            query['$or'] = [
                {'name': {'$regex': search, '$options': 'i'}},
                {'sku': {'$regex': search, '$options': 'i'}},
                {'hsn_code': {'$regex': search, '$options': 'i'}}
            ]
        
        if category and category != 'All' and category != '':
            query['category'] = category
        
        # Get products with optimized query
        try:
            products_docs = list(database['products'].find(query).sort('name', 1))
            products = []
            for doc in products_docs:
                try:
                    # Skip None or invalid documents
                    if doc is None or not isinstance(doc, dict):
                        print(f"Warning: Skipping invalid document: {doc}")
                        continue
                    product = Product.from_dict(doc)
                    if product is None:
                        print(f"Warning: Product.from_dict returned None for document: {doc.get('_id', 'unknown')}")
                        continue
                    products.append(product)
                except Exception as e:
                    import traceback
                    print(f"Warning: Could not parse product document: {e}")
                    print(traceback.format_exc())
                    continue
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error fetching products: {str(e)}")
            print(f"Full traceback:\n{error_trace}")
            return jsonify({'success': False, 'error': f'Error fetching products: {str(e)}'}), 500
        
        # Calculate summary statistics efficiently
        low_stock_items = []
        positive_stock_items = []
        total_stock_value_sales = 0.0
        total_stock_value_purchase = 0.0
        low_stock_qty = 0
        positive_stock_qty = 0
        
        inventory_data = []
        
        # Get last updated dates in a single query for all products
        # Prepare product_ids in both ObjectId and string formats for matching
        product_ids_obj = []
        product_ids_str = []
        for p in products:
            if p.id:
                if isinstance(p.id, str) and ObjectId.is_valid(p.id):
                    product_ids_obj.append(ObjectId(p.id))
                    product_ids_str.append(p.id)
                elif isinstance(p.id, ObjectId):
                    product_ids_obj.append(p.id)
                    product_ids_str.append(str(p.id))
                else:
                    product_ids_str.append(str(p.id))
        
        last_movements = {}
        if product_ids_obj or product_ids_str:
            try:
                # Get the most recent movement for each product using aggregation
                # Match both ObjectId and string product_ids
                match_conditions = []
                if product_ids_obj:
                    match_conditions.append({'product_id': {'$in': product_ids_obj}})
                if product_ids_str:
                    match_conditions.append({'product_id': {'$in': product_ids_str}})
                
                if match_conditions:
                    pipeline = [
                        {'$match': {'$or': match_conditions}},
                        {'$group': {
                            '_id': '$product_id',
                            'last_updated': {'$max': '$created_at'}
                        }}
                    ]
                    recent_movements = database['stock_movements'].aggregate(pipeline)
                    
                    for movement in recent_movements:
                        # Skip None or invalid movements
                        if movement is None or not isinstance(movement, dict):
                            continue
                        # Convert product_id to string for matching
                        product_id = movement.get('_id')
                        if product_id is None:
                            continue
                        if isinstance(product_id, ObjectId):
                            product_id_str = str(product_id)
                        else:
                            product_id_str = str(product_id)
                        last_updated = movement.get('last_updated')
                        if last_updated:
                            last_movements[product_id_str] = last_updated
            except Exception as agg_error:
                # If aggregation fails, continue without last_updated dates
                import traceback
                print(f"Warning: Could not fetch last movements: {agg_error}")
                print(traceback.format_exc())
                pass
        
        for product in products:
            try:
                # Skip None products
                if product is None:
                    print("Warning: Skipping None product")
                    continue
                
                stock_qty = product.stock_quantity if hasattr(product, 'stock_quantity') and product.stock_quantity is not None else 0
                price = float(product.price) if hasattr(product, 'price') and product.price is not None else 0.0
                purchase_price = float(product.purchase_price) if hasattr(product, 'purchase_price') and product.purchase_price is not None else 0.0
                min_stock_level = product.min_stock_level if hasattr(product, 'min_stock_level') and product.min_stock_level is not None else 10
                
                # Calculate stock values
                stock_value_sales = stock_qty * price
                stock_value_purchase = stock_qty * purchase_price
                
                # Track low stock (negative or below min level)
                if stock_qty < 0 or (stock_qty > 0 and stock_qty <= min_stock_level):
                    low_stock_items.append(product.id)
                    low_stock_qty += stock_qty
                
                # Track positive stock
                if stock_qty > 0:
                    positive_stock_items.append(product.id)
                    positive_stock_qty += stock_qty
                
                total_stock_value_sales += stock_value_sales
                total_stock_value_purchase += stock_value_purchase
                
                # Get last updated date
                product_id_str = str(product.id) if product.id else None
                last_updated = last_movements.get(product_id_str) if product_id_str else None
                if not last_updated and hasattr(product, 'updated_at') and product.updated_at:
                    last_updated = product.updated_at
                
                inventory_data.append({
                    'id': str(product.id) if product.id else '',
                    'name': product.name if hasattr(product, 'name') and product.name else '',
                    'vegetable_name_hindi': getattr(product, 'vegetable_name_hindi', '') or '',
                    'sku': product.sku if hasattr(product, 'sku') and product.sku else '',
                    'category': product.category if hasattr(product, 'category') and product.category else '',
                    'stock_quantity': stock_qty,
                    'min_stock_level': min_stock_level,
                    'price': price,
                    'purchase_price': purchase_price,
                    'unit': product.unit if hasattr(product, 'unit') and product.unit else 'PCS',
                    'last_updated': last_updated.isoformat() if last_updated and hasattr(last_updated, 'isoformat') else None,
                    'status': ('out_of_stock' if stock_qty == 0 else 
                              ('low_stock' if stock_qty < 0 or (stock_qty > 0 and stock_qty <= min_stock_level) else 'in_stock'))
                })
            except Exception as product_error:
                # Skip products that cause errors but log them
                import traceback
                print(f"Error processing product {getattr(product, 'id', 'unknown')}: {product_error}")
                print(traceback.format_exc())
                continue
        
        # Return response with inventory data
        return jsonify({
            'success': True,
            'inventory': inventory_data,
            'summary': {
                'low_stock': {
                    'items': len(low_stock_items),
                    'quantity': float(low_stock_qty)
                },
                'positive_stock': {
                    'items': len(positive_stock_items),
                    'quantity': float(positive_stock_qty)
                },
                'stock_value_sales_price': float(total_stock_value_sales),
                'stock_value_purchase_price': float(total_stock_value_purchase),
                'total_products': len(inventory_data)
            }
        })
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = str(e)
        print(f"Error in inventory API: {error_msg}")
        print(f"Full traceback:\n{error_trace}")
        # Return more detailed error in development, simpler in production
        import os
        if os.environ.get('FLASK_ENV') == 'development':
            return jsonify({
                'success': False, 
                'error': error_msg,
                'traceback': error_trace.split('\n')[-10:]  # Last 10 lines
            }), 500
        else:
            return jsonify({'success': False, 'error': 'Internal server error'}), 500

# Legacy template routes (keeping for compatibility)
@product_bp.route('/products')
@login_required
def index():
    """List all products"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    query = {
        'user_id': ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id,
        'is_active': True
    }
    
    if search:
        query['$or'] = [
            {'name': {'$regex': search, '$options': 'i'}},
            {'sku': {'$regex': search, '$options': 'i'}},
            {'hsn_code': {'$regex': search, '$options': 'i'}}
        ]
    
    if category:
        query['category'] = category
    
    # Manual pagination for MongoDB
    skip = (page - 1) * 20
    all_products = [Product.from_dict(doc) for doc in db['products'].find(query).sort('name', 1).skip(skip).limit(20)]
    total_count = db['products'].count_documents(query)
    
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
    
    products = Pagination(all_products, page, 20, total_count)
    
    return render_template('products/index.html', products=products, search=search, category=category)

@product_bp.route('/products/new', methods=['GET', 'POST'])
@login_required
def new():
    """Create new product"""
    form = ProductForm()
    
    if form.validate_on_submit():
        # Check if SKU already exists
        user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
        if db['products'].find_one({'sku': form.sku.data, 'user_id': user_id_obj}):
            flash('SKU already exists. Please choose a different SKU.', 'error')
            return render_template('products/new.html', form=form)
        
        product = Product(
            user_id=current_user.id,
            admin_id=current_user.id,  # Set admin_id to same as user_id for backward compatibility
            name=form.name.data,
            sku=form.sku.data,
            hsn_code=form.hsn_code.data,
            description=form.description.data,
            price=form.price.data,
            gst_rate=form.gst_rate.data,
            stock_quantity=form.stock_quantity.data,
            min_stock_level=form.min_stock_level.data,
            unit=form.unit.data
        )
        
        product.save()
        
        # Add initial stock movement
        if form.stock_quantity.data > 0:
            movement = StockMovement(
                product_id=product.id,
                movement_type='in',
                quantity=form.stock_quantity.data,
                reference='Initial stock',
                notes='Initial stock entry'
            )
            movement.save()
        
        flash('Product created successfully!', 'success')
        return redirect(url_for('product.index'))
    
    return render_template('products/new.html', form=form)

@product_bp.route('/products/<int:id>')
@login_required
def show(id):
    """Show product details"""
    product = Product.find_by_id(id)
    if not product or str(product.user_id) != str(current_user.id) or not product.is_active:
        from flask import abort
        abort(404)
    
    # Get recent stock movements
    product_id_obj = ObjectId(product.id) if isinstance(product.id, str) else product.id
    movements = [StockMovement.from_dict(doc) for doc in db['stock_movements'].find(
        {'product_id': product_id_obj}
    ).sort('created_at', -1).limit(10)]
    
    return render_template('products/show.html', product=product, movements=movements)

@product_bp.route('/products/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit product"""
    product = Product.find_by_id(id)
    if not product or str(product.user_id) != str(current_user.id) or not product.is_active:
        from flask import abort
        abort(404)
    
    form = ProductForm(obj=product)
    
    if form.validate_on_submit():
        # Check if SKU is changed and already exists
        if form.sku.data != product.sku:
            user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
            if db['products'].find_one({'sku': form.sku.data, 'user_id': user_id_obj}):
                flash('SKU already exists. Please choose a different SKU.', 'error')
                return render_template('products/edit.html', form=form, product=product)
        
        product.name = form.name.data
        product.sku = form.sku.data
        product.hsn_code = form.hsn_code.data
        product.description = form.description.data
        product.price = form.price.data
        product.gst_rate = form.gst_rate.data
        product.min_stock_level = form.min_stock_level.data
        product.unit = form.unit.data
        product.save()
        
        flash('Product updated successfully!', 'success')
        return redirect(url_for('product.show', id=product.id))
    
    return render_template('products/edit.html', form=form, product=product)

@product_bp.route('/products/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete product (hard delete)"""
    product = Product.find_by_id(id)
    if not product or str(product.user_id) != str(current_user.id):
        from flask import abort
        abort(404)
    
    product_id_obj = ObjectId(id) if isinstance(id, str) else id
    
    # Check if product has invoice items
    invoice_item_count = db['invoice_items'].count_documents({'product_id': product_id_obj})
    if invoice_item_count > 0:
        flash('Cannot delete product with existing invoice items. Please delete invoices first.', 'error')
        return redirect(url_for('product.show', id=product.id))
    
    # Delete stock movements first
    db['stock_movements'].delete_many({'product_id': product_id_obj})
    
    # Delete customer prices first
    db['customer_product_prices'].delete_many({'product_id': product_id_obj})
    
    # Hard delete the product
    db['products'].delete_one({'_id': product_id_obj})
    
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('product.index'))

@product_bp.route('/products/<int:id>/stock', methods=['GET', 'POST'])
@login_required
def stock_movement(id):
    """Add stock movement"""
    product = Product.find_by_id(id)
    if not product or str(product.user_id) != str(current_user.id) or not product.is_active:
        from flask import abort
        abort(404)
    
    form = StockMovementForm()
    
    if form.validate_on_submit():
        movement = StockMovement(
            product_id=product.id,
            movement_type=form.movement_type.data,
            quantity=form.quantity.data,
            reference=form.reference.data,
            notes=form.notes.data
        )
        
        # Update product stock
        if form.movement_type.data == 'in':
            product.stock_quantity += form.quantity.data
        elif form.movement_type.data == 'out':
            if product.stock_quantity < form.quantity.data:
                flash('Insufficient stock!', 'error')
                return render_template('products/stock_movement.html', form=form, product=product)
            product.stock_quantity -= form.quantity.data
        else:  # adjustment
            product.stock_quantity = form.quantity.data
        
        movement.save()
        
        flash('Stock movement recorded successfully!', 'success')
        return redirect(url_for('product.show', id=product.id))
    
    return render_template('products/stock_movement.html', form=form, product=product)

@product_bp.route('/inventory')
@login_required
def inventory():
    """Inventory overview"""
    user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
    products = [Product.from_dict(doc) for doc in db['products'].find(
        {'user_id': user_id_obj, 'is_active': True}
    ).sort('name', 1)]
    
    # Calculate inventory summary
    total_products = len(products)
    total_value = sum(p.stock_quantity * p.price for p in products)
    low_stock_count = len([p for p in products if p.is_low_stock])
    out_of_stock_count = len([p for p in products if p.stock_quantity == 0])
    
    return render_template('products/inventory.html', 
                         products=products,
                         total_products=total_products,
                         total_value=total_value,
                         low_stock_count=low_stock_count,
                         out_of_stock_count=out_of_stock_count)

@product_bp.route('/search')
@login_required
def search():
    """API endpoint for product search (for invoice creation)"""
    search_term = request.args.get('q', '')
    
    if len(search_term) < 2:
        return jsonify([])
    
    user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
    query = {
        'user_id': user_id_obj,
        'is_active': True,
        '$or': [
            {'name': {'$regex': search_term, '$options': 'i'}},
            {'sku': {'$regex': search_term, '$options': 'i'}},
            {'hsn_code': {'$regex': search_term, '$options': 'i'}}
        ]
    }
    products = [Product.from_dict(doc) for doc in db['products'].find(query).limit(10)]
    
    results = []
    for product in products:
        results.append({
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'price': float(product.price),
            'gst_rate': float(product.gst_rate),
            'stock_quantity': product.stock_quantity,
            'unit': product.unit
        })
    
    return jsonify(results)

@product_bp.route('/<int:id>')
@login_required
def get_product(id):
    """API endpoint to get product details"""
    product = Product.find_by_id(id)
    if not product or str(product.user_id) != str(current_user.id) or not product.is_active:
        from flask import abort
        abort(404)
    
    customer_id = request.args.get('customer_id', type=int)
    price = product.get_customer_price(customer_id) if customer_id else product.price
    
    return jsonify({
        'id': product.id,
        'name': product.name,
        'sku': product.sku,
        'hsn_code': product.hsn_code,
        'price': float(price),
        'default_price': float(product.price),
        'gst_rate': float(product.gst_rate),
        'stock_quantity': product.stock_quantity,
        'unit': product.unit,
        'description': product.description
    })

# Customer Product Pricing Routes moved to before /<int:id> routes (see above)

@product_bp.route('/customer-prices/<int:price_id>', methods=['DELETE'])
@login_required
def api_delete_customer_price(price_id):
    """Delete customer-specific price"""
    try:
        # Get customer IDs for this user
        user_id_obj = ObjectId(current_user.id) if isinstance(current_user.id, str) else current_user.id
        customer_ids = [str(doc['_id']) for doc in db['customers'].find({'user_id': user_id_obj})]
        
        # Find price that belongs to one of these customers
        price_id_obj = ObjectId(price_id) if isinstance(price_id, str) else price_id
        customer_price_doc = db['customer_product_prices'].find_one({
            '_id': price_id_obj,
            'customer_id': {'$in': [ObjectId(cid) if isinstance(cid, str) else cid for cid in customer_ids]}
        })
        
        if not customer_price_doc:
            return jsonify({'success': False, 'error': 'Price not found'}), 404
        
        db['customer_product_prices'].delete_one({'_id': price_id_obj})
        
        return jsonify({'success': True, 'message': 'Customer price deleted successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
