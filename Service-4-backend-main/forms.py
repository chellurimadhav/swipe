from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, DateField, FloatField, IntegerField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange
from wtforms.widgets import TextArea

class LoginForm(FlaskForm):
    """Login form"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class RegistrationForm(FlaskForm):
    """User registration form"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    
    # Business details
    business_name = StringField('Business Name', validators=[DataRequired(), Length(max=200)])
    gst_number = StringField('GST Number', validators=[DataRequired(), Length(min=15, max=15)])
    business_address = TextAreaField('Business Address', validators=[DataRequired()])
    business_phone = StringField('Business Phone', validators=[DataRequired(), Length(max=15)])
    business_email = StringField('Business Email', validators=[DataRequired(), Email()])
    business_state = SelectField('Business State', validators=[DataRequired()], choices=[
        ('Andhra Pradesh', 'Andhra Pradesh'),
        ('Arunachal Pradesh', 'Arunachal Pradesh'),
        ('Assam', 'Assam'),
        ('Bihar', 'Bihar'),
        ('Chhattisgarh', 'Chhattisgarh'),
        ('Goa', 'Goa'),
        ('Gujarat', 'Gujarat'),
        ('Haryana', 'Haryana'),
        ('Himachal Pradesh', 'Himachal Pradesh'),
        ('Jharkhand', 'Jharkhand'),
        ('Karnataka', 'Karnataka'),
        ('Kerala', 'Kerala'),
        ('Madhya Pradesh', 'Madhya Pradesh'),
        ('Maharashtra', 'Maharashtra'),
        ('Manipur', 'Manipur'),
        ('Meghalaya', 'Meghalaya'),
        ('Mizoram', 'Mizoram'),
        ('Nagaland', 'Nagaland'),
        ('Odisha', 'Odisha'),
        ('Punjab', 'Punjab'),
        ('Rajasthan', 'Rajasthan'),
        ('Sikkim', 'Sikkim'),
        ('Tamil Nadu', 'Tamil Nadu'),
        ('Telangana', 'Telangana'),
        ('Tripura', 'Tripura'),
        ('Uttar Pradesh', 'Uttar Pradesh'),
        ('Uttarakhand', 'Uttarakhand'),
        ('West Bengal', 'West Bengal'),
        ('Delhi', 'Delhi'),
        ('Jammu and Kashmir', 'Jammu and Kashmir'),
        ('Ladakh', 'Ladakh'),
        ('Chandigarh', 'Chandigarh'),
        ('Dadra and Nagar Haveli and Daman and Diu', 'Dadra and Nagar Haveli and Daman and Diu'),
        ('Lakshadweep', 'Lakshadweep'),
        ('Puducherry', 'Puducherry'),
        ('Andaman and Nicobar Islands', 'Andaman and Nicobar Islands')
    ])
    business_pincode = StringField('Business Pincode', validators=[DataRequired(), Length(min=6, max=6)])
    business_reason = TextAreaField('Business Reason', validators=[DataRequired()])

class ProfileForm(FlaskForm):
    """User profile edit form"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    business_name = StringField('Business Name', validators=[DataRequired(), Length(max=200)])
    gst_number = StringField('GST Number', validators=[DataRequired(), Length(min=15, max=15)])
    business_address = TextAreaField('Business Address', validators=[DataRequired()])
    business_phone = StringField('Business Phone', validators=[DataRequired(), Length(max=15)])
    business_email = StringField('Business Email', validators=[DataRequired(), Email()])
    business_state = SelectField('Business State', validators=[DataRequired()], choices=[
        ('Andhra Pradesh', 'Andhra Pradesh'),
        ('Arunachal Pradesh', 'Arunachal Pradesh'),
        ('Assam', 'Assam'),
        ('Bihar', 'Bihar'),
        ('Chhattisgarh', 'Chhattisgarh'),
        ('Goa', 'Goa'),
        ('Gujarat', 'Gujarat'),
        ('Haryana', 'Haryana'),
        ('Himachal Pradesh', 'Himachal Pradesh'),
        ('Jharkhand', 'Jharkhand'),
        ('Karnataka', 'Karnataka'),
        ('Kerala', 'Kerala'),
        ('Madhya Pradesh', 'Madhya Pradesh'),
        ('Maharashtra', 'Maharashtra'),
        ('Manipur', 'Manipur'),
        ('Meghalaya', 'Meghalaya'),
        ('Mizoram', 'Mizoram'),
        ('Nagaland', 'Nagaland'),
        ('Odisha', 'Odisha'),
        ('Punjab', 'Punjab'),
        ('Rajasthan', 'Rajasthan'),
        ('Sikkim', 'Sikkim'),
        ('Tamil Nadu', 'Tamil Nadu'),
        ('Telangana', 'Telangana'),
        ('Tripura', 'Tripura'),
        ('Uttar Pradesh', 'Uttar Pradesh'),
        ('Uttarakhand', 'Uttarakhand'),
        ('West Bengal', 'West Bengal'),
        ('Delhi', 'Delhi'),
        ('Jammu and Kashmir', 'Jammu and Kashmir'),
        ('Ladakh', 'Ladakh'),
        ('Chandigarh', 'Chandigarh'),
        ('Dadra and Nagar Haveli and Daman and Diu', 'Dadra and Nagar Haveli and Daman and Diu'),
        ('Lakshadweep', 'Lakshadweep'),
        ('Puducherry', 'Puducherry'),
        ('Andaman and Nicobar Islands', 'Andaman and Nicobar Islands')
    ])
    business_pincode = StringField('Business Pincode', validators=[DataRequired(), Length(min=6, max=6)])

class CustomerForm(FlaskForm):
    """Customer form"""
    name = StringField('Customer Name', validators=[DataRequired(), Length(max=200)])
    gstin = StringField('GSTIN', validators=[Optional(), Length(max=15)])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=15)])
    billing_address = TextAreaField('Billing Address', validators=[DataRequired()])
    shipping_address = TextAreaField('Shipping Address', validators=[Optional()])
    state = SelectField('State', validators=[DataRequired()], choices=[
        ('Andhra Pradesh', 'Andhra Pradesh'),
        ('Arunachal Pradesh', 'Arunachal Pradesh'),
        ('Assam', 'Assam'),
        ('Bihar', 'Bihar'),
        ('Chhattisgarh', 'Chhattisgarh'),
        ('Goa', 'Goa'),
        ('Gujarat', 'Gujarat'),
        ('Haryana', 'Haryana'),
        ('Himachal Pradesh', 'Himachal Pradesh'),
        ('Jharkhand', 'Jharkhand'),
        ('Karnataka', 'Karnataka'),
        ('Kerala', 'Kerala'),
        ('Madhya Pradesh', 'Madhya Pradesh'),
        ('Maharashtra', 'Maharashtra'),
        ('Manipur', 'Manipur'),
        ('Meghalaya', 'Meghalaya'),
        ('Mizoram', 'Mizoram'),
        ('Nagaland', 'Nagaland'),
        ('Odisha', 'Odisha'),
        ('Punjab', 'Punjab'),
        ('Rajasthan', 'Rajasthan'),
        ('Sikkim', 'Sikkim'),
        ('Tamil Nadu', 'Tamil Nadu'),
        ('Telangana', 'Telangana'),
        ('Tripura', 'Tripura'),
        ('Uttar Pradesh', 'Uttar Pradesh'),
        ('Uttarakhand', 'Uttarakhand'),
        ('West Bengal', 'West Bengal'),
        ('Delhi', 'Delhi'),
        ('Jammu and Kashmir', 'Jammu and Kashmir'),
        ('Ladakh', 'Ladakh'),
        ('Chandigarh', 'Chandigarh'),
        ('Dadra and Nagar Haveli and Daman and Diu', 'Dadra and Nagar Haveli and Daman and Diu'),
        ('Lakshadweep', 'Lakshadweep'),
        ('Puducherry', 'Puducherry'),
        ('Andaman and Nicobar Islands', 'Andaman and Nicobar Islands')
    ])
    pincode = StringField('Pincode', validators=[DataRequired(), Length(min=6, max=6)])

class ProductForm(FlaskForm):
    """Product form"""
    name = StringField('Product Name', validators=[DataRequired(), Length(max=200)])
    sku = StringField('SKU', validators=[DataRequired(), Length(max=50)])
    hsn_code = StringField('HSN Code', validators=[DataRequired(), Length(max=10)])
    description = TextAreaField('Description', validators=[Optional()])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    gst_rate = SelectField('GST Rate (%)', validators=[DataRequired()], choices=[
        (0.0, '0%'),
        (5.0, '5%'),
        (12.0, '12%'),
        (18.0, '18%'),
        (28.0, '28%')
    ])
    stock_quantity = IntegerField('Initial Stock Quantity', validators=[DataRequired(), NumberRange(min=0)])
    min_stock_level = IntegerField('Minimum Stock Level', validators=[DataRequired(), NumberRange(min=0)])
    unit = SelectField('Unit', validators=[DataRequired()], choices=[
        ('PCS', 'Pieces'),
        ('KG', 'Kilograms'),
        ('LTR', 'Liters'),
        ('MTR', 'Meters'),
        ('BOX', 'Boxes'),
        ('PKT', 'Packets'),
        ('SET', 'Sets'),
        ('PAIR', 'Pairs'),
        ('DOZ', 'Dozen'),
        ('UNIT', 'Units')
    ])

class StockMovementForm(FlaskForm):
    """Stock movement form"""
    movement_type = SelectField('Movement Type', validators=[DataRequired()], choices=[
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
        ('adjustment', 'Stock Adjustment')
    ])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    reference = StringField('Reference', validators=[Optional(), Length(max=100)])
    notes = TextAreaField('Notes', validators=[Optional()])

class InvoiceForm(FlaskForm):
    """Invoice form"""
    customer_id = SelectField('Customer', validators=[DataRequired()], coerce=int)
    invoice_date = DateField('Invoice Date', validators=[DataRequired()])
    due_date = DateField('Due Date', validators=[Optional()])
    payment_terms = StringField('Payment Terms', validators=[Optional(), Length(max=100)])
    notes = TextAreaField('Notes', validators=[Optional()])
    items_data = HiddenField('Items Data', validators=[DataRequired()])

class CustomerRegistrationForm(FlaskForm):
    """Customer registration form"""
    name = StringField('Full Name', validators=[DataRequired(), Length(max=200)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=15)])
    gstin = StringField('GSTIN', validators=[Optional(), Length(max=15)])
    billing_address = TextAreaField('Billing Address', validators=[DataRequired()])
    shipping_address = TextAreaField('Shipping Address', validators=[Optional()])
    state = SelectField('State', validators=[DataRequired()], choices=[
        ('Andhra Pradesh', 'Andhra Pradesh'),
        ('Arunachal Pradesh', 'Arunachal Pradesh'),
        ('Assam', 'Assam'),
        ('Bihar', 'Bihar'),
        ('Chhattisgarh', 'Chhattisgarh'),
        ('Goa', 'Goa'),
        ('Gujarat', 'Gujarat'),
        ('Haryana', 'Haryana'),
        ('Himachal Pradesh', 'Himachal Pradesh'),
        ('Jharkhand', 'Jharkhand'),
        ('Karnataka', 'Karnataka'),
        ('Kerala', 'Kerala'),
        ('Madhya Pradesh', 'Madhya Pradesh'),
        ('Maharashtra', 'Maharashtra'),
        ('Manipur', 'Manipur'),
        ('Meghalaya', 'Meghalaya'),
        ('Mizoram', 'Mizoram'),
        ('Nagaland', 'Nagaland'),
        ('Odisha', 'Odisha'),
        ('Punjab', 'Punjab'),
        ('Rajasthan', 'Rajasthan'),
        ('Sikkim', 'Sikkim'),
        ('Tamil Nadu', 'Tamil Nadu'),
        ('Telangana', 'Telangana'),
        ('Tripura', 'Tripura'),
        ('Uttar Pradesh', 'Uttar Pradesh'),
        ('Uttarakhand', 'Uttarakhand'),
        ('West Bengal', 'West Bengal'),
        ('Delhi', 'Delhi'),
        ('Jammu and Kashmir', 'Jammu and Kashmir'),
        ('Ladakh', 'Ladakh'),
        ('Chandigarh', 'Chandigarh'),
        ('Dadra and Nagar Haveli and Daman and Diu', 'Dadra and Nagar Haveli and Daman and Diu'),
        ('Lakshadweep', 'Lakshadweep'),
        ('Puducherry', 'Puducherry'),
        ('Andaman and Nicobar Islands', 'Andaman and Nicobar Islands')
    ])
    pincode = StringField('Pincode', validators=[DataRequired(), Length(min=6, max=6)])

class CustomerLoginForm(FlaskForm):
    """Customer login form"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class ForgotPasswordForm(FlaskForm):
    """Forgot password form"""
    email = StringField('Email', validators=[DataRequired(), Email()])

class ResetPasswordForm(FlaskForm):
    """Reset password form"""
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

