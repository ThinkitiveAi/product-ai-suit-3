#!/usr/bin/env python3

import asyncio
import sys
sys.path.append('.')

from app.database.connections import db_manager
from app.models.sql_models import Provider
from app.schemas.provider import VerificationStatus
from app.utils.security import hash_password
from sqlalchemy import select, delete
import uuid

async def create_test_provider():
    """Create a verified test provider account for frontend testing."""
    
    # Test provider credentials
    test_email = "testprovider@example.com"
    test_password = "TestPass123!"
    
    print("Creating test provider account...")
    print(f"Email: {test_email}")
    print(f"Password: {test_password}")
    
    # Initialize database
    db_manager.initialize()
    
    try:
        with db_manager.get_sql_session() as session:
            # First, delete any existing test provider
            delete_stmt = delete(Provider).where(Provider.email == test_email)
            session.execute(delete_stmt)
            session.commit()
            print(f"Removed any existing provider with email: {test_email}")
            
            # Hash the password properly
            password_hash = hash_password(test_password)
            print(f"Password hashed successfully: {password_hash[:50]}...")
            
            # Create new provider with verified status
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
                verification_status=VerificationStatus.VERIFIED,  # Set to verified!
                is_active=True
            )
            
            session.add(provider)
            session.commit()
            
            # Verify the provider was created correctly
            check_stmt = select(Provider).where(Provider.email == test_email)
            result = session.execute(check_stmt)
            created_provider = result.scalar_one()
            
            print("\n✅ Test provider created successfully!")
            print(f"Provider ID: {created_provider.id}")
            print(f"Email: {created_provider.email}")
            print(f"Verification Status: {created_provider.verification_status}")
            print(f"Is Active: {created_provider.is_active}")
            print(f"Specialization: {created_provider.specialization}")
            
            # Test password verification
            from app.utils.security import verify_password
            is_valid = verify_password(test_password, created_provider.password_hash)
            print(f"Password verification test: {'✅ PASS' if is_valid else '❌ FAIL'}")
            
            print("\n🎉 Frontend developer can now use these credentials:")
            print(f"📧 Email: {test_email}")
            print(f"🔐 Password: {test_password}")
            print(f"🌐 Backend URL: http://<your-ip>:8001")
            print(f"🔗 Login endpoint: POST http://<your-ip>:8001/api/v1/provider/login")
            
            return created_provider.id
            
    except Exception as e:
        print(f"❌ Error creating test provider: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(create_test_provider()) 