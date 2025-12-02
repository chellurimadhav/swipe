import requests
import json

def test_railway_backend():
    base_url = "https://web-production-f50e6.up.railway.app"
    
    print("Testing Railway Backend Status...")
    print("=" * 50)
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"✅ Health Check: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
    
    # Test 2: API test
    try:
        response = requests.get(f"{base_url}/api/test", timeout=10)
        print(f"✅ API Test: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ API Test Failed: {e}")
    
    # Test 3: Admin customers endpoint (should return 401 without auth)
    try:
        response = requests.get(f"{base_url}/api/admin/customers", timeout=10)
        print(f"✅ Admin Customers: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Admin Customers Failed: {e}")
    
    # Test 4: Admin dashboard endpoint (should return 401 without auth)
    try:
        response = requests.get(f"{base_url}/api/admin/dashboard", timeout=10)
        print(f"✅ Admin Dashboard: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Admin Dashboard Failed: {e}")
    
    # Test 5: Products endpoint (should work without auth)
    try:
        response = requests.get(f"{base_url}/api/products", timeout=10)
        print(f"✅ Products: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Products Failed: {e}")

if __name__ == "__main__":
    test_railway_backend()
