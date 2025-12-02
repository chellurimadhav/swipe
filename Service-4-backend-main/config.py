import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb+srv://amenityforge_db_user:qcTX55G2K6ct36Ij@cluster0.ibp4qe2.mongodb.net/GST-1?appName=Cluster0'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # CORS settings
    CORS_ORIGINS = [origin.strip() for origin in os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')]
    
    # Security settings
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    # Use 'Lax' for development (localhost), 'None' for production cross-origin (requires Secure=True and HTTPS)
    SESSION_COOKIE_SAMESITE = 'Lax'  # Changed to 'Lax' for better localhost compatibility
    SESSION_COOKIE_DOMAIN = None  # Don't set domain for localhost
    
    # Port configuration for Railway
    PORT = int(os.environ.get('PORT', 5000))
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'static/uploads'
    
    # GST Configuration
    GST_RATES = {
        '0': 0,
        '5': 5,
        '12': 12,
        '18': 18,
        '28': 28
    }
    
    # Invoice settings
    INVOICE_PREFIX = 'INV'
    INVOICE_START_NUMBER = 1000
    
    # Pagination
    ITEMS_PER_PAGE = 20

class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'
    SESSION_COOKIE_SECURE = True

class TestingConfig(Config):
    TESTING = True
    MONGO_URI = 'mongodb://localhost:27017/test_db'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

