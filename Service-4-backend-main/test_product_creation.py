import requests
import json

base_url = 'https://web-production-f50e6.up.railway.app'

print("Testing Product Creation on Railway...")
print("=" * 50)

# Test 1: Try to create a product with the exact data frontend sends
try:
    product_data = {
        "name": "Test Product",
        "description": "Test Description", 
        "price": 100.0,
        "stock_quantity": 10
    }
    
    response = requests.post(f"{base_url}/api/products", 
                           json=product_data,
                           timeout=10)
    print(f"✅ Product Creation (no auth): {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ Product Creation Failed: {e}")

# Test 2: Try with image_url to see if that's the issue
try:
    product_data_with_image = {
        "name": "Test Product 2",
        "description": "Test Description 2",
        "price": 200.0,
        "stock_quantity": 20,
        "image_url": "test.jpg"
    }
    
    response = requests.post(f"{base_url}/api/products", 
                           json=product_data_with_image,
                           timeout=10)
    print(f"✅ Product Creation with image_url: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ Product Creation with image_url Failed: {e}")

print("\n" + "=" * 50)
print("Test completed!")
