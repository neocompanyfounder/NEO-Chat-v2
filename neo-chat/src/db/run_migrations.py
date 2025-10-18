#!/usr/bin/env python3
"""Run database migrations on startup."""

import asyncio
import os
from pathlib import Path
from src.db import get_db_client
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def run_migrations():
    """Run all pending database migrations."""
    try:
        # Get database client (assumes it's already connected)
        db_client = get_db_client()
        
        logger.info("Starting database migrations...")
        
        # Get migrations directory
        migrations_dir = Path(__file__).parent / "migrations"
        
        # Get all SQL migration files sorted by name
        migration_files = sorted(migrations_dir.glob("*.sql"))
        
        logger.info(f"Found {len(migration_files)} migration files")
        
        # Run each migration
        for migration_file in migration_files:
            logger.info(f"Running migration: {migration_file.name}")
            
            # Read migration SQL
            with open(migration_file, "r") as f:
                sql = f.read()
            
            # Execute migration
            try:
                async with db_client.acquire() as conn:
                    await conn.execute(sql)
                    
                logger.info(f"✅ Migration completed: {migration_file.name}")
                
            except Exception as e:
                # Check if it's a "already exists" error (which is okay)
                if "already exists" in str(e).lower():
                    logger.info(f"⏭️  Migration already applied: {migration_file.name}")
                else:
                    logger.error(f"❌ Migration failed: {migration_file.name} - {e}")
                    # Continue with other migrations
        
        logger.info("✅ All migrations completed!")
        
    except Exception as e:
        logger.error(f"Migration process failed: {e}")
        raise


async def main():
    """Run migrations standalone."""
    db_client = get_db_client()
    await db_client.connect()
    try:
        await run_migrations()
    finally:
        await db_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
