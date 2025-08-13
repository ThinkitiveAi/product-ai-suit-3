#!/usr/bin/env python3

import asyncio
import sys
sys.path.append('.')

import sqlite3
import bcrypt
from app.utils.security import verify_password

async def test_rishi_login():
    """Test Rishi's login credentials and password verification."""
    
    email = "rishi.vyas1110@gmail.com"
    password = "Test@123"
    
    print("Testing Rishi's login credentials...")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print()
    
    # Connect to database and get provider data
    conn = sqlite3.connect('healthfirst.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT email, password_hash, verification_status, is_active 
        FROM providers 
        WHERE email = ?
    ''', (email,))
    
    result = cursor.fetchone()
    
    if not result:
        print("❌ Provider not found in database")
        return
    
    db_email, password_hash, verification_status, is_active = result
    
    print("📋 Provider details from database:")
    print(f"Email: {db_email}")
    print(f"Password hash: {password_hash[:50]}...")
    print(f"Verification status: {verification_status}")
    print(f"Is active: {is_active}")
    print()
    
    # Test password verification
    print("🔐 Testing password verification...")
    password_match = verify_password(password, password_hash)
    print(f"Password verification: {'✅ PASS' if password_match else '❌ FAIL'}")
    
    # Test with bcrypt directly
    bcrypt_match = bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    print(f"Direct bcrypt check: {'✅ PASS' if bcrypt_match else '❌ FAIL'}")
    print()
    
    # Test the full auth service
    print("🔍 Testing with AuthService...")
    from app.services.auth_service import AuthService
    from app.schemas.auth import ProviderLoginSchema
    
    login_data = ProviderLoginSchema(email=email, password=password)
    auth_service = AuthService()
    
    success, response_data = await auth_service.authenticate_provider(login_data)
    
    if success:
        print("✅ AUTH SERVICE: Login successful!")
        print(f"Token: {response_data['data']['access_token'][:30]}...")
    else:
        print("❌ AUTH SERVICE: Login failed")
        print(f"Error: {response_data['message']}")
        print(f"Error code: {response_data.get('error_code', 'N/A')}")
        
        # Check the specific failure reason
        if response_data.get('error_code') == 'ACCOUNT_NOT_VERIFIED':
            print("\n💡 SOLUTION: The account needs to be verified!")
            print("The password is correct but verification_status is PENDING instead of VERIFIED")
    
    conn.close()

if __name__ == "__main__":
    asyncio.run(test_rishi_login()) 