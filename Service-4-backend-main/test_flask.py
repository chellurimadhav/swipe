from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/test')
def test():
    return {'message': 'Flask is working!'}

@app.route('/api/products')
def products():
    return {
        'success': True,
        'products': [
            {
                'id': 1,
                'name': 'Test Product',
                'description': 'Test Description',
                'price': 100.0,
                'gst_rate': 18.0,
                'stock_quantity': 10,
                'image_url': '',
                'brand': 'Test Brand',
                'category': 'Test Category',
                'sku': 'TEST-001',
                'hsn_code': 'TEST123',
                'is_active': True,
                'created_at': '2024-01-01T00:00:00'
            }
        ]
    }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

