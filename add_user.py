"""Script to add a user to the database."""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables from neo-chat/.env
load_dotenv('neo-chat/.env')

async def add_user():
    """Add user to the database."""
    phone_number = "+966556265604"
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return
    
    print(f"Connecting to database...")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)
        
        # Check if user already exists
        existing_user = await conn.fetchrow(
            "SELECT id, phone_number, created_at FROM users WHERE phone_number = $1",
            phone_number
        )
        
        if existing_user:
            print(f"✅ User already exists:")
            print(f"   ID: {existing_user['id']}")
            print(f"   Phone: {existing_user['phone_number']}")
            print(f"   Created: {existing_user['created_at']}")
        else:
            # Create new user
            new_user = await conn.fetchrow(
                "INSERT INTO users (phone_number) VALUES ($1) RETURNING id, phone_number, created_at",
                phone_number
            )
            print(f"✅ User created successfully:")
            print(f"   ID: {new_user['id']}")
            print(f"   Phone: {new_user['phone_number']}")
            print(f"   Created: {new_user['created_at']}")
        
        await conn.close()
        print("\n✅ Done!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(add_user())
