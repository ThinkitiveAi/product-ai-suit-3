#!/usr/bin/env python3

import asyncio
import sys
sys.path.append('.')

from app.database.connections import db_manager
from app.services.provider_repository import get_provider_repository
import sqlite3

async def debug_provider_data():
    """Debug what data the repository returns vs database."""
    
    email = "rishi.vyas1110@gmail.com"
    
    print("🔍 Debugging provider data retrieval...")
    print(f"Email: {email}")
    print()
    
    # Initialize database
    db_manager.initialize()
    
    # Check raw database data
    print("📊 Raw database data:")
    conn = sqlite3.connect('healthfirst.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM providers WHERE email = ?', (email,))
    columns = [description[0] for description in cursor.description]
    result = cursor.fetchone()
    
    if result:
        for i, value in enumerate(result):
            print(f"  {columns[i]}: {value}")
    else:
        print("  ❌ Provider not found")
        return
    
    conn.close()
    print()
    
    # Check repository data
    print("🏪 Repository data:")
    repository = get_provider_repository()
    provider_data = await repository.get_provider_by_email(email)
    
    if provider_data:
        for key, value in provider_data.items():
            print(f"  {key}: {value}")
        
        # Check if password_hash is missing
        if 'password_hash' not in provider_data:
            print("\n❌ ISSUE FOUND: password_hash is missing from repository data!")
            print("The to_dict() method in the Provider model doesn't include password_hash")
        else:
            print(f"\n✅ password_hash found: {provider_data['password_hash']}")
    else:
        print("  ❌ Provider not found")

if __name__ == "__main__":
    asyncio.run(debug_provider_data()) 