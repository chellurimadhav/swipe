from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId

def get_db():
    """Get the database instance dynamically"""
    from database import db
    return db

class BaseModel:
    """Base model for MongoDB documents"""
    
    @staticmethod
    def to_dict(doc):
        """Convert MongoDB document to dict, converting ObjectId to string"""
        if doc is None:
            return None
        if isinstance(doc, dict):
            result = {}
            for key, value in doc.items():
                if isinstance(value, ObjectId):
                    result[key] = str(value)
                elif isinstance(value, datetime):
                    result[key] = value.isoformat()
                elif isinstance(value, dict):
                    result[key] = BaseModel.to_dict(value)
                elif isinstance(value, list):
                    result[key] = [BaseModel.to_dict(item) if isinstance(item, dict) else item for item in value]
                else:
                    result[key] = value
            return result
        return doc
    
    @staticmethod
    def from_dict(data):
        """Convert dict to MongoDB document format"""
        if data is None:
            return None
        result = {}
        for key, value in data.items():
            if key == '_id' and isinstance(value, str):
                try:
                    result[key] = ObjectId(value)
                except:
                    result[key] = value
            elif isinstance(value, dict):
                result[key] = BaseModel.from_dict(value)
            elif isinstance(value, list):
                result[key] = [BaseModel.from_dict(item) if isinstance(item, dict) else item for item in value]
            else:
                result[key] = value
        return result

class User(UserMixin):
    """User model for business owners"""
    
    collection_name = 'users'
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('_id') or kwargs.get('id')
        self.username = kwargs.get('username')
        self.email = kwargs.get('email')
        self.password_hash = kwargs.get('password_hash')
        self.business_name = kwargs.get('business_name')
        self.gst_number = kwargs.get('gst_number')
        self.business_address = kwargs.get('business_address')
        self.business_phone = kwargs.get('business_phone')
        self.business_email = kwargs.get('business_email')
        self.business_state = kwargs.get('business_state')
        self.business_pincode = kwargs.get('business_pincode')
        self.business_reason = kwargs.get('business_reason')
        self.is_approved = kwargs.get('is_approved', False)
        self.approved_by = kwargs.get('approved_by')
        self.approved_at = kwargs.get('approved_at')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        # Use __dict__ to set is_active since UserMixin has it as a property
        self.__dict__['is_active'] = kwargs.get('is_active', True)
    
    @property
    def is_active(self):
        """Override UserMixin's is_active property to make it settable"""
        return self.__dict__.get('is_active', True)
    
    @is_active.setter
    def is_active(self, value):
        """Allow setting is_active"""
        self.__dict__['is_active'] = value
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        data = {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'business_name': self.business_name,
            'gst_number': self.gst_number,
            'business_address': self.business_address,
            'business_phone': self.business_phone,
            'business_email': self.business_email,
            'business_state': self.business_state,
            'business_pincode': self.business_pincode,
            'business_reason': self.business_reason,
            'is_approved': self.is_approved,
            'approved_by': ObjectId(self.approved_by) if self.approved_by and isinstance(self.approved_by, str) and ObjectId.is_valid(self.approved_by) else self.approved_by,
            'approved_at': self.approved_at,
            'created_at': self.created_at,
            'is_active': self.is_active
        }
        # Only include _id if it exists and is valid
        if self.id:
            if isinstance(self.id, str) and ObjectId.is_valid(self.id):
                data['_id'] = ObjectId(self.id)
            else:
                data['_id'] = self.id
        return data
    
    @classmethod
    def from_dict(cls, data):
        if data is None:
            return None
        if not isinstance(data, dict):
            return None
        # Create a copy to avoid modifying the original
        user_data = data.copy()
        if '_id' in user_data:
            user_data['id'] = str(user_data['_id']) if user_data['_id'] is not None else None
            # Remove _id from kwargs to avoid passing it to __init__
            if '_id' in user_data:
                del user_data['_id']
        try:
            return cls(**user_data)
        except Exception as e:
            print(f"Error creating User from dict: {e}")
            print(f"Data: {user_data}")
            raise
    
    def save(self):
        """Save user to MongoDB"""
        try:
            db = get_db()
            if db is None:
                raise ValueError("Database not initialized. Call init_app() first.")
            data = self.to_dict()
            # Remove _id from data if it's None or empty for insert operations
            if '_id' in data and (data['_id'] is None or not data['_id']):
                del data['_id']
            
            if self.id and '_id' in data and data['_id']:
                # Update existing document
                update_data = {k: v for k, v in data.items() if k != '_id'}
                db[self.collection_name].update_one({'_id': data['_id']}, {'$set': update_data})
            else:
                # Insert new document
                result = db[self.collection_name].insert_one(data)
                if result is not None and hasattr(result, 'inserted_id') and result.inserted_id:
                    self.id = str(result.inserted_id)
                else:
                    raise ValueError("Failed to insert document: result is None or missing inserted_id")
            return self
        except Exception as e:
            import traceback
            print(f"Error saving user: {e}")
            traceback.print_exc()
            raise
    
    @classmethod
    def find_by_id(cls, user_id):
        """Find user by ID"""
        try:
            db = get_db()
            if db is None:
                return None
            if not user_id:
                return None
            doc = db[cls.collection_name].find_one({'_id': ObjectId(user_id)})
            if doc:
                return cls.from_dict(doc)
        except Exception as e:
            print(f"Error finding user by ID: {e}")
        return None
    
    @classmethod
    def find_by_email(cls, email):
        """Find user by email"""
        try:
            db = get_db()
            if db is None:
                return None
            doc = db[cls.collection_name].find_one({'email': email})
            if doc:
                return cls.from_dict(doc)
        except Exception as e:
            print(f"Error finding user by email: {e}")
        return None
    
    @classmethod
    def find_by_username(cls, username):
        """Find user by username"""
        try:
            db = get_db()
            if db is None:
                return None
            if not username:
                return None
            doc = db[cls.collection_name].find_one({'username': username})
            if doc:
                return cls.from_dict(doc)
        except Exception as e:
            print(f"Error finding user by username: {e}")
        return None
    
    def __repr__(self):
        return f'<User {self.username}>'

class SuperAdmin(UserMixin):
    """Super Admin model"""
    
    collection_name = 'super_admins'
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('_id') or kwargs.get('id')
        self.email = kwargs.get('email')
        self.password_hash = kwargs.get('password_hash')
        self.name = kwargs.get('name')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        # Use __dict__ to set is_active since UserMixin has it as a property
        self.__dict__['is_active'] = kwargs.get('is_active', True)
    
    @property
    def is_active(self):
        """Override UserMixin's is_active property to make it settable"""
        return self.__dict__.get('is_active', True)
    
    @is_active.setter
    def is_active(self, value):
        """Allow setting is_active"""
        self.__dict__['is_active'] = value
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            '_id': ObjectId(self.id) if isinstance(self.id, str) and ObjectId.is_valid(self.id) else self.id,
            'email': self.email,
            'password_hash': self.password_hash,
            'name': self.name,
            'created_at': self.created_at,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data):
        if data is None:
            return None
        if '_id' in data:
            data['id'] = str(data['_id'])
        return cls(**data)
    
    def save(self):
        """Save super admin to MongoDB"""
        db = get_db()
        if db is None:
            raise ValueError("Database not initialized. Call init_app() first.")
        data = self.to_dict()
        if '_id' in data and data['_id']:
            db[self.collection_name].update_one({'_id': data['_id']}, {'$set': data})
        else:
            result = db[self.collection_name].insert_one(data)
            self.id = str(result.inserted_id)
        return self
    
    @classmethod
    def find_by_id(cls, admin_id):
        """Find super admin by ID"""
        try:
            db = get_db()
            if db is None:
                return None
            doc = db[cls.collection_name].find_one({'_id': ObjectId(admin_id)})
            if doc:
                return cls.from_dict(doc)
        except:
            pass
        return None
    
    @classmethod
    def find_by_email(cls, email):
        """Find super admin by email"""
        db = get_db()
        if db is None:
            return None
        doc = db[cls.collection_name].find_one({'email': email})
        if doc:
            return cls.from_dict(doc)
        return None
    
    def __repr__(self):
        return f'<SuperAdmin {self.name}>'

class Customer(UserMixin):
    """Customer model with login capabilities"""
    
    collection_name = 'customers'
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('_id') or kwargs.get('id')
        self.user_id = kwargs.get('user_id')
        self.name = kwargs.get('name')
        self.email = kwargs.get('email')
        self.password_hash = kwargs.get('password_hash')
        self.phone = kwargs.get('phone')
        self.gstin = kwargs.get('gstin')
        self.company_name = kwargs.get('company_name')
        self.billing_address = kwargs.get('billing_address')
        self.shipping_address = kwargs.get('shipping_address')
        self.state = kwargs.get('state')
        self.pincode = kwargs.get('pincode')
        self.bank_name = kwargs.get('bank_name')
        self.bank_account_number = kwargs.get('bank_account_number')
        self.bank_ifsc = kwargs.get('bank_ifsc')
        self.opening_balance = kwargs.get('opening_balance', 0.0)
        self.opening_balance_type = kwargs.get('opening_balance_type', 'debit')
        self.credit_limit = kwargs.get('credit_limit', 0.0)
        self.discount = kwargs.get('discount', 0.0)
        self.notes = kwargs.get('notes')
        self.tags = kwargs.get('tags')
        self.cc_emails = kwargs.get('cc_emails')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        # Use __dict__ to set is_active since UserMixin has it as a property
        self.__dict__['is_active'] = kwargs.get('is_active', True)
    
    @property
    def is_active(self):
        """Override UserMixin's is_active property to make it settable"""
        return self.__dict__.get('is_active', True)
    
    @is_active.setter
    def is_active(self, value):
        """Allow setting is_active"""
        self.__dict__['is_active'] = value
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            '_id': ObjectId(self.id) if isinstance(self.id, str) and ObjectId.is_valid(self.id) else self.id,
            'user_id': ObjectId(self.user_id) if self.user_id and isinstance(self.user_id, str) and ObjectId.is_valid(self.user_id) else self.user_id,
            'name': self.name,
            'email': self.email,
            'password_hash': self.password_hash,
            'phone': self.phone,
            'gstin': self.gstin,
            'company_name': self.company_name,
            'billing_address': self.billing_address,
            'shipping_address': self.shipping_address,
            'state': self.state,
            'pincode': self.pincode,
            'bank_name': self.bank_name,
            'bank_account_number': self.bank_account_number,
            'bank_ifsc': self.bank_ifsc,
            'opening_balance': self.opening_balance,
            'opening_balance_type': self.opening_balance_type,
            'credit_limit': self.credit_limit,
            'discount': self.discount,
            'notes': self.notes,
            'tags': self.tags,
            'cc_emails': self.cc_emails,
            'created_at': self.created_at,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data):
        if data is None:
            return None
        if '_id' in data:
            data['id'] = str(data['_id'])
        if 'user_id' in data and isinstance(data['user_id'], ObjectId):
            data['user_id'] = str(data['user_id'])
        return cls(**data)
    
    def save(self):
        """Save customer to MongoDB"""
        try:
            db = get_db()
            if db is None:
                raise ValueError("Database not initialized. Call init_app() first.")
            data = self.to_dict()
            if '_id' in data and data['_id']:
                db[self.collection_name].update_one({'_id': data['_id']}, {'$set': data})
            else:
                result = db[self.collection_name].insert_one(data)
                self.id = str(result.inserted_id)
            return self
        except Exception as e:
            print(f"Error saving customer: {e}")
            raise
    
    @classmethod
    def find_by_id(cls, customer_id):
        """Find customer by ID"""
        try:
            db = get_db()
            if db is None:
                return None
            doc = db[cls.collection_name].find_one({'_id': ObjectId(customer_id)})
            if doc:
                return cls.from_dict(doc)
        except:
            pass
        return None
    
    @classmethod
    def find_by_email(cls, email):
        """Find customer by email"""
        try:
            db = get_db()
            if db is None:
                return None
            doc = db[cls.collection_name].find_one({'email': email})
            if doc:
                return cls.from_dict(doc)
        except Exception as e:
            print(f"Error finding customer by email: {e}")
        return None
    
    def __repr__(self):
        return f'<Customer {self.name}>'

class Product:
    """Product model"""
    
    collection_name = 'products'
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('_id') or kwargs.get('id')
        self.user_id = kwargs.get('user_id')
        self.admin_id = kwargs.get('admin_id')
        self.name = kwargs.get('name')
        self.sku = kwargs.get('sku')
        self.hsn_code = kwargs.get('hsn_code')
        self.description = kwargs.get('description')
        self.category = kwargs.get('category')
        self.brand = kwargs.get('brand')
        self.price = kwargs.get('price')
        self.purchase_price = kwargs.get('purchase_price', 0.0)
        self.gst_rate = kwargs.get('gst_rate', 18.0)
        self.stock_quantity = kwargs.get('stock_quantity', 0)
        self.min_stock_level = kwargs.get('min_stock_level', 10)
        self.unit = kwargs.get('unit', 'PCS')
        self.image_url = kwargs.get('image_url')
        self.weight = kwargs.get('weight')
        self.dimensions = kwargs.get('dimensions')
        self.vegetable_name = kwargs.get('vegetable_name')
        self.vegetable_name_hindi = kwargs.get('vegetable_name_hindi')
        self.quantity_gm = kwargs.get('quantity_gm')
        self.quantity_kg = kwargs.get('quantity_kg')
        self.rate_per_gm = kwargs.get('rate_per_gm')
        self.rate_per_kg = kwargs.get('rate_per_kg')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
        self.is_active = kwargs.get('is_active', True)
    
    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.min_stock_level

    def to_dict(self):
        return {
            '_id': ObjectId(self.id) if isinstance(self.id, str) and ObjectId.is_valid(self.id) else self.id,
            'user_id': ObjectId(self.user_id) if self.user_id and isinstance(self.user_id, str) and ObjectId.is_valid(self.user_id) else self.user_id,
            'admin_id': ObjectId(self.admin_id) if self.admin_id and isinstance(self.admin_id, str) and ObjectId.is_valid(self.admin_id) else self.admin_id,
            'name': self.name,
            'sku': self.sku,
            'hsn_code': self.hsn_code,
            'description': self.description,
            'category': self.category,
            'brand': self.brand,
            'price': self.price,
            'purchase_price': self.purchase_price,
            'gst_rate': self.gst_rate,
            'stock_quantity': self.stock_quantity,
            'min_stock_level': self.min_stock_level,
            'unit': self.unit,
            'image_url': self.image_url,
            'weight': self.weight,
            'dimensions': self.dimensions,
            'vegetable_name': self.vegetable_name,
            'vegetable_name_hindi': self.vegetable_name_hindi,
            'quantity_gm': self.quantity_gm,
            'quantity_kg': self.quantity_kg,
            'rate_per_gm': self.rate_per_gm,
            'rate_per_kg': self.rate_per_kg,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data):
        if data is None:
            return None
        if '_id' in data:
            data['id'] = str(data['_id'])
        if 'user_id' in data and isinstance(data['user_id'], ObjectId):
            data['user_id'] = str(data['user_id'])
        if 'admin_id' in data and isinstance(data['admin_id'], ObjectId):
            data['admin_id'] = str(data['admin_id'])
        return cls(**data)
    
    def save(self):
        """Save product to MongoDB"""
        db = get_db()
        if db is None:
            raise ValueError("Database not initialized. Call init_app() first.")
        data = self.to_dict()
        data['updated_at'] = datetime.utcnow()
        if '_id' in data and data['_id']:
            db[self.collection_name].update_one({'_id': data['_id']}, {'$set': data})
        else:
            result = db[self.collection_name].insert_one(data)
            self.id = str(result.inserted_id)
        return self
    
    @classmethod
    def find_by_id(cls, product_id):
        """Find product by ID"""
        db = get_db()
        if db is None:
            raise ValueError("Database not initialized. Call init_app() first.")
        try:
            doc = db[cls.collection_name].find_one({'_id': ObjectId(product_id)})
            if doc:
                return cls.from_dict(doc)
        except:
            pass
        return None
    
    def __repr__(self):
        return f'<Product {self.name}>'

class Invoice:
    """Invoice model"""
    
    collection_name = 'invoices'
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('_id') or kwargs.get('id')
        self.user_id = kwargs.get('user_id')
        self.customer_id = kwargs.get('customer_id')
        self.order_id = kwargs.get('order_id')
        self.invoice_number = kwargs.get('invoice_number')
        self.invoice_date = kwargs.get('invoice_date', datetime.utcnow().date())
        self.due_date = kwargs.get('due_date')
        self.subtotal = kwargs.get('subtotal', 0.0)
        self.cgst_amount = kwargs.get('cgst_amount', 0.0)
        self.sgst_amount = kwargs.get('sgst_amount', 0.0)
        self.igst_amount = kwargs.get('igst_amount', 0.0)
        self.total_amount = kwargs.get('total_amount', 0.0)
        self.status = kwargs.get('status', 'pending')
        self.payment_terms = kwargs.get('payment_terms')
        self.notes = kwargs.get('notes')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
        self.items = kwargs.get('items', [])
    
    def calculate_totals(self):
        """Calculate invoice totals"""
        self.subtotal = sum(item.get('total', 0) for item in self.items)
        
        # Get customer and user for state comparison
        customer = Customer.find_by_id(self.customer_id)
        user = User.find_by_id(self.user_id)
        
        if customer and user:
            customer_state = customer.state
            business_state = user.business_state
        
        if customer_state == business_state:
            # Same state - CGST + SGST
            total_gst = sum(item.get('gst_amount', 0) for item in self.items)
            self.cgst_amount = total_gst / 2
            self.sgst_amount = total_gst / 2
            self.igst_amount = 0.0
        else:
            # Different state - IGST
            self.igst_amount = sum(item.get('gst_amount', 0) for item in self.items)
            self.cgst_amount = 0.0
            self.sgst_amount = 0.0
        
        self.total_amount = self.subtotal + self.cgst_amount + self.sgst_amount + self.igst_amount

    def to_dict(self):
        return {
            '_id': ObjectId(self.id) if isinstance(self.id, str) and ObjectId.is_valid(self.id) else self.id,
            'user_id': ObjectId(self.user_id) if self.user_id and isinstance(self.user_id, str) and ObjectId.is_valid(self.user_id) else self.user_id,
            'customer_id': ObjectId(self.customer_id) if self.customer_id and isinstance(self.customer_id, str) and ObjectId.is_valid(self.customer_id) else self.customer_id,
            'order_id': ObjectId(self.order_id) if self.order_id and isinstance(self.order_id, str) and ObjectId.is_valid(self.order_id) else self.order_id,
            'invoice_number': self.invoice_number,
            'invoice_date': self.invoice_date,
            'due_date': self.due_date,
            'subtotal': self.subtotal,
            'cgst_amount': self.cgst_amount,
            'sgst_amount': self.sgst_amount,
            'igst_amount': self.igst_amount,
            'total_amount': self.total_amount,
            'status': self.status,
            'payment_terms': self.payment_terms,
            'notes': self.notes,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'items': self.items
        }
    
    @classmethod
    def from_dict(cls, data):
        if data is None:
            return None
        if '_id' in data:
            data['id'] = str(data['_id'])
        if 'user_id' in data and isinstance(data['user_id'], ObjectId):
            data['user_id'] = str(data['user_id'])
        if 'customer_id' in data and isinstance(data['customer_id'], ObjectId):
            data['customer_id'] = str(data['customer_id'])
        if 'order_id' in data and isinstance(data['order_id'], ObjectId):
            data['order_id'] = str(data['order_id'])
        return cls(**data)
    
    def save(self):
        """Save invoice to MongoDB"""
        db = get_db()
        if db is None:
            raise ValueError("Database not initialized. Call init_app() first.")
        data = self.to_dict()
        data['updated_at'] = datetime.utcnow()
        if '_id' in data and data['_id']:
            db[self.collection_name].update_one({'_id': data['_id']}, {'$set': data})
        else:
            result = db[self.collection_name].insert_one(data)
            self.id = str(result.inserted_id)
        return self
    
    @classmethod
    def find_by_id(cls, invoice_id):
        """Find invoice by ID"""
        db = get_db()
        if db is None:
            raise ValueError("Database not initialized. Call init_app() first.")
        try:
            doc = db[cls.collection_name].find_one({'_id': ObjectId(invoice_id)})
            if doc:
                return cls.from_dict(doc)
        except:
            pass
        return None
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'

class InvoiceItem:
    """Invoice item model"""
    
    collection_name = 'invoice_items'
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('_id') or kwargs.get('id')
        self.invoice_id = kwargs.get('invoice_id')
        self.product_id = kwargs.get('product_id')
        self.quantity = kwargs.get('quantity')
        self.unit_price = kwargs.get('unit_price')
        self.gst_rate = kwargs.get('gst_rate')
        self.gst_amount = kwargs.get('gst_amount')
        self.total = kwargs.get('total')
    
    def calculate_totals(self):
        """Calculate item totals"""
        self.total = self.quantity * self.unit_price

    def to_dict(self):
        return {
            '_id': ObjectId(self.id) if isinstance(self.id, str) and ObjectId.is_valid(self.id) else self.id,
            'invoice_id': ObjectId(self.invoice_id) if self.invoice_id and isinstance(self.invoice_id, str) and ObjectId.is_valid(self.invoice_id) else self.invoice_id,
            'product_id': ObjectId(self.product_id) if self.product_id and isinstance(self.product_id, str) and ObjectId.is_valid(self.product_id) else self.product_id,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'gst_rate': self.gst_rate,
            'gst_amount': self.gst_amount,
            'total': self.total
        }
    
    @classmethod
    def from_dict(cls, data):
        if data is None:
            return None
        if '_id' in data:
            data['id'] = str(data['_id'])
        if 'invoice_id' in data and isinstance(data['invoice_id'], ObjectId):
            data['invoice_id'] = str(data['invoice_id'])
        if 'product_id' in data and isinstance(data['product_id'], ObjectId):
            data['product_id'] = str(data['product_id'])
        return cls(**data)
    
    def save(self):
        """Save invoice item to MongoDB"""
        db = get_db()
        if db is None:
            raise ValueError("Database not initialized. Call init_app() first.")
        data = self.to_dict()
        if '_id' in data and data['_id']:
            db[self.collection_name].update_one({'_id': data['_id']}, {'$set': data})
        else:
            result = db[self.collection_name].insert_one(data)
            self.id = str(result.inserted_id)
        return self
    
    def __repr__(self):
        return f'<InvoiceItem Product:{self.product_id}>'

class StockMovement:
    """Stock movement model for tracking inventory changes"""
    
    collection_name = 'stock_movements'
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('_id') or kwargs.get('id')
        self.product_id = kwargs.get('product_id')
        self.movement_type = kwargs.get('movement_type')
        self.quantity = kwargs.get('quantity')
        self.reference = kwargs.get('reference')
        self.notes = kwargs.get('notes')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
    
    def to_dict(self):
        return {
            '_id': ObjectId(self.id) if isinstance(self.id, str) and ObjectId.is_valid(self.id) else self.id,
            'product_id': ObjectId(self.product_id) if self.product_id and isinstance(self.product_id, str) and ObjectId.is_valid(self.product_id) else self.product_id,
            'movement_type': self.movement_type,
            'quantity': self.quantity,
            'reference': self.reference,
            'notes': self.notes,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data):
        if data is None:
            return None
        if '_id' in data:
            data['id'] = str(data['_id'])
        if 'product_id' in data and isinstance(data['product_id'], ObjectId):
            data['product_id'] = str(data['product_id'])
        return cls(**data)
    
    def save(self):
        """Save stock movement to MongoDB"""
        db = get_db()
        if db is None:
            raise ValueError("Database not initialized. Call init_app() first.")
        data = self.to_dict()
        if '_id' in data and data['_id']:
            db[self.collection_name].update_one({'_id': data['_id']}, {'$set': data})
        else:
            result = db[self.collection_name].insert_one(data)
            self.id = str(result.inserted_id)
        return self
    
    def __repr__(self):
        return f'<StockMovement {self.movement_type} {self.quantity}>'

class GSTReport:
    """GST report model for storing periodic reports"""
    
    collection_name = 'gst_reports'
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('_id') or kwargs.get('id')
        self.user_id = kwargs.get('user_id')
        self.report_type = kwargs.get('report_type')
        self.period_month = kwargs.get('period_month')
        self.period_year = kwargs.get('period_year')
        self.total_taxable_value = kwargs.get('total_taxable_value', 0.0)
        self.total_cgst = kwargs.get('total_cgst', 0.0)
        self.total_sgst = kwargs.get('total_sgst', 0.0)
        self.total_igst = kwargs.get('total_igst', 0.0)
        self.report_data = kwargs.get('report_data')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
    
    def to_dict(self):
        return {
            '_id': ObjectId(self.id) if isinstance(self.id, str) and ObjectId.is_valid(self.id) else self.id,
            'user_id': ObjectId(self.user_id) if self.user_id and isinstance(self.user_id, str) and ObjectId.is_valid(self.user_id) else self.user_id,
            'report_type': self.report_type,
            'period_month': self.period_month,
            'period_year': self.period_year,
            'total_taxable_value': self.total_taxable_value,
            'total_cgst': self.total_cgst,
            'total_sgst': self.total_sgst,
            'total_igst': self.total_igst,
            'report_data': self.report_data,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data):
        if data is None:
            return None
        if '_id' in data:
            data['id'] = str(data['_id'])
        if 'user_id' in data and isinstance(data['user_id'], ObjectId):
            data['user_id'] = str(data['user_id'])
        return cls(**data)
    
    def save(self):
        """Save GST report to MongoDB"""
        db = get_db()
        if db is None:
            raise ValueError("Database not initialized. Call init_app() first.")
        data = self.to_dict()
        if '_id' in data and data['_id']:
            db[self.collection_name].update_one({'_id': data['_id']}, {'$set': data})
        else:
            result = db[self.collection_name].insert_one(data)
            self.id = str(result.inserted_id)
        return self
    
    def __repr__(self):
        return f'<GSTReport {self.report_type} {self.period_month}/{self.period_year}>'

class Order:
    """Order model for customer orders"""
    
    collection_name = 'orders'
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('_id') or kwargs.get('id')
        self.customer_id = kwargs.get('customer_id')
        self.order_number = kwargs.get('order_number')
        self.order_date = kwargs.get('order_date', datetime.utcnow())
        self.status = kwargs.get('status', 'pending')
        self.subtotal = kwargs.get('subtotal', 0.0)
        self.total_amount = kwargs.get('total_amount', 0.0)
        self.notes = kwargs.get('notes')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
        self.items = kwargs.get('items', [])
    
    def calculate_totals(self):
        """Calculate order totals"""
        self.subtotal = sum(item.get('total', 0) for item in self.items)
        self.total_amount = self.subtotal

    def to_dict(self):
        # Build base dictionary without _id so MongoDB can auto-generate it
        data = {
            'customer_id': ObjectId(self.customer_id) if self.customer_id and isinstance(self.customer_id, str) and ObjectId.is_valid(self.customer_id) else self.customer_id,
            'order_number': self.order_number,
            'order_date': self.order_date,
            'status': self.status,
            'subtotal': self.subtotal,
            'total_amount': self.total_amount,
            'notes': self.notes,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'items': self.items
        }
        # Only include _id when we actually have one; otherwise let MongoDB create it
        if self.id:
            data['_id'] = ObjectId(self.id) if isinstance(self.id, str) and ObjectId.is_valid(self.id) else self.id
        return data
    
    @classmethod
    def from_dict(cls, data):
        if data is None:
            return None
        if '_id' in data:
            data['id'] = str(data['_id'])
        if 'customer_id' in data and isinstance(data['customer_id'], ObjectId):
            data['customer_id'] = str(data['customer_id'])
        return cls(**data)
    
    def save(self):
        """Save order to MongoDB"""
        db = get_db()
        if db is None:
            raise ValueError("Database not initialized. Call init_app() first.")
        data = self.to_dict()
        data['updated_at'] = datetime.utcnow()
        
        # Remove _id if it's None or empty for insert operations
        if '_id' in data and (data['_id'] is None or not data['_id']):
            del data['_id']
        
        if '_id' in data and data['_id']:
            db[self.collection_name].update_one({'_id': data['_id']}, {'$set': data})
        else:
            result = db[self.collection_name].insert_one(data)
            if result and result.inserted_id:
                self.id = str(result.inserted_id)
            else:
                raise ValueError("Failed to insert order: result is None or missing inserted_id")
        return self
    
    @classmethod
    def find_by_id(cls, order_id):
        """Find order by ID"""
        db = get_db()
        if db is None:
            raise ValueError("Database not initialized. Call init_app() first.")
        try:
            doc = db[cls.collection_name].find_one({'_id': ObjectId(order_id)})
            if doc:
                return cls.from_dict(doc)
        except:
            pass
        return None
    
    def __repr__(self):
        return f'<Order {self.order_number}>'

class OrderItem:
    """Order item model"""
    
    collection_name = 'order_items'
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('_id') or kwargs.get('id')
        self.order_id = kwargs.get('order_id')
        self.product_id = kwargs.get('product_id')
        self.quantity = kwargs.get('quantity')
        self.unit_price = kwargs.get('unit_price')
        self.total = kwargs.get('total')
    
    def calculate_totals(self):
        """Calculate item totals"""
        self.total = self.quantity * self.unit_price

    def to_dict(self):
        # Build base dictionary without _id so MongoDB can auto-generate it
        data = {
            'order_id': ObjectId(self.order_id) if self.order_id and isinstance(self.order_id, str) and ObjectId.is_valid(self.order_id) else self.order_id,
            'product_id': ObjectId(self.product_id) if self.product_id and isinstance(self.product_id, str) and ObjectId.is_valid(self.product_id) else self.product_id,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total': self.total
        }
        # Only include _id when we actually have one; otherwise let MongoDB create it
        if self.id:
            data['_id'] = ObjectId(self.id) if isinstance(self.id, str) and ObjectId.is_valid(self.id) else self.id
        return data
    
    @classmethod
    def from_dict(cls, data):
        if data is None:
            return None
        if '_id' in data:
            data['id'] = str(data['_id'])
        if 'order_id' in data and isinstance(data['order_id'], ObjectId):
            data['order_id'] = str(data['order_id'])
        if 'product_id' in data and isinstance(data['product_id'], ObjectId):
            data['product_id'] = str(data['product_id'])
        return cls(**data)
    
    def save(self):
        """Save order item to MongoDB"""
        db = get_db()
        if db is None:
            raise ValueError("Database not initialized. Call init_app() first.")
        data = self.to_dict()
        
        # Remove _id if it's None or empty for insert operations
        if '_id' in data and (data['_id'] is None or not data['_id']):
            del data['_id']
        
        if '_id' in data and data['_id']:
            db[self.collection_name].update_one({'_id': data['_id']}, {'$set': data})
        else:
            result = db[self.collection_name].insert_one(data)
            if result and result.inserted_id:
                self.id = str(result.inserted_id)
            else:
                raise ValueError("Failed to insert order item: result is None or missing inserted_id")
        return self
    
    def __repr__(self):
        return f'<OrderItem Product:{self.product_id}>'

class CustomerProductPrice:
    """Customer-specific product pricing"""
    
    collection_name = 'customer_product_prices'
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('_id') or kwargs.get('id')
        self.customer_id = kwargs.get('customer_id')
        self.product_id = kwargs.get('product_id')
        self.price = kwargs.get('price')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
    
    def to_dict(self):
        return {
            '_id': ObjectId(self.id) if isinstance(self.id, str) and ObjectId.is_valid(self.id) else self.id,
            'customer_id': ObjectId(self.customer_id) if self.customer_id and isinstance(self.customer_id, str) and ObjectId.is_valid(self.customer_id) else self.customer_id,
            'product_id': ObjectId(self.product_id) if self.product_id and isinstance(self.product_id, str) and ObjectId.is_valid(self.product_id) else self.product_id,
            'price': self.price,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data):
        if data is None:
            return None
        if '_id' in data:
            data['id'] = str(data['_id'])
        if 'customer_id' in data and isinstance(data['customer_id'], ObjectId):
            data['customer_id'] = str(data['customer_id'])
        if 'product_id' in data and isinstance(data['product_id'], ObjectId):
            data['product_id'] = str(data['product_id'])
        return cls(**data)
    
    def save(self):
        """Save customer product price to MongoDB"""
        db = get_db()
        if db is None:
            raise ValueError("Database not initialized. Call init_app() first.")
        data = self.to_dict()
        data['updated_at'] = datetime.utcnow()
        if '_id' in data and data['_id']:
            db[self.collection_name].update_one({'_id': data['_id']}, {'$set': data})
        else:
            result = db[self.collection_name].insert_one(data)
            self.id = str(result.inserted_id)
        return self
    
    @classmethod
    def find_by_customer_and_product(cls, customer_id, product_id):
        """Find price by customer and product"""
        db = get_db()
        if db is None:
            raise ValueError("Database not initialized. Call init_app() first.")
        try:
            doc = db[cls.collection_name].find_one({
                'customer_id': ObjectId(customer_id) if isinstance(customer_id, str) else customer_id,
                'product_id': ObjectId(product_id) if isinstance(product_id, str) else product_id
            })
            if doc:
                return cls.from_dict(doc)
        except:
            pass
        return None

    def __repr__(self):
        return f'<CustomerProductPrice Customer:{self.customer_id} Product:{self.product_id} Price:{self.price}>'
