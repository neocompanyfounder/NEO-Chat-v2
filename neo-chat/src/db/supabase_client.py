"""Supabase database client with connection pooling."""

from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
import asyncpg
from asyncpg import Pool

from ..utils.config import settings
from ..utils.logger import logger


class SupabaseClient:
    """Supabase PostgreSQL client with connection pooling via Supavisor.
    
    Uses asyncpg for async PostgreSQL connections with connection pooling.
    Connects via Supavisor (port 6543) for better connection management.
    """
    
    def __init__(self):
        """Initialize Supabase client."""
        self._pool: Optional[Pool] = None
        
    async def connect(self) -> None:
        """Create connection pool.
        
        Connects to Supabase via Supavisor pooler (port 6543) as specified in FR-016a.
        Uses SSL for secure connections.
        """
        if self._pool is not None:
            logger.warning("Connection pool already exists")
            return
            
        try:
            # Parse connection string
            # Format: postgresql://user:password@host:port/database
            self._pool = await asyncpg.create_pool(
                dsn=settings.SUPABASE_URL,
                min_size=5,
                max_size=20,
                command_timeout=settings.SUPABASE_TIMEOUT,
                server_settings={
                    'application_name': 'neo-chat',
                }
            )
            
            logger.info(
                "Connected to Supabase",
                extra={
                    "event_type": "database_connected",
                    "metadata": {
                        "pool_size": f"5-20",
                        "timeout": settings.SUPABASE_TIMEOUT
                    }
                }
            )
            
        except Exception as e:
            logger.error(
                f"Failed to connect to Supabase: {e}",
                extra={
                    "event_type": "database_connection_failed",
                    "metadata": {"error": str(e)}
                }
            )
            raise
    
    async def disconnect(self) -> None:
        """Close connection pool."""
        if self._pool is None:
            return
            
        try:
            await self._pool.close()
            self._pool = None
            
            logger.info(
                "Disconnected from Supabase",
                extra={"event_type": "database_disconnected"}
            )
            
        except Exception as e:
            logger.error(
                f"Error disconnecting from Supabase: {e}",
                extra={
                    "event_type": "database_disconnection_error",
                    "metadata": {"error": str(e)}
                }
            )
    
    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator:
        """Acquire a connection from the pool.
        
        Yields:
            Database connection
            
        Example:
            async with supabase_client.acquire() as conn:
                result = await conn.fetch("SELECT * FROM users")
        """
        if self._pool is None:
            raise RuntimeError("Connection pool not initialized. Call connect() first.")
        
        async with self._pool.acquire() as connection:
            yield connection
    
    async def execute(self, query: str, *args, user_id: Optional[str] = None) -> str:
        """Execute a query that doesn't return rows.
        
        Args:
            query: SQL query
            *args: Query parameters
            user_id: Optional user ID for RLS context
            
        Returns:
            Query status
        """
        async with self.acquire() as conn:
            if user_id:
                await conn.execute(f"SET app.current_user_id = '{user_id}'")
            
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args, user_id: Optional[str] = None) -> list:
        """Fetch multiple rows.
        
        Args:
            query: SQL query
            *args: Query parameters
            user_id: Optional user ID for RLS context
            
        Returns:
            List of records
        """
        async with self.acquire() as conn:
            if user_id:
                await conn.execute(f"SET app.current_user_id = '{user_id}'")
            
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args, user_id: Optional[str] = None):
        """Fetch a single row.
        
        Args:
            query: SQL query
            *args: Query parameters
            user_id: Optional user ID for RLS context
            
        Returns:
            Single record or None
        """
        async with self.acquire() as conn:
            if user_id:
                await conn.execute(f"SET app.current_user_id = '{user_id}'")
            
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args, user_id: Optional[str] = None):
        """Fetch a single value.
        
        Args:
            query: SQL query
            *args: Query parameters
            user_id: Optional user ID for RLS context
            
        Returns:
            Single value or None
        """
        async with self.acquire() as conn:
            if user_id:
                await conn.execute(f"SET app.current_user_id = '{user_id}'")
            
            return await conn.fetchval(query, *args)
    
    async def health_check(self) -> bool:
        """Check database connection health.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            result = await self.fetchval("SELECT 1")
            return result == 1
        except Exception as e:
            logger.error(
                f"Database health check failed: {e}",
                extra={
                    "event_type": "health_check_failed",
                    "metadata": {"error": str(e)}
                }
            )
            return False


# Global client instance
supabase_client = SupabaseClient()


def get_supabase_client(settings=None) -> SupabaseClient:
    """Get the global Supabase client instance.
    
    Args:
        settings: Optional settings (ignored, for compatibility)
    
    Returns:
        SupabaseClient instance
    """
    return supabase_client
