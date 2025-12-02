from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os

# Global MongoDB client
client = None
db = None

def init_app(app):
    """Initialize MongoDB connection with Flask app"""
    global client, db
    
    # Get MongoDB URI from config
    mongo_uri = app.config.get('MONGO_URI') or os.environ.get('MONGO_URI')
    
    if not mongo_uri:
        raise ValueError("MONGO_URI not found in config or environment variables")
    
    try:
        # Connect to MongoDB
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # Test connection
        client.server_info()
        
        # Get database name from URI or use default
        db_name = mongo_uri.split('/')[-1].split('?')[0] if '/' in mongo_uri else 'GST-1'
        db = client[db_name]
        
        # Create indexes for better performance
        create_indexes(db)
        
        print(f"Successfully connected to MongoDB database: {db_name}")
        return db
    except ConnectionFailure as e:
        print(f"Failed to connect to MongoDB: {e}")
        raise

def create_indexes(database):
    """Create indexes for better query performance"""
    # Users collection
    database.users.create_index("email", unique=True)
    database.users.create_index("username", unique=True)
    database.users.create_index("gst_number", unique=True)
    
    # Super Admins collection
    database.super_admins.create_index("email", unique=True)
    
    # Customers collection
    database.customers.create_index("email", unique=True)
    database.customers.create_index("user_id")
    
    # Products collection
    database.products.create_index("user_id")
    database.products.create_index("admin_id")
    database.products.create_index("sku")
    
    # Invoices collection
    database.invoices.create_index("invoice_number", unique=True)
    database.invoices.create_index("user_id")
    database.invoices.create_index("customer_id")
    
    # Orders collection
    database.orders.create_index("order_number", unique=True)
    database.orders.create_index("customer_id")
    
    # Customer Product Prices collection
    database.customer_product_prices.create_index([("customer_id", 1), ("product_id", 1)], unique=True)
    
    print("MongoDB indexes created successfully")

