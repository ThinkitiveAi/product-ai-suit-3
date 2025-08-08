#!/usr/bin/env python3

import asyncio
import sys
sys.path.append('.')

from app.database.connections import db_manager
from app.models.sql_models import Provider
from app.schemas.provider import VerificationStatus
from sqlalchemy import select, update
import bcrypt

async def fix_test_provider():
    """Fix the test provider by using direct bcrypt instead of passlib."""
    
    test_email = "testprovider@example.com"
    test_password = "TestPass123!"
    
    print("Fixing test provider password hash...")
    print(f"Email: {test_email}")
    print(f"Password: {test_password}")
    
    # Initialize database
    db_manager.initialize()
    
    try:
        with db_manager.get_sql_session() as session:
            # Hash password using direct bcrypt
            salt = bcrypt.gensalt(rounds=12)
            password_hash = bcrypt.hashpw(test_password.encode('utf-8'), salt).decode('utf-8')
            print(f"New password hash: {password_hash[:50]}...")
            
            # Update the existing provider with the new hash
            update_stmt = update(Provider).where(Provider.email == test_email).values(
                password_hash=password_hash,
                verification_status=VerificationStatus.VERIFIED,
                is_active=True
            )
            result = session.execute(update_stmt)
            session.commit()
            
            if result.rowcount == 0:
                print("No provider found to update. Creating new one...")
                # Create new provider if none exists
                import uuid
                provider = Provider(
                    id=str(uuid.uuid4()),
                    first_name="Test",
                    last_name="Provider",
                    email=test_email,
                    phone_number="+1234567890",
                    password_hash=password_hash,
                    specialization="General Medicine",
                    license_number="TEST123456",
                    years_of_experience=5,
                    clinic_street="123 Test Street",
                    clinic_city="Test City",
                    clinic_state="Test State",
                    clinic_zip="12345",
                    verification_status=VerificationStatus.VERIFIED,
                    is_active=True
                )
                session.add(provider)
                session.commit()
                print("New provider created!")
            else:
                print(f"Updated {result.rowcount} provider(s)")
            
            # Verify the provider
            check_stmt = select(Provider).where(Provider.email == test_email)
            result = session.execute(check_stmt)
            provider = result.scalar_one()
            
            # Test password verification using bcrypt directly
            is_valid = bcrypt.checkpw(test_password.encode('utf-8'), provider.password_hash.encode('utf-8'))
            print(f"Direct bcrypt verification: {'✅ PASS' if is_valid else '❌ FAIL'}")
            
            print("\n✅ Test provider fixed successfully!")
            print(f"Provider ID: {provider.id}")
            print(f"Email: {provider.email}")
            print(f"Verification Status: {provider.verification_status}")
            print(f"Is Active: {provider.is_active}")
            
            print("\n🎉 Frontend developer credentials:")
            print(f"📧 Email: {test_email}")
            print(f"🔐 Password: {test_password}")
            
    except Exception as e:
        print(f"❌ Error fixing test provider: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(fix_test_provider()) 