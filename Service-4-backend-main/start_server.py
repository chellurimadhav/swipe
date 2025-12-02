#!/usr/bin/env python3
"""
Startup script for Railway deployment
Handles PORT environment variable and starts gunicorn
"""
import os
import sys
import subprocess

# Get PORT from environment, default to 5000
port = os.environ.get('PORT', '5000')

# Build gunicorn command
cmd = [
    'gunicorn',
    '--bind', f'0.0.0.0:{port}',
    '--workers', '4',
    '--timeout', '120',
    '--access-logfile', '-',
    '--error-logfile', '-',
    'wsgi:app'
]

# Start gunicorn
print(f"Starting gunicorn on port {port}...")
sys.exit(subprocess.call(cmd))

