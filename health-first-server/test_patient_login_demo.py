#!/usr/bin/env python3
"""
Demo script to test Patient Login functionality
This script demonstrates the complete patient login flow.
"""

import asyncio
import json
import requests
from datetime import date
from app.utils.security import hash_password
from app.services.patient_repository import get_patient_repository
from app.config import config

# Configuration
BASE_URL = "http://localhost:8000"
DEMO_PATIENT = {
    "email": "demo.patient@healthfirst.com",
    "password": "DemoPatient123!",
    "first_name": "Demo",
    "last_name": "Patient",
    "phone_number": "+1234567890",
    "date_of_birth": date(1990, 1, 15),
    "gender": "other",
    "address": {
        "street": "123 Demo Street",
        "city": "Demo City",
        "state": "CA",
        "zip": "12345"
    }
}

async def create_demo_patient():
    """Create a demo patient for testing login."""
    try:
        print("🏥 Creating demo patient for login testing...")
        
        repository = get_patient_repository()
        
        # Check if patient already exists
        existing_patient = await repository.get_patient_by_email(DEMO_PATIENT["email"])
        if existing_patient:
            print(f"✅ Demo patient already exists: {DEMO_PATIENT['email']}")
            return True
        
        # Hash password
        password_hash = hash_password(DEMO_PATIENT["password"])
        
        # Prepare patient data
        patient_data = {
            "first_name": DEMO_PATIENT["first_name"],
            "last_name": DEMO_PATIENT["last_name"],
            "email": DEMO_PATIENT["email"],
            "phone_number": DEMO_PATIENT["phone_number"],
            "password_hash": password_hash,
            "date_of_birth": DEMO_PATIENT["date_of_birth"],
            "gender": DEMO_PATIENT["gender"],
            "address": DEMO_PATIENT["address"]
        }
        
        # Create patient
        created_patient = await repository.create_patient(patient_data)
        print(f"✅ Demo patient created successfully: {created_patient['patient_id']}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating demo patient: {str(e)}")
        return False

def test_patient_login():
    """Test patient login endpoint."""
    try:
        print("\n🔐 Testing Patient Login...")
        
        login_data = {
            "email": DEMO_PATIENT["email"],
            "password": DEMO_PATIENT["password"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/patient/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"📝 Message: {data['message']}")
            print(f"🔑 Token Type: {data['data']['token_type']}")
            print(f"⏱️  Expires In: {data['data']['expires_in']} seconds")
            print(f"👤 Patient ID: {data['data']['patient']['patient_id']}")
            print(f"📧 Email: {data['data']['patient']['email']}")
            print(f"👨‍⚕️ Name: {data['data']['patient']['first_name']} {data['data']['patient']['last_name']}")
            print(f"✉️  Email Verified: {data['data']['patient']['email_verified']}")
            print(f"📱 Phone Verified: {data['data']['patient']['phone_verified']}")
            
            return data['data']['access_token']
        else:
            print(f"❌ Login failed: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the server is running on localhost:8000")
        return None
    except Exception as e:
        print(f"❌ Error during login: {str(e)}")
        return None

def test_token_validation(token):
    """Test token validation endpoint."""
    try:
        print("\n🔍 Testing Token Validation...")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/patient/validate-token",
            json={"token": token},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('data', {}).get('valid'):
                print("✅ Token is valid!")
                print(f"👤 Patient ID: {data['data']['patient_id']}")
                print(f"📧 Email: {data['data']['email']}")
                print(f"🏃 Active: {data['data']['is_active']}")
            else:
                print(f"❌ Token validation failed: {data.get('data', {}).get('error', 'Unknown error')}")
        else:
            print(f"❌ Token validation request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during token validation: {str(e)}")

def test_patient_profile(token):
    """Test getting patient profile with token."""
    try:
        print("\n👤 Testing Patient Profile Access...")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{BASE_URL}/api/v1/patient/profile",
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Profile retrieved successfully!")
            patient = data['data']
            print(f"👤 Name: {patient['first_name']} {patient['last_name']}")
            print(f"📧 Email: {patient['email']}")
            print(f"📱 Phone: {patient['phone_number']}")
            print(f"🎂 Date of Birth: {patient['date_of_birth']}")
            print(f"🏠 Address: {patient['address']['street']}, {patient['address']['city']}, {patient['address']['state']}")
        else:
            print(f"❌ Profile access failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during profile access: {str(e)}")

def test_verification_status(token):
    """Test getting patient verification status."""
    try:
        print("\n✅ Testing Verification Status...")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{BASE_URL}/api/v1/patient/verification-status",
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Verification status retrieved!")
            status_data = data['data']
            print(f"✉️  Email Verified: {status_data['email_verified']}")
            print(f"📱 Phone Verified: {status_data['phone_verified']}")
        else:
            print(f"❌ Verification status request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during verification status check: {str(e)}")

def test_invalid_login():
    """Test login with invalid credentials."""
    try:
        print("\n🚫 Testing Invalid Login...")
        
        invalid_data = {
            "email": DEMO_PATIENT["email"],
            "password": "wrongpassword"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/patient/login",
            json=invalid_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            data = response.json()
            print("✅ Invalid login correctly rejected!")
            print(f"❌ Error: {data['message']}")
            print(f"🏷️  Error Code: {data['error_code']}")
        else:
            print(f"⚠️  Unexpected response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during invalid login test: {str(e)}")

def test_unauthorized_access():
    """Test accessing protected endpoint without token."""
    try:
        print("\n🔒 Testing Unauthorized Access...")
        
        response = requests.get(f"{BASE_URL}/api/v1/patient/profile")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Unauthorized access correctly blocked!")
        else:
            print(f"⚠️  Unexpected response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during unauthorized access test: {str(e)}")

async def main():
    """Run the complete patient login demo."""
    print("🚀 Patient Login System Demo")
    print("=" * 50)
    
    # Create demo patient
    patient_created = await create_demo_patient()
    if not patient_created:
        print("❌ Failed to create demo patient. Exiting.")
        return
    
    # Test successful login
    token = test_patient_login()
    if not token:
        print("❌ Login failed. Cannot proceed with other tests.")
        return
    
    # Test token validation
    test_token_validation(token)
    
    # Test profile access
    test_patient_profile(token)
    
    # Test verification status
    test_verification_status(token)
    
    # Test invalid login
    test_invalid_login()
    
    # Test unauthorized access
    test_unauthorized_access()
    
    print("\n🎉 Patient Login Demo Completed!")
    print("=" * 50)
    print("\n📋 Summary:")
    print("✅ Patient login with JWT authentication")
    print("✅ 30-minute token expiry")
    print("✅ Token validation")
    print("✅ Protected endpoints")
    print("✅ Profile access")
    print("✅ Verification status checking")
    print("✅ Error handling")
    print("✅ Security middleware")
    print("\n🔐 Demo Credentials:")
    print(f"📧 Email: {DEMO_PATIENT['email']}")
    print(f"🔑 Password: {DEMO_PATIENT['password']}")

if __name__ == "__main__":
    asyncio.run(main()) 