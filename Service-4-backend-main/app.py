from flask import Flask, render_template, send_from_directory, jsonify, request, send_file, make_response
from flask_cors import CORS
import os
from config import config
from database import init_app as init_db
from flask_login import LoginManager
from models import User
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO
import datetime

# Import routes
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.customer_routes import customer_bp
from routes.product_routes import product_bp
from routes.invoice_routes import invoice_bp
from routes.gst_routes import gst_bp
from routes.report_routes import report_bp
from routes.customer_auth_routes import customer_auth_bp
from routes.super_admin_routes import super_admin_bp
from routes.admin_routes import admin_bp
from routes.import_export_routes import import_export_bp

def create_app(config_name='development'):
    app = Flask(__name__, static_folder='frontend/dist', template_folder='frontend/dist')
    app.config.from_object(config[config_name])
    
    # Disable strict slashes to prevent redirects that break CORS preflight
    app.url_map.strict_slashes = False
    
    # Enable CORS for API routes with credentials support
    cors_origins = app.config.get('CORS_ORIGINS', ['http://localhost:3000', 'http://localhost:5173'])
    CORS(app, resources={
        r"/api/*": {
            "origins": cors_origins if app.config.get('FLASK_ENV') == 'production' else "*",
            "supports_credentials": True,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "Origin", "Accept", "X-Requested-With"],
            "expose_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Initialize MongoDB connection
    try:
        from database import init_app as init_db
        init_db(app)
    except Exception as e:
        # Log error but don't fail app startup - health check should still work
        import logging
        logging.warning(f"MongoDB initialization warning: {e}")
        # Print to stdout for container logs
        print(f"WARNING: MongoDB initialization issue (app will continue): {e}")
    
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = None  # Disable redirect for API routes
    
    @login_manager.user_loader
    def load_user(user_id):
        # Try to load super admin first, then admin user, then customer
        from models import SuperAdmin
        super_admin = SuperAdmin.find_by_id(user_id)
        if super_admin:
            return super_admin
        
        user = User.find_by_id(user_id)
        if user:
            return user
        
        from models import Customer
        customer = Customer.find_by_id(user_id)
        return customer
    
    # Allow OPTIONS requests globally to avoid login redirects during CORS preflight
    @app.before_request
    def handle_cors_preflight():
        if request.method == 'OPTIONS':
            response = make_response('', 200)
            return response

    # Health check endpoint - register early before catch-all routes
    @app.route('/health')
    def health():
        """Health check endpoint for Railway/deployment"""
        return jsonify({'status': 'healthy', 'message': 'GST Billing System API is running'}), 200
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(customer_bp, url_prefix='/api/customers')
    app.register_blueprint(product_bp, url_prefix='/api/products')
    app.register_blueprint(invoice_bp, url_prefix='/api/invoices')
    app.register_blueprint(gst_bp, url_prefix='/api/gst')
    app.register_blueprint(report_bp, url_prefix='/api/reports')
    app.register_blueprint(customer_auth_bp, url_prefix='/api/customer-auth')
    app.register_blueprint(super_admin_bp, url_prefix='/api/super-admin')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(import_export_bp, url_prefix='/api')
    
    # PDF Generation endpoint
    @app.route('/api/generate-pdf', methods=['POST'])
    def generate_pdf():
        try:
            data = request.get_json()
            
            # Create PDF
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = []
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=1  # Center alignment
            )
            
            # Business Header
            business_name = data.get('business_name', '')
            business_address = data.get('business_address', '')
            business_phone = data.get('business_phone', '')
            
            elements.append(Paragraph(business_name, title_style))
            if business_address:
                elements.append(Paragraph(business_address, styles['Normal']))
            if business_phone:
                elements.append(Paragraph(f"Phone: {business_phone}", styles['Normal']))
            
            elements.append(Spacer(1, 20))
            
            # Invoice Details
            invoice_number = data.get('invoice_number', '')
            invoice_date = data.get('invoice_date', '')
            customer_name = data.get('customer_name', '')
            customer_address = data.get('customer_address', '')
            customer_phone = data.get('customer_phone', '')
            
            invoice_info = [
                ['Invoice Number:', invoice_number],
                ['Date:', invoice_date],
                ['Customer:', customer_name],
                ['Address:', customer_address],
                ['Phone:', customer_phone]
            ]
            
            invoice_table = Table(invoice_info, colWidths=[2*inch, 4*inch])
            invoice_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(invoice_table)
            elements.append(Spacer(1, 20))
            
            # Items Table
            items = data.get('items', [])
            if items:
                # Table headers
                table_data = [['S.No', 'Product', 'Description', 'Quantity', 'Unit Price', 'Total']]
                
                # Add items
                for i, item in enumerate(items, 1):
                    product = item.get('product', {})
                    table_data.append([
                        str(i),
                        product.get('name', ''),
                        product.get('description', ''),
                        str(item.get('quantity', 0)),
                        f"₹{item.get('unit_price', 0):.2f}",
                        f"₹{item.get('total', 0):.2f}"
                    ])
                
                # Add total row
                total_amount = data.get('total_amount', 0)
                table_data.append(['', '', '', '', 'Total:', f"₹{total_amount:.2f}"])
                
                # Create table
                items_table = Table(table_data, colWidths=[0.5*inch, 1.5*inch, 2*inch, 0.8*inch, 1*inch, 1*inch])
                items_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header row
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),  # Total row
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -2), 1, colors.black),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
                elements.append(items_table)
            
            # Custom columns if any
            custom_columns = data.get('custom_columns', {})
            if custom_columns:
                elements.append(Spacer(1, 20))
                elements.append(Paragraph("Additional Information:", styles['Heading2']))
                
                custom_data = [[key, value] for key, value in custom_columns.items()]
                custom_table = Table(custom_data, colWidths=[2*inch, 4*inch])
                custom_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
                elements.append(custom_table)
            
            # Notes
            notes = data.get('notes', '')
            if notes:
                elements.append(Spacer(1, 20))
                elements.append(Paragraph("Notes:", styles['Heading2']))
                elements.append(Paragraph(notes, styles['Normal']))
            
            # Build PDF
            doc.build(elements)
            buffer.seek(0)
            
            return send_file(
                buffer,
                as_attachment=True,
                download_name=f"invoice_{invoice_number}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mimetype='application/pdf'
            )
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Serve React app (only for production)
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        # Skip API routes and health endpoint
        if path.startswith('api/'):
            return jsonify({'error': 'API route not found'}), 404
        
        # Skip health endpoint (already handled above)
        if path == 'health':
            return jsonify({'status': 'healthy', 'message': 'GST Billing System API is running'}), 200
            
        if path != "" and os.path.exists(app.static_folder + '/' + path):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')
    
    return app

if __name__ == '__main__':
    config_name = os.environ.get('FLASK_ENV', 'development')
    app = create_app(config_name)
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=(config_name == 'development'), host='0.0.0.0', port=port)
