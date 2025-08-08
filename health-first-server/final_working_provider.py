#!/usr/bin/env python3

import asyncio
import sys
sys.path.append('.')

from app.database.connections import db_manager
from app.models.sql_models import Provider
from app.schemas.provider import VerificationStatus
from sqlalchemy import select, delete
import uuid
import bcrypt
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_bcrypt_hash(password: str) -> str:
    """Create bcrypt hash exactly as the security module does."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_bcrypt_hash(password: str, hash_str: str) -> bool:
    """Verify bcrypt hash exactly as the security module does."""
    return bcrypt.checkpw(password.encode('utf-8'), hash_str.encode('utf-8'))

async def create_final_provider():
    """Create the final working provider."""
    
    # Use simple credentials
    email = "provider@demo.com"
    password = "Demo123!"
    
    print("Creating final working provider...")
    print(f"Email: {email}")
    print(f"Password: {password}")
    
    # Initialize database
    db_manager.initialize()
    
    try:
        with db_manager.get_sql_session() as session:
            # Delete any existing provider
            delete_stmt = delete(Provider).where(Provider.email == email)
            session.execute(delete_stmt)
            session.commit()
            
            # Create hash
            password_hash = create_bcrypt_hash(password)
            print(f"Hash created: {password_hash[:40]}...")
            
            # Test verification immediately
            test_verify = verify_bcrypt_hash(password, password_hash)
            print(f"Immediate verification: {'✅ PASS' if test_verify else '❌ FAIL'}")
            
            if not test_verify:
                print("❌ Hash verification failed immediately. Stopping.")
                return
            
            # Create provider
            provider = Provider(
                id=str(uuid.uuid4()),
                first_name="Working",
                last_name="Provider", 
                email=email,
                phone_number="+1555123456",
                password_hash=password_hash,
                specialization="Internal Medicine",
                license_number="WORK123",
                years_of_experience=8,
                clinic_street="789 Working St",
                clinic_city="Working City",
                clinic_state="Working State", 
                clinic_zip="67890",
                verification_status=VerificationStatus.VERIFIED,
                is_active=True
            )
            
            session.add(provider)
            session.commit()
            
            # Verify from database
            check_stmt = select(Provider).where(Provider.email == email)
            result = session.execute(check_stmt)
            db_provider = result.scalar_one()
            
            print(f"\nProvider stored in database:")
            print(f"ID: {db_provider.id}")
            print(f"Email: {db_provider.email}")
            print(f"Status: {db_provider.verification_status}")
            print(f"Active: {db_provider.is_active}")
            
            # Test with stored hash
            stored_verify = verify_bcrypt_hash(password, db_provider.password_hash)
            print(f"Database hash verification: {'✅ PASS' if stored_verify else '❌ FAIL'}")
            
            if stored_verify:
                print("\n🎉 SUCCESS! Provider ready for frontend testing!")
                print("=" * 60)
                print(f"📧 Email: {email}")
                print(f"🔐 Password: {password}")
                print(f"🌐 Backend: http://<your-ip>:8001")
                print(f"🔗 Login: POST /api/v1/provider/login")
                print("=" * 60)
                
                # Test with actual auth service
                print("\n🧪 Testing with auth service...")
                from app.services.auth_service import AuthService
                from app.schemas.auth import ProviderLoginSchema
                
                login_data = ProviderLoginSchema(email=email, password=password)
                auth_service = AuthService()
                
                success, response = await auth_service.authenticate_provider(login_data)
                
                if success:
                    print("✅ AUTH SERVICE TEST PASSED!")
                    print(f"Token: {response['data']['access_token'][:30]}...")
                else:
                    print("❌ Auth service test failed:")
                    print(f"Error: {response['message']}")
            else:
                print("❌ Database verification failed")
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_final_provider()) 