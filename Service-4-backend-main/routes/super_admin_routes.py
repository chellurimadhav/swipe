from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from models import SuperAdmin, User
from database import db
from bson import ObjectId
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

super_admin_bp = Blueprint('super_admin', __name__)

@super_admin_bp.route('/login', methods=['POST'])
def login():
    """Super admin login"""
    try:
        data = request.get_json()
        
        super_admin = SuperAdmin.find_by_email(data['email'])
        if super_admin and super_admin.check_password(data['password']):
            login_user(super_admin, remember=data.get('remember_me', False))
            session.permanent = True
            print(f"Login successful for super admin: {super_admin.email}")
            print(f"Session after login: {session}")
            
            return jsonify({
                'success': True,
                'message': 'Login successful!',
                'super_admin': {
                    'id': super_admin.id,
                    'name': super_admin.name,
                    'email': super_admin.email
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@super_admin_bp.route('/logout')
@login_required
def logout():
    """Super admin logout"""
    logout_user()
    return jsonify({'success': True, 'message': 'Logout successful'})

@super_admin_bp.route('/dashboard')
# @login_required  # Temporarily disabled for development
def dashboard():
    """Super admin dashboard"""
    try:
        print(f"Current user: {current_user}")
        print(f"User authenticated: {current_user.is_authenticated}")
        print(f"Session: {session}")
        # Get pending admin registrations
        pending_admins = [User.from_dict(doc) for doc in db['users'].find(
            {'is_approved': False, 'is_active': True}
        )]
        
        # Get approved admins
        approved_admins = [User.from_dict(doc) for doc in db['users'].find(
            {'is_approved': True, 'is_active': True}
        )]
        
        # Get total customers
        from models import Customer
        total_customers = db['customers'].count_documents({'is_active': True})
        
        # Get total products
        from models import Product
        total_products = db['products'].count_documents({'is_active': True})
        
        pending_list = []
        for admin in pending_admins:
            pending_list.append({
                'id': admin.id,
                'username': admin.username or '',
                'email': admin.email or '',
                'business_name': admin.business_name or '',
                'business_reason': admin.business_reason or '',
                'created_at': admin.created_at.isoformat()
            })
        
        approved_list = []
        for admin in approved_admins:
            approved_list.append({
                'id': admin.id,
                'username': admin.username or '',
                'email': admin.email or '',
                'business_name': admin.business_name or '',
                'approved_at': admin.approved_at.isoformat() if admin.approved_at else admin.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'stats': {
                'pending_admins': len(pending_list),
                'approved_admins': len(approved_list),
                'total_customers': total_customers,
                'total_products': total_products
            },
            'pending_admins': pending_list,
            'approved_admins': approved_list
        })
        
    except Exception as e:
        print(f"Dashboard error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@super_admin_bp.route('/approve-admin/<int:admin_id>', methods=['POST'])
# @login_required  # Temporarily disabled for development
def approve_admin(admin_id):
    """Approve admin registration"""
    try:
        admin = User.find_by_id(admin_id)
        if not admin:
            return jsonify({'success': False, 'message': 'Admin not found'}), 404
        
        if admin.is_approved:
            return jsonify({'success': False, 'message': 'Admin already approved'}), 400
        
        # Approve the admin
        admin.is_approved = True
        admin.approved_by = current_user.id
        admin.approved_at = datetime.utcnow()
        
        admin.save()
        
        # Send approval email
        send_approval_email(admin.email, admin.business_name)
        
        return jsonify({
            'success': True,
            'message': f'Admin {admin.business_name} approved successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@super_admin_bp.route('/reject-admin/<int:admin_id>', methods=['POST'])
# @login_required  # Temporarily disabled for development
def reject_admin(admin_id):
    """Reject admin registration"""
    try:
        admin = User.find_by_id(admin_id)
        if not admin:
            return jsonify({'success': False, 'message': 'Admin not found'}), 404
        
        if admin.is_approved:
            return jsonify({'success': False, 'message': 'Admin already approved'}), 400
        
        # Send rejection email
        send_rejection_email(admin.email, admin.business_name)
        
        # Delete the admin registration
        admin_id_obj = ObjectId(admin_id) if isinstance(admin_id, str) else admin_id
        db['users'].delete_one({'_id': admin_id_obj})
        
        return jsonify({
            'success': True,
            'message': f'Admin {admin.business_name} rejected and removed'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def send_approval_email(email, business_name):
    """Send approval email to admin"""
    try:
        # For now, just print the email content
        # In production, you would use a proper email service
        print(f"APPROVAL EMAIL TO: {email}")
        print(f"Subject: Your Business Registration Has Been Approved")
        print(f"Content: Dear {business_name}, your business registration has been approved. You can now login to your dashboard.")
        
        # Example email sending code (uncomment and configure for production):
        # import smtplib
        # from email.mime.text import MIMEText
        # from email.mime.multipart import MIMEMultipart
        #
        # msg = MIMEMultipart()
        # msg['From'] = 'noreply@yourdomain.com'
        # msg['To'] = email
        # msg['Subject'] = 'Your Business Registration Has Been Approved'
        #
        # body = f"""Dear {business_name},
        #
        # Congratulations! Your business registration has been approved by our super admin.
        # You can now login to your dashboard and start managing your business.
        #
        # Login URL: http://yourdomain.com/login
        #
        # Best regards,
        # Your Platform Team"""
        #
        # msg.attach(MIMEText(body, 'plain'))
        #
        # # Configure your SMTP settings
        # server = smtplib.SMTP('smtp.gmail.com', 587)
        # server.starttls()
        # server.login('your-email@gmail.com', 'your-app-password')
        # text = msg.as_string()
        # server.sendmail('noreply@yourdomain.com', email, text)
        # server.quit()
        
    except Exception as e:
        print(f"Error sending approval email: {e}")

def send_rejection_email(email, business_name):
    """Send rejection email to admin"""
    try:
        # For now, just print the email content
        # In production, you would use a proper email service
        print(f"REJECTION EMAIL TO: {email}")
        print(f"Subject: Business Registration Update")
        print(f"Content: Dear {business_name}, your business registration has been reviewed and unfortunately not approved at this time.")
        
        # Example email sending code (uncomment and configure for production):
        # import smtplib
        # from email.mime.text import MIMEText
        # from email.mime.multipart import MIMEMultipart
        #
        # msg = MIMEMultipart()
        # msg['From'] = 'noreply@yourdomain.com'
        # msg['To'] = email
        # msg['Subject'] = 'Business Registration Update'
        #
        # body = f"""Dear {business_name},
        #
        # Thank you for your interest in our platform. After careful review, 
        # we regret to inform you that your business registration has not been 
        # approved at this time.
        #
        # If you have any questions, please feel free to contact us.
        #
        # Best regards,
        # Your Platform Team"""
        #
        # msg.attach(MIMEText(body, 'plain'))
        #
        # # Configure your SMTP settings
        # server = smtplib.SMTP('smtp.gmail.com', 587)
        # server.starttls()
        # server.login('your-email@gmail.com', 'your-app-password')
        # text = msg.as_string()
        # server.sendmail('noreply@yourdomain.com', email, text)
        # server.quit()
        
    except Exception as e:
        print(f"Error sending rejection email: {e}")
