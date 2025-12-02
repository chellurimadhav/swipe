#!/usr/bin/env python3
"""
Test script to check Railway deployment
"""

import requests
import json

def test_railway():
    base_url = "https://web-production-f50e6.up.railway.app"
    
    # Test health endpoint
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Health error: {e}")
    
    # Test root endpoint
    print("\nTesting root endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        print(f"Root: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Root error: {e}")
    
    # Test super-admin login
    print("\nTesting super-admin login...")
    try:
        data = {"email": "admin@gstbilling.com", "password": "admin123"}
        response = requests.post(f"{base_url}/api/super-admin/login", json=data)
        print(f"Super-admin login: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Super-admin login error: {e}")
    
    # Test auth login
    print("\nTesting auth login...")
    try:
        data = {"email": "admin@gstbilling.com", "password": "admin123"}
        response = requests.post(f"{base_url}/api/auth/login", json=data)
        print(f"Auth login: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Auth login error: {e}")

if __name__ == "__main__":
    test_railway()
