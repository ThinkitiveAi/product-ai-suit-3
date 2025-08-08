#!/usr/bin/env python3

import asyncio
import sys
sys.path.append('.')

from app.services.auth_service import AuthService
from app.schemas.auth import ProviderLoginSchema
from app.database.connections import db_manager

async def test_login():
    """Test the login functionality with the created test provider."""
    
    test_email = "testprovider@example.com"
    test_password = "TestPass123!"
    
    print("🔐 Testing login functionality...")
    print(f"Email: {test_email}")
    print(f"Password: {test_password}")
    
    try:
        # Initialize database first
        db_manager.initialize()
        print("Database initialized...")
        
        # Create login data
        login_data = ProviderLoginSchema(
            email=test_email,
            password=test_password
        )
        
        # Initialize auth service
        auth_service = AuthService()
        
        # Attempt authentication
        success, response_data = await auth_service.authenticate_provider(login_data)
        
        if success:
            print("\n✅ LOGIN SUCCESSFUL!")
            print(f"Access Token: {response_data['data']['access_token'][:50]}...")
            print(f"Token Type: {response_data['data']['token_type']}")
            print(f"Expires In: {response_data['data']['expires_in']} seconds")
            print(f"Provider Name: {response_data['data']['provider']['first_name']} {response_data['data']['provider']['last_name']}")
            print(f"Specialization: {response_data['data']['provider']['specialization']}")
            print(f"Verification Status: {response_data['data']['provider']['verification_status']}")
        else:
            print("\n❌ LOGIN FAILED!")
            print(f"Error: {response_data['message']}")
            print(f"Error Code: {response_data.get('error_code', 'Unknown')}")
            
    except Exception as e:
        print(f"\n❌ Login test failed with exception: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_login()) 