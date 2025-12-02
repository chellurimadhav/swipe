from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime

# Create Flask app
app = Flask(__name__)

# Enable CORS with credentials support
CORS(app, 
     origins=["*"],
     supports_credentials=True,
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "Origin", "Accept", "X-Requested-With"],
     expose_headers=["Content-Type", "Authorization"],
     max_age=86400
)

# Simple in-memory storage for demo
products = [
    {
        'id': 1,
        'name': 'Sample Product 1',
        'description': 'This is a sample product for testing',
        'price': 100.0,
        'stock_quantity': 50,
        'created_at': datetime.utcnow().isoformat()
    },
    {
        'id': 2,
        'name': 'Sample Product 2',
        'description': 'Another sample product for testing',
        'price': 200.0,
        'stock_quantity': 30,
        'created_at': datetime.utcnow().isoformat()
    }
]
customers = [
    {
        'id': 1,
        'name': 'John Doe',
        'email': 'john.doe@example.com',
        'phone': '+91 9876543210',
        'billing_address': '123 Main Street, Mumbai, Maharashtra',
        'state': 'Maharashtra',
        'pincode': '400001',
        'created_at': datetime.utcnow().isoformat(),
        'is_active': True
    },
    {
        'id': 2,
        'name': 'Jane Smith',
        'email': 'jane.smith@example.com',
        'phone': '+91 8765432109',
        'billing_address': '456 Park Avenue, Delhi, Delhi',
        'state': 'Delhi',
        'pincode': '110001',
        'created_at': datetime.utcnow().isoformat(),
        'is_active': True
    },
    {
        'id': 3,
        'name': 'Alice Johnson',
        'email': 'alice.johnson@example.com',
        'phone': '+91 7654321098',
        'billing_address': '789 Pine Road, Bangalore, Karnataka',
        'state': 'Karnataka',
        'pincode': '560001',
        'created_at': datetime.utcnow().isoformat(),
        'is_active': True
    }
]
orders = [
    {
        'id': 1,
        'order_number': 'ORD-0001',
        'customer_id': 1,
        'customer_name': 'John Doe',
        'customer_email': 'john.doe@example.com',
        'products': [],
        'items': [],
        'total_amount': 0,
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat()
    },
    {
        'id': 2,
        'order_number': 'ORD-0002',
        'customer_id': 2,
        'customer_name': 'Jane Smith',
        'customer_email': 'jane.smith@example.com',
        'products': [],
        'items': [],
        'total_amount': 200.0,
        'status': 'invoiced',
        'created_at': datetime.utcnow().isoformat()
    }
]
invoices = [
    {
        'id': 1,
        'invoice_number': 'INV-0001',
        'customer_id': 1,
        'customer_name': 'John Doe',
        'customer_email': 'john.doe@example.com',
        'order_id': 1,
        'products': [],
        'items': [],
        'total_amount': 0,
        'gst_amount': 0,
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat()
    },
    {
        'id': 2,
        'invoice_number': 'INV-0002',
        'customer_id': 2,
        'customer_name': 'Jane Smith',
        'customer_email': 'jane.smith@example.com',
        'order_id': 2,
        'products': [],
        'items': [],
        'total_amount': 200.0,
        'gst_amount': 36.0,
        'status': 'paid',
        'created_at': datetime.utcnow().isoformat()
    },
    {
        'id': 3,
        'invoice_number': 'INV-0003',
        'customer_id': 3,
        'customer_name': 'Alice Johnson',
        'customer_email': 'alice.johnson@example.com',
        'order_id': 3,
        'products': [],
        'items': [],
        'total_amount': 200.0,
        'gst_amount': 36.0,
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat()
    }
]

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy', 
        'message': 'GST Billing System API is running',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/')
def root():
    return jsonify({
        'status': 'healthy', 
        'message': 'GST Billing System API is running',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'running',
        'message': 'API is operational'
    })

# Product routes
@app.route('/api/products', methods=['GET'])
@app.route('/api/products/', methods=['GET'])
def get_products():
    return jsonify({
        'success': True,
        'products': products
    })

@app.route('/api/products', methods=['POST'])
def create_product():
    try:
        data = request.get_json()
        product = {
            'id': len(products) + 1,
            'name': data.get('name'),
            'description': data.get('description'),
            'price': data.get('price'),
            'stock_quantity': data.get('stock_quantity', 0),
            'created_at': datetime.utcnow().isoformat()
        }
        products.append(product)
        
        return jsonify({
            'success': True,
            'message': 'Product created successfully',
            'product': product
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = next((p for p in products if p['id'] == product_id), None)
    if product:
        return jsonify({
            'success': True,
            'product': product
        })
    else:
        return jsonify({'success': False, 'message': 'Product not found'}), 404

@app.route('/api/products/<int:product_id>/stock', methods=['POST'])
def update_product_stock(product_id):
    try:
        product = next((p for p in products if p['id'] == product_id), None)
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'}), 404
        
        data = request.get_json()
        movement_type = data.get('movement_type')
        quantity = data.get('quantity', 0)
        
        if movement_type == 'in':
            product['stock_quantity'] += quantity
        elif movement_type == 'out':
            if product['stock_quantity'] >= quantity:
                product['stock_quantity'] -= quantity
            else:
                return jsonify({'success': False, 'message': 'Insufficient stock'}), 400
        
        return jsonify({
            'success': True,
            'message': f'Stock updated successfully. New quantity: {product["stock_quantity"]}',
            'new_quantity': product['stock_quantity']
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Customer routes
@app.route('/api/admin/customers', methods=['GET'])
def get_customers():
    return jsonify({
        'success': True,
        'customers': customers
    })

@app.route('/api/admin/customers', methods=['POST'])
def create_customer():
    try:
        data = request.get_json()
        customer = {
            'id': len(customers) + 1,
            'name': data.get('name'),
            'email': data.get('email'),
            'phone': data.get('phone'),
            'billing_address': data.get('billing_address'),
            'state': data.get('state', ''),
            'pincode': data.get('pincode', ''),
            'created_at': datetime.utcnow().isoformat(),
            'is_active': True
        }
        customers.append(customer)
        
        return jsonify({
            'success': True,
            'message': 'Customer created successfully',
            'customer': customer
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Customer order routes
@app.route('/api/customers/orders', methods=['GET'])
def get_customer_orders():
    # Return orders for customer view
    return jsonify({
        'success': True,
        'orders': orders
    })

@app.route('/api/customers/orders', methods=['POST'])
def create_customer_order():
    try:
        data = request.get_json()
        
        # Try to find customer information
        customer_id = data.get('customer_id')
        customer_name = data.get('customer_name', 'Unknown Customer')
        customer_email = data.get('customer_email', 'unknown@example.com')
        
        # If customer_id is provided, try to find customer details
        if customer_id:
            customer = next((c for c in customers if c['id'] == customer_id), None)
            if customer:
                customer_name = customer['name']
                customer_email = customer['email']
        
        order = {
            'id': len(orders) + 1,
            'order_number': f'ORD-{len(orders) + 1:04d}',
            'customer_id': customer_id,
            'customer_name': customer_name,
            'customer_email': customer_email,
            'products': data.get('products', []),
            'items': data.get('products', []),  # Add items field for compatibility
            'total_amount': data.get('total_amount', 0),
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat()
        }
        orders.append(order)
        
        return jsonify({
            'success': True,
            'message': 'Order created successfully',
            'order': order
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Customer invoice routes
@app.route('/api/customers/invoices', methods=['GET'])
def get_customer_invoices():
    # Return empty invoices list for now
    return jsonify({
        'success': True,
        'invoices': []
    })

@app.route('/api/customers/invoices', methods=['POST'])
def create_customer_invoice():
    try:
        data = request.get_json()
        
        # Try to find customer information
        customer_id = data.get('customer_id')
        customer_name = data.get('customer_name', 'Unknown Customer')
        customer_email = data.get('customer_email', 'unknown@example.com')
        
        # If customer_id is provided, try to find customer details
        if customer_id:
            customer = next((c for c in customers if c['id'] == customer_id), None)
            if customer:
                customer_name = customer['name']
                customer_email = customer['email']
        
        invoice = {
            'id': len(invoices) + 1,
            'invoice_number': f'INV-{len(invoices) + 1:04d}',
            'customer_id': customer_id,
            'customer_name': customer_name,
            'customer_email': customer_email,
            'order_id': data.get('order_id'),
            'products': data.get('products', []),
            'items': data.get('products', []),  # Add items field for compatibility
            'total_amount': data.get('total_amount', 0),
            'gst_amount': data.get('gst_amount', 0),
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat()
        }
        invoices.append(invoice)
        
        return jsonify({
            'success': True,
            'message': 'Invoice created successfully',
            'invoice': invoice
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Auth routes (simplified)
@app.route('/api/auth/register', methods=['POST'])
def register():
    return jsonify({
        'success': True,
        'message': 'Registration successful!'
    })

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    return jsonify({
        'success': True,
        'message': 'Login successful!',
        'user': {
            'id': 1,
            'username': 'admin',
            'email': 'admin@test.com',
            'business_name': 'Test Business'
        }
    })

@app.route('/api/auth/logout', methods=['POST'])
def auth_logout():
    return jsonify({
        'success': True,
        'message': 'Logout successful!'
    })

@app.route('/api/auth/check')
def auth_check():
    return jsonify({
        'authenticated': True,
        'user_type': 'admin',
        'user': {
            'id': 1,
            'username': 'admin',
            'email': 'admin@test.com'
        }
    })

# Admin order routes
@app.route('/api/admin/orders', methods=['GET'])
def get_admin_orders():
    return jsonify({
        'success': True,
        'orders': orders
    })

@app.route('/api/admin/orders/<int:order_id>/generate-invoice', methods=['POST'])
def generate_invoice_from_order(order_id):
    try:
        # Find the order
        order = next((o for o in orders if o['id'] == order_id), None)
        if not order:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Create invoice from order
        invoice = {
            'id': len(invoices) + 1,
            'invoice_number': f'INV-{len(invoices) + 1:04d}',
            'customer_id': order.get('customer_id'),
            'customer_name': order.get('customer_name', 'Unknown Customer'),
            'customer_email': order.get('customer_email', 'unknown@example.com'),
            'order_id': order_id,
            'products': order.get('products', []),
            'items': order.get('items', []),
            'total_amount': order.get('total_amount', 0),
            'gst_amount': order.get('total_amount', 0) * 0.18,  # 18% GST
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat()
        }
        invoices.append(invoice)
        
        # Update order status
        order['status'] = 'invoiced'
        
        return jsonify({
            'success': True,
            'message': 'Invoice generated successfully',
            'invoice': invoice
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        # Find the order
        order = next((o for o in orders if o['id'] == order_id), None)
        if not order:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Update order status
        order['status'] = new_status
        
        return jsonify({
            'success': True,
            'message': f'Order status updated to {new_status}',
            'order': order
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Invoice routes
@app.route('/api/invoices', methods=['GET'])
def get_invoices():
    return jsonify({
        'success': True,
        'invoices': invoices
    })

@app.route('/api/invoices', methods=['POST'])
def create_invoice():
    try:
        data = request.get_json()
        invoice = {
            'id': len(invoices) + 1,
            'invoice_number': f'INV-{len(invoices) + 1:04d}',
            'customer_id': data.get('customer_id'),
            'customer_name': data.get('customer_name', 'Unknown Customer'),
            'customer_email': data.get('customer_email', 'unknown@example.com'),
            'order_id': data.get('order_id'),
            'products': data.get('products', []),
            'items': data.get('products', []),  # Add items field for compatibility
            'total_amount': data.get('total_amount', 0),
            'gst_amount': data.get('gst_amount', 0),
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat()
        }
        invoices.append(invoice)
        
        return jsonify({
            'success': True,
            'message': 'Invoice created successfully',
            'invoice': invoice
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/invoices/<int:invoice_id>/download', methods=['GET'])
def download_invoice_pdf(invoice_id):
    try:
        # Find the invoice
        invoice = next((i for i in invoices if i['id'] == invoice_id), None)
        if not invoice:
            return jsonify({'success': False, 'error': 'Invoice not found'}), 404
        
        # For demo purposes, return a simple HTML response that can be converted to PDF
        # In a real application, you would use a library like reportlab or weasyprint
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Invoice {invoice['invoice_number']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; }}
                .invoice-details {{ margin: 20px 0; }}
                .customer-details {{ margin: 20px 0; }}
                .items-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .items-table th, .items-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .total {{ text-align: right; margin-top: 20px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>GST Billing System</h1>
                <h2>INVOICE</h2>
                <p>Invoice Number: {invoice['invoice_number']}</p>
                <p>Date: {invoice['created_at'][:10]}</p>
            </div>
            
            <div class="customer-details">
                <h3>Customer Details:</h3>
                <p><strong>Name:</strong> {invoice['customer_name']}</p>
                <p><strong>Email:</strong> {invoice['customer_email']}</p>
            </div>
            
            <table class="items-table">
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Quantity</th>
                        <th>Price</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f"<tr><td>{item.get('name', 'Product')}</td><td>{item.get('quantity', 1)}</td><td>₹{item.get('price', 0)}</td><td>₹{item.get('total', 0)}</td></tr>" for item in invoice.get('items', [])])}
                </tbody>
            </table>
            
            <div class="total">
                <p>Subtotal: ₹{invoice['total_amount']}</p>
                <p>GST (18%): ₹{invoice['gst_amount']}</p>
                <p><strong>Total Amount: ₹{invoice['total_amount'] + invoice['gst_amount']}</strong></p>
            </div>
            
            <div style="margin-top: 40px; text-align: center;">
                <p>Thank you for your business!</p>
            </div>
        </body>
        </html>
        """
        
        from flask import Response
        return Response(html_content, mimetype='text/html', headers={
            'Content-Disposition': f'attachment; filename=invoice_{invoice["invoice_number"]}.html'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Alternative PDF download endpoint (in case frontend uses different URL)
@app.route('/api/invoices/<int:invoice_id>/pdf', methods=['GET'])
def download_invoice_pdf_alt(invoice_id):
    return download_invoice_pdf(invoice_id)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
