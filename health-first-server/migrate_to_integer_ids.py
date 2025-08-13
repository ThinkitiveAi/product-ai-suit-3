#!/usr/bin/env python3

import asyncio
import sys
sys.path.append('.')

import sqlite3
import os
from app.database.connections import db_manager
from app.models.sql_models import Provider
from app.schemas.provider import VerificationStatus

async def migrate_to_integer_ids():
    """Migrate from UUID IDs to integer IDs while preserving data."""
    
    print("🔄 Migrating database from UUID IDs to integer IDs...")
    
    # Backup current data
    print("📦 Backing up existing provider data...")
    
    # Read existing provider data
    existing_providers = []
    if os.path.exists('healthfirst.db'):
        conn = sqlite3.connect('healthfirst.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT first_name, last_name, email, phone_number, password_hash, 
                       specialization, license_number, years_of_experience,
                       clinic_street, clinic_city, clinic_state, clinic_zip,
                       verification_status, is_active
                FROM providers
            ''')
            
            for row in cursor.fetchall():
                existing_providers.append({
                    'first_name': row[0],
                    'last_name': row[1],
                    'email': row[2],
                    'phone_number': row[3],
                    'password_hash': row[4],
                    'specialization': row[5],
                    'license_number': row[6],
                    'years_of_experience': row[7],
                    'clinic_street': row[8],
                    'clinic_city': row[9],
                    'clinic_state': row[10],
                    'clinic_zip': row[11],
                    'verification_status': row[12],
                    'is_active': bool(row[13])
                })
                
            print(f"✅ Found {len(existing_providers)} providers to migrate")
            
        except Exception as e:
            print(f"ℹ️  No existing providers table or data: {e}")
        
        conn.close()
    
    # Remove old database
    if os.path.exists('healthfirst.db'):
        os.remove('healthfirst.db')
        print("🗑️  Removed old database")
    
    # Initialize new database with integer IDs
    print("🏗️  Creating new database with integer IDs...")
    db_manager.initialize()
    
    # Recreate providers with new schema
    if existing_providers:
        print("📝 Migrating provider data...")
        
        with db_manager.get_sql_session() as session:
            for i, provider_data in enumerate(existing_providers, 1):
                # Convert verification status string to enum
                verification_status = VerificationStatus.VERIFIED if provider_data['verification_status'] == 'VERIFIED' else VerificationStatus.PENDING
                
                provider = Provider(
                    first_name=provider_data['first_name'],
                    last_name=provider_data['last_name'],
                    email=provider_data['email'],
                    phone_number=provider_data['phone_number'],
                    password_hash=provider_data['password_hash'],
                    specialization=provider_data['specialization'],
                    license_number=provider_data['license_number'],
                    years_of_experience=provider_data['years_of_experience'],
                    clinic_street=provider_data['clinic_street'],
                    clinic_city=provider_data['clinic_city'],
                    clinic_state=provider_data['clinic_state'],
                    clinic_zip=provider_data['clinic_zip'],
                    verification_status=verification_status,
                    is_active=provider_data['is_active']
                )
                
                session.add(provider)
                session.flush()  # Get the auto-generated ID
                
                print(f"✅ Migrated provider: {provider_data['email']} -> ID: {provider.id}")
            
            session.commit()
    
    # Verify migration
    print("\n🔍 Verifying migration...")
    with db_manager.get_sql_session() as session:
        providers = session.query(Provider).all()
        
        print("📊 Migrated providers:")
        for provider in providers:
            print(f"  ID: {provider.id} | {provider.first_name} {provider.last_name} | {provider.email}")
    
    print(f"\n🎉 Migration complete! {len(existing_providers)} providers migrated to integer IDs.")
    print("🔗 API endpoints now use simple integer IDs:")
    print("   GET /api/v1/provider/1")
    print("   POST /api/v1/provider/1/availability")

if __name__ == "__main__":
    asyncio.run(migrate_to_integer_ids()) 