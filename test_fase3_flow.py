#!/usr/bin/env python3
"""
Full FASE 3 integration test: Register → Login → Upload → Classify
"""
import requests
import json
import os
from pathlib import Path
from PIL import Image
import io

BASE_URL = "http://localhost:8000"
ML_URL = "http://localhost:8001"

# Test user
TEST_EMAIL = "fase3test@pilah.in"
TEST_PASSWORD = "TestPass123!@#"
TEST_NAME = "Fase 3 Tester"

def test_ml_health():
    """Test ML service health"""
    print("\n=== Testing ML Service Health ===")
    try:
        resp = requests.get(f"{ML_URL}/health", timeout=5)
        print(f"ML Health: {resp.status_code}")
        print(f"Response: {resp.json()}")
        return True
    except Exception as e:
        print(f"ML Health check failed: {e}")
        return False

def test_register():
    """Test user registration"""
    print("\n=== Testing Registration ===")
    payload = {
        "email": TEST_EMAIL,
        "name": TEST_NAME,
        "password": TEST_PASSWORD,
        "password2": TEST_PASSWORD
    }
    try:
        resp = requests.post(f"{BASE_URL}/api/users/register/", json=payload, timeout=10)
        print(f"Register status: {resp.status_code}")
        print(f"Response: {resp.json()}")
        return resp.status_code == 201
    except Exception as e:
        print(f"Register failed: {e}")
        return False

def test_login():
    """Test user login"""
    print("\n=== Testing Login ===")
    payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    try:
        resp = requests.post(f"{BASE_URL}/api/token/", json=payload, timeout=10)
        print(f"Login status: {resp.status_code}")
        data = resp.json()
        print(f"Response keys: {list(data.keys())}")
        
        if resp.status_code == 200 and "access" in data:
            token = data["access"]
            print(f"Access token obtained (first 20 chars): {token[:20]}...")
            return token
        return None
    except Exception as e:
        print(f"Login failed: {e}")
        return None

def create_test_image(filename="test_image.jpg", size=(200, 200)):
    """Create simple test image"""
    img = Image.new('RGB', size, color=(73, 109, 137))
    img.save(filename)
    return filename

def test_upload(token):
    """Test image upload"""
    print("\n=== Testing Image Upload ===")
    
    # Create test image
    img_path = create_test_image()
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        with open(img_path, 'rb') as f:
            files = {'file': f}
            data = {
                'file_name': os.path.basename(img_path),
                'file_size': os.path.getsize(img_path)
            }
            resp = requests.post(
                f"{BASE_URL}/api/uploads/create/",
                files=files,
                data=data,
                headers=headers,
                timeout=10
            )
        
        print(f"Upload status: {resp.status_code}")
        data = resp.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if resp.status_code == 201 and "id" in data:
            upload_id = data["id"]
            print(f"Upload successful, ID: {upload_id}")
            return upload_id
        return None
    except Exception as e:
        print(f"Upload failed: {e}")
        return None
    finally:
        if os.path.exists(img_path):
            os.remove(img_path)

def test_classify(token, upload_id):
    """Test classification"""
    print("\n=== Testing Classification ===")
    
    payload = {
        "upload_id": upload_id
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        resp = requests.post(
            f"{BASE_URL}/api/classifications/",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        print(f"Classification status: {resp.status_code}")
        data = resp.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if resp.status_code == 201:
            print(f"Classification successful!")
            print(f"Category: {data.get('category')}")
            print(f"Confidence: {data.get('confidence')}")
            return True
        return False
    except Exception as e:
        print(f"Classification failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("FASE 3 Integration Test - Full Flow")
    print("=" * 60)
    
    # Test ML service
    if not test_ml_health():
        print("\nWARNING: ML service not responding, continuing with tests...")
    
    # Register
    if not test_register():
        print("\nRegistration failed. Continuing with login...")
    
    # Login
    token = test_login()
    if not token:
        print("\nLogin failed. Cannot continue with upload/classify tests.")
        return
    
    # Upload
    upload_id = test_upload(token)
    if not upload_id:
        print("\nUpload failed. Cannot test classification.")
        return
    
    # Classify
    test_classify(token, upload_id)
    
    print("\n" + "=" * 60)
    print("Test flow completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
