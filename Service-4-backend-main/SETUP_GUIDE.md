# 🚀 GST Billing System - Setup Guide

This guide will help you set up and run the complete GST Billing + Inventory Management System on your local machine.

## 📋 Prerequisites

Before you begin, make sure you have the following installed:

- **Python 3.8 or higher**
- **pip** (Python package installer)
- **Git** (optional, for cloning the repository)

## 🛠 Installation Steps

### 1. Clone or Download the Project

If you have Git:
```bash
git clone <repository-url>
cd gst_inventory_app
```

Or download and extract the ZIP file to a folder named `gst_inventory_app`.

### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize the Application

Run the setup script to create the database and sample data:

```bash
python setup.py
```

This will:
- Create the SQLite database
- Create all necessary tables
- Create an admin user (username: `admin`, password: `admin123`)
- Set up the upload directory

### 5. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## 🎯 Quick Start Guide

### First Login

1. Open your browser and go to `http://localhost:5000`
2. Click "Login" or go directly to `http://localhost:5000/login`
3. Use the default admin credentials:
   - **Username:** `admin`
   - **Password:** `admin123`

### Alternative: Register New Business

1. Go to `http://localhost:5000/register`
2. Fill in your business details including:
   - Username and password
   - Business name and GST number
   - Complete business address
   - Contact information

### Getting Started

After logging in, follow these steps:

1. **Add Customers** - Go to Customers → Add Customer
2. **Add Products** - Go to Products → Add Product
3. **Create Invoices** - Go to Invoices → New Invoice
4. **View Reports** - Check out the Dashboard and Reports sections

## 📁 Project Structure

```
gst_inventory_app/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── models.py             # Database models
├── database.py           # Database initialization
├── forms.py              # Form definitions
├── pdf_generator.py      # PDF generation utilities
├── setup.py              # Setup script
├── requirements.txt      # Python dependencies
├── README.md            # Project documentation
├── SETUP_GUIDE.md       # This file
├── routes/              # Route handlers
│   ├── auth_routes.py    # Authentication routes
│   ├── dashboard_routes.py # Dashboard routes
│   ├── customer_routes.py # Customer management
│   ├── product_routes.py # Product & inventory
│   ├── invoice_routes.py # Billing & invoices
│   ├── gst_routes.py     # GST reports
│   └── report_routes.py  # Business reports
├── templates/           # HTML templates
│   ├── base.html        # Base template
│   ├── index.html       # Landing page
│   ├── auth/           # Authentication templates
│   ├── dashboard/      # Dashboard templates
│   ├── customers/      # Customer templates
│   ├── products/       # Product templates
│   ├── invoices/       # Invoice templates
│   ├── gst/           # GST report templates
│   └── reports/       # Report templates
└── static/            # Static files (CSS, JS, images)
```

## 🔧 Configuration

### Environment Variables

You can customize the application by setting environment variables:

```bash
# Windows
set FLASK_ENV=production
set SECRET_KEY=your-secret-key-here

# macOS/Linux
export FLASK_ENV=production
export SECRET_KEY=your-secret-key-here
```

### Database Configuration

The application uses SQLite by default. To use MySQL or PostgreSQL:

1. Update `config.py` with your database settings
2. Install the appropriate database driver:
   - MySQL: `pip install mysqlclient`
   - PostgreSQL: `pip install psycopg2-binary`

## 🚀 Features Overview

### ✅ Implemented Features

- **Multi-User Authentication**
  - User registration with business details
  - Secure login/logout
  - Profile management

- **Customer Management**
  - Add, edit, delete customers
  - Store GSTIN, contact details, addresses
  - Search and filter customers

- **Product & Inventory Management**
  - Product catalog with HSN codes
  - Stock tracking and alerts
  - Stock movement history
  - Low stock notifications

- **GST Billing System**
  - Professional invoice generation
  - Automatic GST calculations (CGST/SGST/IGST)
  - PDF invoice download
  - Invoice status management

- **GST Reports**
  - GSTR-1 report generation
  - GSTR-3B report generation
  - GST summary by rate
  - Tax liability reports

- **Business Reports**
  - Sales reports (daily/monthly/yearly)
  - Customer analysis
  - Product performance
  - Inventory valuation

- **Dashboard & Analytics**
  - Real-time business metrics
  - Sales trends and charts
  - Top customers and products
  - Recent activity feed

### 🔄 Multi-User Data Isolation

- Each registered user has their own isolated business environment
- All data (customers, products, invoices) is separated by user
- Individual GST numbers and business details per user
- Secure session-based authentication

## 🛡 Security Features

- Password hashing with Werkzeug
- CSRF protection on forms
- Session management
- Input validation and sanitization
- SQL injection protection via SQLAlchemy ORM

## 📊 Database Schema

The application includes the following main tables:

- **Users** - Business owners and their details
- **Customers** - Customer information and addresses
- **Products** - Product catalog with HSN codes and pricing
- **Invoices** - Invoice headers and totals
- **InvoiceItems** - Individual items in invoices
- **StockMovements** - Inventory tracking
- **GSTReports** - Generated GST reports

## 🔧 Troubleshooting

### Common Issues

1. **Import Errors**
   - Make sure you're in the virtual environment
   - Run `pip install -r requirements.txt` again

2. **Database Errors**
   - Delete the `gst_inventory.db` file and run `python setup.py` again

3. **PDF Generation Issues**
   - Install system dependencies for WeasyPrint:
     - Windows: Install GTK3
     - macOS: `brew install cairo pango gdk-pixbuf libffi`
     - Ubuntu: `sudo apt-get install build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info`

4. **Port Already in Use**
   - Change the port in `app.py` or kill the process using port 5000

### Getting Help

If you encounter any issues:

1. Check the console output for error messages
2. Verify all dependencies are installed
3. Ensure you're using Python 3.8 or higher
4. Check that the virtual environment is activated

## 🚀 Deployment

### Production Deployment

For production deployment:

1. Set environment variables:
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=your-secure-secret-key
   ```

2. Use a production WSGI server:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

3. Set up a reverse proxy (nginx) for better performance

4. Use a production database (MySQL/PostgreSQL)

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python setup.py

EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For support and questions:
- Check the troubleshooting section above
- Review the code comments and documentation
- Create an issue in the repository

---

**Happy Billing! 🎉**

Your GST Billing System is now ready to streamline your business operations.

