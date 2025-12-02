#!/bin/bash

# Build script for deployment
set -e

echo "🚀 Building GST Billing System for production..."

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the project root."
    exit 1
fi

# Build frontend
echo "📦 Building frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "📥 Installing frontend dependencies..."
    npm install
fi

echo "🔨 Building frontend assets..."
npm run build

cd ..

# Check if build was successful
if [ ! -d "frontend/dist" ]; then
    echo "❌ Error: Frontend build failed. frontend/dist directory not found."
    exit 1
fi

echo "✅ Frontend build completed successfully!"

# Check Python dependencies
echo "🐍 Checking Python dependencies..."
if [ ! -d "venv" ]; then
    echo "📥 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

echo "✅ Python dependencies installed!"

# Check environment file
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and set your production values before deploying!"
fi

echo "✅ Build process completed!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your production settings"
echo "2. Run database migrations: flask db upgrade"
echo "3. Start the server: gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app"

