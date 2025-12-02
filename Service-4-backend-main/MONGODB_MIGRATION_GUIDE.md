# MongoDB Migration Guide

This document outlines the conversion patterns from SQLAlchemy to MongoDB for all route files.

## Common Conversion Patterns

### 1. Query by ID
**SQLAlchemy:**
```python
user = User.query.get(user_id)
```

**MongoDB:**
```python
user = User.find_by_id(user_id)
```

### 2. Query by Field
**SQLAlchemy:**
```python
user = User.query.filter_by(email=email).first()
```

**MongoDB:**
```python
user = User.find_by_email(email)
```

### 3. Query All
**SQLAlchemy:**
```python
users = User.query.all()
```

**MongoDB:**
```python
from database import db
from bson import ObjectId
users = [User.from_dict(doc) for doc in db['users'].find()]
```

### 4. Query with Filter
**SQLAlchemy:**
```python
from sqlalchemy import or_
customers = Customer.query.filter(
    or_(
        Customer.user_id == current_user.id,
        Customer.user_id.is_(None)
    )
).all()
```

**MongoDB:**
```python
from database import db
from bson import ObjectId
query = {
    '$or': [
        {'user_id': ObjectId(current_user.id)},
        {'user_id': None}
    ]
}
customers = [Customer.from_dict(doc) for doc in db['customers'].find(query)]
```

### 5. Create/Insert
**SQLAlchemy:**
```python
user = User(...)
db.session.add(user)
db.session.commit()
```

**MongoDB:**
```python
user = User(...)
user.save()
```

### 6. Update
**SQLAlchemy:**
```python
user.is_approved = True
db.session.commit()
```

**MongoDB:**
```python
user.is_approved = True
user.save()
```

### 7. Delete
**SQLAlchemy:**
```python
db.session.delete(user)
db.session.commit()
```

**MongoDB:**
```python
from database import db
from bson import ObjectId
db['users'].delete_one({'_id': ObjectId(user.id)})
```

### 8. Count
**SQLAlchemy:**
```python
count = User.query.count()
```

**MongoDB:**
```python
from database import db
count = db['users'].count_documents({})
```

### 9. Order By
**SQLAlchemy:**
```python
from sqlalchemy import desc
products = Product.query.order_by(desc(Product.created_at)).all()
```

**MongoDB:**
```python
from database import db
products = [Product.from_dict(doc) for doc in db['products'].find().sort('created_at', -1)]
```

### 10. Limit/Pagination
**SQLAlchemy:**
```python
products = Product.query.limit(10).offset(20).all()
```

**MongoDB:**
```python
from database import db
products = [Product.from_dict(doc) for doc in db['products'].find().skip(20).limit(10)]
```

### 11. Aggregations
**SQLAlchemy:**
```python
from sqlalchemy import func
total = db.session.query(func.sum(Invoice.total_amount)).scalar()
```

**MongoDB:**
```python
from database import db
result = db['invoices'].aggregate([
    {'$group': {'_id': None, 'total': {'$sum': '$total_amount'}}}
])
total = next(result, {}).get('total', 0)
```

### 12. Relationships/Joins
**SQLAlchemy:**
```python
invoice = Invoice.query.get(invoice_id)
customer = invoice.customer  # Using relationship
```

**MongoDB:**
```python
invoice = Invoice.find_by_id(invoice_id)
customer = Customer.find_by_id(invoice.customer_id)  # Manual lookup
```

## Important Notes

1. **ObjectId Conversion**: Always convert string IDs to ObjectId when querying:
   ```python
   from bson import ObjectId
   ObjectId(user_id)  # If user_id is a string
   ```

2. **Collection Names**: Use the `collection_name` attribute from model classes:
   ```python
   db[User.collection_name].find()
   ```

3. **Date Handling**: MongoDB stores dates as datetime objects, same as SQLAlchemy

4. **Relationships**: MongoDB doesn't have foreign keys. Store ObjectId references and manually lookup related documents.

5. **Transactions**: MongoDB supports transactions but they're not needed for simple operations. Use `save()` method on models.

## Files That Need Updates

All route files in the `routes/` directory need to be updated:
- ✅ auth_routes.py (DONE)
- ⏳ customer_auth_routes.py
- ⏳ admin_routes.py
- ⏳ admin_customer_routes.py
- ⏳ customer_routes.py
- ⏳ dashboard_routes.py
- ⏳ product_routes.py
- ⏳ invoice_routes.py
- ⏳ order_routes.py (if exists)
- ⏳ report_routes.py
- ⏳ gst_routes.py
- ⏳ super_admin_routes.py
- ⏳ import_export_routes.py

