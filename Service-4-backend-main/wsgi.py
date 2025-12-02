"""
WSGI entry point for production deployment
"""
import os
from app import create_app

# Get environment from environment variable, default to production
config_name = os.environ.get('FLASK_ENV', 'production')
if config_name == 'development':
    config_name = 'development'
elif config_name == 'production':
    config_name = 'production'
else:
    config_name = 'production'

# Create the Flask app instance
app = create_app(config_name)

if __name__ == '__main__':
    app.run()

