#!/usr/bin/env python3

import asyncio
import sys
sys.path.append('.')

from app.services.auth_service import AuthService
from app.schemas.auth import ProviderLoginSchema
from app.database.connections import db_manager

async def test_demo_login():
    """Test login with the demo provider."""
    
    test_email = "demo@healthfirst.com"
    test_password = "Demo123!"
    
    print("🧪 Testing demo provider login...")
    print(f"Email: {test_email}")
    print(f"Password: {test_password}")
    
    try:
        # Initialize database
        db_manager.initialize()
        
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
            print("\n🎉 LOGIN SUCCESSFUL!")
            print(f"Access Token: {response_data['data']['access_token'][:30]}...")
            print(f"Token Type: {response_data['data']['token_type']}")
            print(f"Expires In: {response_data['data']['expires_in']} seconds")
            print(f"Provider: {response_data['data']['provider']['first_name']} {response_data['data']['provider']['last_name']}")
            print(f"Specialization: {response_data['data']['provider']['specialization']}")
            print(f"Status: {response_data['data']['provider']['verification_status']}")
            print("\n✅ AUTHENTICATION WORKING CORRECTLY!")
        else:
            print("\n❌ LOGIN FAILED!")
            print(f"Error: {response_data['message']}")
            print(f"Error Code: {response_data.get('error_code', 'Unknown')}")
            
    except Exception as e:
        print(f"\n❌ Login test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_demo_login()) 