#!/usr/bin/env python3

import asyncio
import sys
sys.path.append('.')

from app.database.connections import db_manager
from app.models.sql_models import Provider
from app.schemas.provider import VerificationStatus
from app.utils.security import hash_password, verify_password
from sqlalchemy import select, delete
import uuid

async def fix_rishi_provider():
    """Fix Rishi's provider account with proper password hashing."""
    
    # Rishi's credentials from the user query
    first_name = "Rishi"
    last_name = "Vyas"
    email = "rishi.vyas1110@gmail.com"
    phone_number = "+91-9421749384"
    password = "Test@123"
    specialization = "Cardiology"
    license_number = "123456789098"
    years_of_experience = 5
    clinic_street = "Near to your house"
    clinic_city = "Jalgaon"
    clinic_state = "Maharastra"
    clinic_zip = "444601"
    
    print("🔧 Fixing Rishi's provider account...")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print()
    
    # Initialize database
    db_manager.initialize()
    
    try:
        with db_manager.get_sql_session() as session:
            # Delete existing provider if exists
            delete_stmt = delete(Provider).where(Provider.email == email)
            session.execute(delete_stmt)
            session.commit()
            print(f"✅ Removed any existing provider with email: {email}")
            
            # Hash the password properly using the security module
            password_hash = hash_password(password)
            print(f"✅ Password hashed: {password_hash[:50]}...")
            
            # Test the hash immediately
            test_verify = verify_password(password, password_hash)
            print(f"✅ Hash verification test: {'PASS' if test_verify else 'FAIL'}")
            
            if not test_verify:
                print("❌ Hash verification failed. Cannot proceed.")
                return
            
            # Create new provider with exact data from user query
            provider = Provider(
                id=str(uuid.uuid4()),
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number,
                password_hash=password_hash,
                specialization=specialization,
                license_number=license_number,
                years_of_experience=years_of_experience,
                clinic_street=clinic_street,
                clinic_city=clinic_city,
                clinic_state=clinic_state,
                clinic_zip=clinic_zip,
                verification_status=VerificationStatus.VERIFIED,  # Set as verified
                is_active=True
            )
            
            session.add(provider)
            session.commit()
            
            print("✅ Provider created successfully!")
            
            # Verify the provider was stored correctly
            check_stmt = select(Provider).where(Provider.email == email)
            result = session.execute(check_stmt)
            db_provider = result.scalar_one()
            
            print("\n📋 Provider details in database:")
            print(f"ID: {db_provider.id}")
            print(f"Name: {db_provider.first_name} {db_provider.last_name}")
            print(f"Email: {db_provider.email}")
            print(f"Phone: {db_provider.phone_number}")
            print(f"Specialization: {db_provider.specialization}")
            print(f"License: {db_provider.license_number}")
            print(f"Experience: {db_provider.years_of_experience} years")
            print(f"Clinic: {db_provider.clinic_street}, {db_provider.clinic_city}, {db_provider.clinic_state} {db_provider.clinic_zip}")
            print(f"Verification: {db_provider.verification_status}")
            print(f"Active: {db_provider.is_active}")
            
            # Test password verification from database
            stored_verify = verify_password(password, db_provider.password_hash)
            print(f"\n✅ Database password verification: {'PASS' if stored_verify else 'FAIL'}")
            
            if stored_verify:
                print("\n🎉 SUCCESS! Rishi's provider account is now properly set up!")
                print("=" * 60)
                print("LOGIN CREDENTIALS:")
                print(f"📧 Email: {email}")
                print(f"🔐 Password: {password}")
                print("🌐 API Endpoint: POST /api/v1/provider/login")
                print("=" * 60)
                
                # Test with auth service
                print("\n🧪 Testing with AuthService...")
                from app.services.auth_service import AuthService
                from app.schemas.auth import ProviderLoginSchema
                
                login_data = ProviderLoginSchema(email=email, password=password)
                auth_service = AuthService()
                
                success, response_data = await auth_service.authenticate_provider(login_data)
                
                if success:
                    print("✅ AUTH SERVICE TEST: Login successful!")
                    print(f"Token: {response_data['data']['access_token'][:50]}...")
                else:
                    print("❌ Auth service test failed:")
                    print(f"Error: {response_data['message']}")
                    print(f"Error code: {response_data.get('error_code', 'N/A')}")
            else:
                print("❌ Database verification failed")
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_rishi_provider()) 