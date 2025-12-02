from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from models import User
from forms import LoginForm, RegistrationForm, ProfileForm
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    """Landing page - bypassed for now"""
    return jsonify({
        'success': True,
        'message': 'Landing page bypassed for development'
    })

@auth_bp.route('/login', methods=['POST'])
def login():
    """Admin login"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        if 'email' not in data or 'password' not in data:
            return jsonify({'success': False, 'message': 'Email and password are required'}), 400
        
        user = User.find_by_email(data['email'])
        if user and user.check_password(data['password']):
            # Auto-approve legacy users if needed
            if not user.is_approved:
                user.is_approved = True
                user.save()
            
            login_user(user, remember=data.get('remember_me', False))
            session.permanent = True
            # Force session to be saved immediately
            session.modified = True
            
            # Ensure ID is a string (convert ObjectId if needed)
            user_id = str(user.id) if user.id else None
            
            return jsonify({
                'success': True,
                'message': 'Login successful!',
                'user': {
                    'id': user_id,
                    'username': user.username,
                    'email': user.email,
                    'business_name': user.business_name
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
            
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Login error: {error_msg}'}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    """Admin registration"""
    try:
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        if 'email' not in data or 'password' not in data:
            return jsonify({'success': False, 'message': 'Email and password are required'}), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password are required'}), 400
        
        # Check if username or email already exists
        username = data.get('name') or data.get('username') or email.split('@')[0] if '@' in email else email
        username = username.strip() if username else email.split('@')[0] if '@' in email else email
        
        if username and User.find_by_username(username):
            return jsonify({'success': False, 'message': 'Username already exists'}), 400
        
        if User.find_by_email(email):
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        # Check database connection
        from database import db
        if db is None:
            return jsonify({'success': False, 'message': 'Database not initialized'}), 500
        
        # Handle GST number - validate and check for duplicates
        gst_number = data.get('gst_number', '').strip().upper()
        
        # If GST number is provided, validate it
        if gst_number:
            if not is_valid_gst(gst_number):
                return jsonify({'success': False, 'message': 'Invalid GST number format. GST number must be 15 characters in format: 00AAAAA0000A1Z5'}), 400
            
            # Check if GST number already exists
            existing_user = User.find_by_gst_number(gst_number)
            if existing_user:
                return jsonify({'success': False, 'message': 'GST number already registered. Please use a different GST number.'}), 400
        else:
            # Generate a unique GST number if not provided
            # Format: 00 + first 5 chars of username (uppercase, alphanumeric) + timestamp + Z + random char
            from datetime import datetime
            import random
            import string
            
            username_part = re.sub(r'[^A-Z0-9]', '', username.upper())[:5]
            if len(username_part) < 5:
                username_part = username_part.ljust(5, 'A')
            
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')[-4:]  # Last 4 digits
            random_char = random.choice(string.ascii_uppercase + string.digits)
            
            # Generate unique GST number: 00 + 5 chars + 4 digits + 1 char + Z + 1 char
            gst_number = f"00{username_part}{timestamp}{random.choice(string.ascii_uppercase)}Z{random_char}"
            
            # Ensure it's unique (very unlikely to conflict, but check anyway)
            counter = 0
            while User.find_by_gst_number(gst_number) and counter < 10:
                random_char = random.choice(string.ascii_uppercase + string.digits)
                gst_number = f"00{username_part}{timestamp}{random.choice(string.ascii_uppercase)}Z{random_char}"
                counter += 1
            
            if counter >= 10:
                return jsonify({'success': False, 'message': 'Unable to generate unique GST number. Please provide a GST number.'}), 500
        
         # Create new admin user (auto-approved)
        user = User(
            username=username,
            email=email,
            business_name=data.get('business_name', 'My Business'),
            gst_number=gst_number,
            business_address=data.get('business_address', 'Business Address'),
            business_phone=data.get('business_phone', '1234567890'),
            business_email=email,
            business_state=data.get('business_state', 'Delhi'),
            business_pincode=data.get('business_pincode', '110001'),
            business_reason=data.get('business_reason', 'Business reason not provided'),
            is_approved=True
        )
        user.set_password(password)
        user.save()
        
        if not user.id:
            return jsonify({'success': False, 'message': 'Failed to create user'}), 500
        
        # Ensure ID is a string (convert ObjectId if needed)
        user_id = str(user.id) if user.id else None
        
        return jsonify({
            'success': True,
            'message': 'Registration successful! Please login.',
            'user': {
                'id': user_id,
                'username': user.username,
                'email': user.email,
                'business_name': user.business_name
            }
        })
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        
        # Handle specific MongoDB duplicate key errors
        if 'E11000' in error_msg or 'duplicate key' in error_msg.lower():
            if 'gst_number' in error_msg:
                return jsonify({'success': False, 'message': 'GST number already registered. Please use a different GST number.'}), 400
            elif 'email' in error_msg:
                return jsonify({'success': False, 'message': 'Email already registered'}), 400
            elif 'username' in error_msg:
                return jsonify({'success': False, 'message': 'Username already exists'}), 400
            else:
                return jsonify({'success': False, 'message': 'A record with this information already exists. Please check your details.'}), 400
        
        return jsonify({'success': False, 'message': f'Registration error: {error_msg}'}), 500

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """User logout"""
    try:
        logout_user()
        session.clear()
        return jsonify({
            'success': True,
            'message': 'Logout successful'
        })
    except Exception as e:
        return jsonify({
            'success': True,
            'message': 'Logout successful'
        })

@auth_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    """User profile management - bypassed for now"""
    return jsonify({
        'success': True,
        'message': 'Profile management bypassed for development',
        'user': {
            'id': 1,
            'username': 'demo',
            'email': 'demo@example.com',
            'business_name': 'Demo Business'
        }
    })

@auth_bp.route('/check', methods=['GET'])
def check_auth():
    """Check if user is authenticated and return user type"""
    try:
        # Check if user is authenticated - this should work even if session is just created
        # Use getattr to safely check authentication status
        is_authenticated = getattr(current_user, 'is_authenticated', False) if hasattr(current_user, 'is_authenticated') else False
        
        if is_authenticated:
            # Determine user type by checking model attributes
            # SuperAdmin has 'is_super_admin' or 'name' attribute (not 'username')
            # User (admin) has 'username' and 'business_name' attributes
            # Customer has 'name' attribute (not 'username')
            
            if hasattr(current_user, 'is_super_admin') and current_user.is_super_admin:
                user_type = 'super_admin'
            elif hasattr(current_user, 'username') and hasattr(current_user, 'business_name'):
                # User model has username and business_name, so it's an admin
                user_type = 'admin'
            elif hasattr(current_user, 'is_admin') and current_user.is_admin:
                user_type = 'admin'
            elif hasattr(current_user, 'name') and not hasattr(current_user, 'username'):
                # Customer model has name but not username
                user_type = 'customer'
            else:
                # Default: if user logged in via /api/auth/login, they're admin
                # Check by trying to find in users collection
                from database import db
                from bson import ObjectId
                user_id = current_user.id if hasattr(current_user, 'id') else None
                if user_id:
                    # Check if exists in users collection (admin) or customers collection
                    user_doc = db['users'].find_one({'_id': ObjectId(user_id) if isinstance(user_id, str) else user_id})
                    if user_doc:
                        user_type = 'admin'
                    else:
                        user_type = 'customer'
                else:
                    user_type = 'customer'
            
            # Ensure ID is a string (convert ObjectId if needed)
            user_id = str(current_user.id) if hasattr(current_user, 'id') and current_user.id else None
            
            return jsonify({
                'authenticated': True,
                'user_type': user_type,
                'user_id': user_id
            })
        else:
            return jsonify({
                'authenticated': False,
                'user_type': None
            })
    except Exception as e:
        return jsonify({
            'authenticated': False,
            'user_type': None,
            'error': str(e)
        }), 500

def is_valid_gst(gst_number):
    """Validate GST number format"""
    # GST number should be 15 characters: 2 digits + 10 digits + 1 digit + 1 digit + 1 digit
    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    return bool(re.match(pattern, gst_number))

