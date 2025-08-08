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

async def create_fresh_provider():
    """Create a completely fresh provider with clean bcrypt hash."""
    
    # Use a simpler test email and password
    test_email = "demo@healthfirst.com"
    test_password = "Demo123!"
    
    print("Creating fresh demo provider...")
    print(f"Email: {test_email}")
    print(f"Password: {test_password}")
    
    # Initialize database
    db_manager.initialize()
    
    try:
        with db_manager.get_sql_session() as session:
            # Delete any existing demo provider
            delete_stmt = delete(Provider).where(Provider.email == test_email)
            session.execute(delete_stmt)
            session.commit()
            print(f"Cleaned up any existing provider with email: {test_email}")
            
            # Create simple bcrypt hash
            password_bytes = test_password.encode('utf-8')
            salt = bcrypt.gensalt(rounds=10)  # Use lower rounds for compatibility
            hashed = bcrypt.hashpw(password_bytes, salt)
            password_hash = hashed.decode('utf-8')
            print(f"Password hash created: {password_hash[:30]}...")
            
            # Test the hash immediately
            test_result = bcrypt.checkpw(password_bytes, hashed)
            print(f"Hash test: {'✅ PASS' if test_result else '❌ FAIL'}")
            
            # Create new provider
            provider = Provider(
                id=str(uuid.uuid4()),
                first_name="Demo",
                last_name="Provider",
                email=test_email,
                phone_number="+1555000123",
                password_hash=password_hash,
                specialization="Family Medicine",
                license_number="DEMO789",
                years_of_experience=10,
                clinic_street="456 Demo Street",
                clinic_city="Demo City",
                clinic_state="Demo State",
                clinic_zip="54321",
                verification_status=VerificationStatus.VERIFIED,  # Set to verified!
                is_active=True
            )
            
            session.add(provider)
            session.commit()
            
            # Verify the provider was created
            check_stmt = select(Provider).where(Provider.email == test_email)
            result = session.execute(check_stmt)
            created_provider = result.scalar_one()
            
            print("\n✅ Fresh demo provider created successfully!")
            print(f"Provider ID: {created_provider.id}")
            print(f"Email: {created_provider.email}")
            print(f"Verification Status: {created_provider.verification_status}")
            print(f"Is Active: {created_provider.is_active}")
            
            # Test password again with the stored hash
            stored_hash = created_provider.password_hash.encode('utf-8')
            final_test = bcrypt.checkpw(password_bytes, stored_hash)
            print(f"Final verification test: {'✅ PASS' if final_test else '❌ FAIL'}")
            
            print("\n🎉 READY FOR FRONTEND TESTING!")
            print("=" * 50)
            print(f"📧 Email: {test_email}")
            print(f"🔐 Password: {test_password}")
            print(f"🌐 Backend URL: http://<your-ip>:8001")
            print(f"🔗 Login Endpoint: POST /api/v1/provider/login")
            print("=" * 50)
            
            # Create a quick curl example
            print("\n📋 Quick test with curl:")
            print(f"""curl -X POST "http://<your-ip>:8001/api/v1/provider/login" \\
-H "Content-Type: application/json" \\
-d '{{"email": "{test_email}", "password": "{test_password}"}}'""")
            
            return created_provider.id
            
    except Exception as e:
        print(f"❌ Error creating demo provider: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(create_fresh_provider()) 