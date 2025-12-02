# Deployment Guide

This guide will help you deploy the GST Billing System to production.

## Prerequisites

- Python 3.9+ installed
- Node.js 18+ and npm installed (for frontend build)
- PostgreSQL or MySQL database (recommended for production)
- Domain name and SSL certificate (for HTTPS)

## Quick Deployment Steps

### 1. Environment Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set the following required variables:
   ```bash
   FLASK_ENV=production
   SECRET_KEY=your-very-secure-secret-key-here-minimum-32-characters
   DATABASE_URL=postgresql://user:password@localhost:5432/dbname
   CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   PORT=5000
   ```

### 2. Database Setup

#### For PostgreSQL:
```bash
# Install PostgreSQL client libraries
pip install psycopg2-binary

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://user:password@localhost:5432/gst_billing
```

#### For MySQL:
```bash
# Install MySQL client libraries
pip install pymysql

# Update DATABASE_URL in .env
DATABASE_URL=mysql://user:password@localhost:3306/gst_billing
```

#### Initialize Database:
```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run migrations
flask db upgrade

# Or create tables directly
python -c "from app import create_app; from database import db; app = create_app('production'); app.app_context().push(); db.create_all()"
```

### 3. Build Frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

The built files will be in `frontend/dist/` which is served by Flask.

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run Production Server

#### Using Gunicorn (Recommended):
```bash
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 --access-logfile - --error-logfile - wsgi:app
```

#### Using Flask Development Server (Not Recommended for Production):
```bash
export FLASK_ENV=production
python app.py
```

## Deployment Platforms

### Railway

1. **Connect Repository**: Link your GitHub repository to Railway
2. **Set Environment Variables**: Add all variables from `.env.example`
3. **Build Command**: Railway will auto-detect and use the `Procfile`
4. **Deploy**: Railway will automatically deploy on push

The `Procfile` is already configured for Railway.

### Heroku

1. **Install Heroku CLI**:
   ```bash
   heroku login
   ```

2. **Create App**:
   ```bash
   heroku create your-app-name
   ```

3. **Set Environment Variables**:
   ```bash
   heroku config:set FLASK_ENV=production
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set DATABASE_URL=postgresql://...
   heroku config:set CORS_ORIGINS=https://yourdomain.com
   ```

4. **Add PostgreSQL Addon**:
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```

5. **Deploy**:
   ```bash
   git push heroku main
   ```

6. **Run Migrations**:
   ```bash
   heroku run flask db upgrade
   ```

### Docker

1. **Build Image**:
   ```bash
   docker build -t gst-billing-system .
   ```

2. **Run Container**:
   ```bash
   docker run -d \
     -p 5000:5000 \
     -e FLASK_ENV=production \
     -e SECRET_KEY=your-secret-key \
     -e DATABASE_URL=postgresql://... \
     -e CORS_ORIGINS=https://yourdomain.com \
     --name gst-billing \
     gst-billing-system
   ```

### VPS/Cloud Server (Ubuntu/Debian)

1. **Install Dependencies**:
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv nginx postgresql
   ```

2. **Setup Application**:
   ```bash
   git clone <your-repo>
   cd gst-billing-system
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Setup Systemd Service**:
   Create `/etc/systemd/system/gst-billing.service`:
   ```ini
   [Unit]
   Description=GST Billing System
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/path/to/gst-billing-system
   Environment="PATH=/path/to/gst-billing-system/venv/bin"
   Environment="FLASK_ENV=production"
   ExecStart=/path/to/gst-billing-system/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 --timeout 120 wsgi:app

   [Install]
   WantedBy=multi-user.target
   ```

4. **Start Service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable gst-billing
   sudo systemctl start gst-billing
   ```

5. **Setup Nginx Reverse Proxy**:
   Create `/etc/nginx/sites-available/gst-billing`:
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

6. **Enable Site**:
   ```bash
   sudo ln -s /etc/nginx/sites-available/gst-billing /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

7. **Setup SSL with Let's Encrypt**:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

## Security Checklist

- [ ] Change `SECRET_KEY` to a strong random string (minimum 32 characters)
- [ ] Use PostgreSQL or MySQL instead of SQLite for production
- [ ] Enable HTTPS/SSL certificate
- [ ] Set `SESSION_COOKIE_SECURE=True` in production
- [ ] Configure proper CORS origins (no wildcards in production)
- [ ] Set up firewall rules
- [ ] Enable database backups
- [ ] Set up monitoring and logging
- [ ] Use environment variables for all secrets
- [ ] Disable debug mode in production
- [ ] Set up rate limiting
- [ ] Configure proper file upload limits

## Monitoring

### Health Check Endpoint

The application provides a health check endpoint:
```
GET /health
```

Returns:
```json
{
  "status": "healthy",
  "message": "GST Billing System API is running"
}
```

### Logging

Logs are output to stdout/stderr and can be captured by your process manager (systemd, Docker, etc.).

For file logging, configure in `app.py`:
```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
```

## Troubleshooting

### Database Connection Issues
- Verify `DATABASE_URL` format is correct
- Check database server is running
- Verify user permissions
- Check firewall rules

### CORS Errors
- Verify `CORS_ORIGINS` includes your frontend domain
- Check that origins don't have trailing slashes
- Ensure HTTPS is used in production

### Static Files Not Loading
- Verify `frontend/dist/` exists and contains built files
- Check `static_folder` path in `app.py`
- Verify file permissions

### 500 Errors
- Check application logs
- Verify database migrations are up to date
- Check environment variables are set correctly

## Backup Strategy

### Database Backup (PostgreSQL)
```bash
pg_dump -U user -d dbname > backup_$(date +%Y%m%d).sql
```

### Automated Backups
Set up a cron job:
```bash
0 2 * * * pg_dump -U user -d dbname > /backups/db_$(date +\%Y\%m\%d).sql
```

## Performance Optimization

1. **Use Production Database**: PostgreSQL or MySQL instead of SQLite
2. **Enable Caching**: Consider Redis for session storage
3. **CDN**: Serve static assets via CDN
4. **Database Indexing**: Ensure proper indexes on frequently queried columns
5. **Connection Pooling**: Configure database connection pooling
6. **Load Balancing**: Use multiple Gunicorn workers (already configured)

## Support

For issues or questions, please check:
- Application logs
- Database logs
- Server logs
- GitHub Issues

