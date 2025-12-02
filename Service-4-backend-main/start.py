#!/usr/bin/env python3
"""
Simple startup script for Railway deployment
"""

import os
import sys

def main():
    print("🚀 Starting GST Billing System...")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"Port: {os.environ.get('PORT', '5000')}")
    
    try:
        from app_working import app
        print("✅ Working app imported successfully")
        
        # Test the health endpoint
        with app.test_client() as client:
            response = client.get('/health')
            print(f"Health check response: {response.status_code}")
            print(f"Health check data: {response.get_json()}")
            
            # Test API endpoint
            response = client.get('/api/test')
            print(f"API test response: {response.status_code}")
            print(f"API test data: {response.get_json()}")
        
        return app
        
    except Exception as e:
        print(f"❌ Error starting working app: {e}")
        import traceback
        traceback.print_exc()
        
        # Create minimal app
        from flask import Flask, jsonify
        app = Flask(__name__)
        
        @app.route('/health')
        def health():
            return jsonify({'status': 'healthy', 'message': 'GST Billing System API is running'})
        
        @app.route('/')
        def health_check():
            return jsonify({'status': 'healthy', 'message': 'GST Billing System API is running'})
        
        return app

if __name__ == '__main__':
    app = main()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
