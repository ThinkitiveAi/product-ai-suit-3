#!/usr/bin/env python3

import asyncio
import sys
sys.path.append('.')

from app.database.connections import db_manager
from app.services.auth_service import AuthService
from app.schemas.auth import ProviderLoginSchema
import sqlite3

async def test_rishi_login_fixed():
    """Test Rishi's login with proper database initialization."""
    
    email = "rishi.vyas1110@gmail.com"
    password = "Test@123"
    
    print("Testing Rishi's login credentials (Fixed)...")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print()
    
    # Initialize database properly
    print("🔧 Initializing database...")
    db_manager.initialize()
    print("✅ Database initialized")
    print()
    
    # Check current database state
    conn = sqlite3.connect('healthfirst.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT email, password_hash, verification_status, is_active 
        FROM providers 
        WHERE email = ?
    ''', (email,))
    
    result = cursor.fetchone()
    
    if result:
        db_email, password_hash, verification_status, is_active = result
        print("📋 Current provider status:")
        print(f"Email: {db_email}")
        print(f"Password hash: {password_hash[:50]}...")
        print(f"Verification status: {verification_status}")
        print(f"Is active: {is_active}")
        print()
    else:
        print("❌ Provider not found in database")
        conn.close()
        return
    
    conn.close()
    
    # Test the full auth service with proper initialization
    print("🔍 Testing with AuthService (with proper database)...")
    
    try:
        login_data = ProviderLoginSchema(email=email, password=password)
        auth_service = AuthService()
        
        success, response_data = await auth_service.authenticate_provider(login_data)
        
        if success:
            print("✅ AUTH SERVICE: Login successful!")
            print(f"Message: {response_data['message']}")
            print(f"Token: {response_data['data']['access_token'][:50]}...")
            print(f"Provider ID: {response_data['data']['provider']['provider_id']}")
            print(f"Provider name: {response_data['data']['provider']['first_name']} {response_data['data']['provider']['last_name']}")
            print("\n🎉 SUCCESS! You can now use these credentials to login via the API!")
        else:
            print("❌ AUTH SERVICE: Login failed")
            print(f"Error: {response_data['message']}")
            print(f"Error code: {response_data.get('error_code', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Error during authentication: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rishi_login_fixed()) 