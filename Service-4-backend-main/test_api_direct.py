import requests
import json

base_url = 'https://web-production-f50e6.up.railway.app'

print("Testing Railway API Directly...")
print("=" * 50)

# Test 1: Health check
try:
    response = requests.get(f"{base_url}/health", timeout=10)
    print(f"✅ Health Check: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ Health Check Failed: {e}")

# Test 2: Products endpoint
try:
    response = requests.get(f"{base_url}/api/products", timeout=10)
    print(f"✅ Products API: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ Products API Failed: {e}")

# Test 3: Test API endpoint
try:
    response = requests.get(f"{base_url}/api/test", timeout=10)
    print(f"✅ Test API: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ Test API Failed: {e}")

print("\n" + "=" * 50)
print("Test completed!")
