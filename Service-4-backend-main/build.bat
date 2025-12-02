@echo off
REM Build script for Windows deployment

echo Building GST Billing System for production...

REM Check if we're in the right directory
if not exist "app.py" (
    echo Error: app.py not found. Please run this script from the project root.
    exit /b 1
)

REM Build frontend
echo Building frontend...
cd frontend

if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)

echo Building frontend assets...
call npm run build

cd ..

REM Check if build was successful
if not exist "frontend\dist" (
    echo Error: Frontend build failed. frontend\dist directory not found.
    exit /b 1
)

echo Frontend build completed successfully!

REM Check Python dependencies
echo Checking Python dependencies...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -r requirements.txt

echo Python dependencies installed!

REM Check environment file
if not exist ".env" (
    echo Warning: .env file not found. Copying from .env.example...
    copy .env.example .env
    echo Please edit .env and set your production values before deploying!
)

echo Build process completed!
echo.
echo Next steps:
echo 1. Edit .env file with your production settings
echo 2. Run database migrations: flask db upgrade
echo 3. Start the server: gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app

