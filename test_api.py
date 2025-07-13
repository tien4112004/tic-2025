#!/usr/bin/env python3
"""
Test script for E-commerce API endpoints
Run this script while the API server is running to test all endpoints
"""

import requests
import json
import io
from PIL import Image
import sys
import time

BASE_URL = "http://localhost:8000"

def create_test_image():
    """Create a simple test image"""
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes

def test_endpoint(name, method, url, **kwargs):
    """Test a single endpoint"""
    print(f"\n🧪 Testing {name}...")
    try:
        response = requests.request(method, url, **kwargs)
        print(f"   Status: {response.status_code}")
        
        if response.status_code < 400:
            print(f"   ✅ Success")
            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
                if isinstance(data, dict) and 'products' in data:
                    print(f"   📦 Found {len(data['products'])} products")
                    if 'pagination' in data:
                        print(f"   📄 Page {data['pagination']['page']}/{data['pagination']['total_pages']}")
                elif isinstance(data, list):
                    print(f"   📦 Found {len(data)} items")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection Error - Is the server running on {BASE_URL}?")
        return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False
    
    return response.status_code < 400

def main():
    print("🚀 Starting E-commerce API Tests")
    print(f"   Base URL: {BASE_URL}")
    
    success_count = 0
    total_tests = 0
    
    # Test 1: Health check
    total_tests += 1
    if test_endpoint("Health Check", "GET", f"{BASE_URL}/health"):
        success_count += 1
    
    # Test 2: Root endpoint
    total_tests += 1
    if test_endpoint("Root Endpoint", "GET", f"{BASE_URL}/"):
        success_count += 1
    
    # Test 3: Get all products (default)
    total_tests += 1
    if test_endpoint("Get Products (Default)", "GET", f"{BASE_URL}/products"):
        success_count += 1
    
    # Test 4: Get products with search
    total_tests += 1
    if test_endpoint("Search Products", "GET", f"{BASE_URL}/products?search=product"):
        success_count += 1
    
    # Test 5: Get products with category filter
    total_tests += 1
    if test_endpoint("Filter by Category", "GET", f"{BASE_URL}/products?category=Electronics"):
        success_count += 1
    
    # Test 6: Get products with price filter
    total_tests += 1
    if test_endpoint("Filter by Price", "GET", f"{BASE_URL}/products?min_price=50&max_price=100"):
        success_count += 1
    
    # Test 7: Get products with sorting
    total_tests += 1
    if test_endpoint("Sort by Price", "GET", f"{BASE_URL}/products?sort_by=price&sort_order=desc"):
        success_count += 1
    
    # Test 8: Get products with pagination
    total_tests += 1
    if test_endpoint("Pagination", "GET", f"{BASE_URL}/products?page=2&page_size=5"):
        success_count += 1
    
    # Test 9: Get categories
    total_tests += 1
    if test_endpoint("Get Categories", "GET", f"{BASE_URL}/products/categories"):
        success_count += 1
    
    # Test 10: Get brands
    total_tests += 1
    if test_endpoint("Get Brands", "GET", f"{BASE_URL}/products/brands"):
        success_count += 1
    
    # Test 11: Visual search service status
    total_tests += 1
    if test_endpoint("Visual Search Service Status", "GET", f"{BASE_URL}/services/status"):
        success_count += 1
    
    # Test 12: Image search with valid image
    total_tests += 1
    test_image = create_test_image()
    files = {'file': ('test.jpg', test_image, 'image/jpeg')}
    if test_endpoint("Image Search (Visual)", "POST", f"{BASE_URL}/search/image", files=files):
        success_count += 1
    
    # Test 13: Image search with invalid file type
    total_tests += 1
    text_file = io.StringIO("This is not an image")
    files = {'file': ('test.txt', text_file, 'text/plain')}
    response = requests.post(f"{BASE_URL}/search/image", files=files)
    print(f"\n🧪 Testing Image Search (Invalid File)...")
    print(f"   Status: {response.status_code}")
    if response.status_code == 400:
        print(f"   ✅ Correctly rejected invalid file")
        success_count += 1
    else:
        print(f"   ❌ Should have rejected invalid file")
    
    # Test 14: Invalid query parameters
    total_tests += 1
    response = requests.get(f"{BASE_URL}/products?page=0")  # Invalid page number
    print(f"\n🧪 Testing Invalid Parameters...")
    print(f"   Status: {response.status_code}")
    if response.status_code == 422:
        print(f"   ✅ Correctly validated parameters")
        success_count += 1
    else:
        print(f"   ❌ Should have validated parameters")
    
    # Summary
    print(f"\n📊 Test Results: {success_count}/{total_tests} tests passed")
    if success_count == total_tests:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {total_tests - success_count} tests failed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)