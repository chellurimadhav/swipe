# 🚀 Quick Deployment Guide

## Pre-Deployment Checklist

- [ ] Build frontend: `cd frontend && npm install && npm run build`
- [ ] Set environment variables (see `.env.example`)
- [ ] Configure database (PostgreSQL/MySQL recommended)
- [ ] Set strong `SECRET_KEY`
- [ ] Configure `CORS_ORIGINS` for your domain
- [ ] Test locally with production config

## Quick Start

### 1. Build the Application

**Linux/Mac:**
```bash
chmod +x build.sh
./build.sh
```

**Windows:**
```cmd
build.bat
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
# Edit .env with your production settings
```

### 3. Initialize Database

```bash
# Activate virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# Run migrations
flask db upgrade

# Or create tables
python -c "from app import create_app; from database import db; app = create_app('production'); app.app_context().push(); db.create_all()"
```

### 4. Run Production Server

```bash
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 wsgi:app
```

## Platform-Specific Deployment

### Railway
1. Connect your GitHub repo
2. Add environment variables from `.env.example`
3. Deploy automatically on push

### Heroku
```bash
heroku create your-app-name
heroku config:set FLASK_ENV=production SECRET_KEY=your-key
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
heroku run flask db upgrade
```

### Docker
```bash
docker build -t gst-billing .
docker run -p 5000:5000 -e FLASK_ENV=production -e SECRET_KEY=your-key gst-billing
```

## Environment Variables

Required variables:
- `FLASK_ENV=production`
- `SECRET_KEY` (minimum 32 characters, use a strong random string)
- `DATABASE_URL` (PostgreSQL/MySQL connection string)
- `CORS_ORIGINS` (comma-separated list of allowed origins)

Optional:
- `PORT` (default: 5000)
- `MAX_CONTENT_LENGTH` (default: 16MB)

## Security Notes

⚠️ **IMPORTANT:**
- Never commit `.env` file
- Use strong `SECRET_KEY` in production
- Enable HTTPS/SSL
- Use production database (not SQLite)
- Configure proper CORS origins
- Set `SESSION_COOKIE_SECURE=True` in production

## Health Check

Test deployment:
```bash
curl http://your-domain/health
```

Should return:
```json
{"status": "healthy", "message": "GST Billing System API is running"}
```

## Troubleshooting

**Frontend not loading:**
- Ensure `frontend/dist/` exists
- Run `npm run build` in frontend directory

**Database errors:**
- Verify `DATABASE_URL` format
- Check database server is running
- Run migrations: `flask db upgrade`

**CORS errors:**
- Verify `CORS_ORIGINS` includes your domain
- Check no trailing slashes in origins

For detailed deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md)

