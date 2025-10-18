"""PostgreSQL database client with pgvector support and connection pooling."""

from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
import asyncpg
from asyncpg import Pool

from ..utils.config import settings
from ..utils.logger import logger


class DatabaseClient:
    """PostgreSQL client with pgvector support and connection pooling.
    
    Uses asyncpg for async PostgreSQL connections with connection pooling.
    Provides vector operations via the pgvector extension.
    """
    
    def __init__(self):
        """Initialize database client."""
        self._pool: Optional[Pool] = None
        self._vector_registered: bool = False
        
    async def connect(self) -> None:
        """Create connection pool and register pgvector types.
        
        Creates asyncpg connection pool and registers pgvector extension
        for vector operations.
        """
        if self._pool is not None:
            logger.warning("Connection pool already exists")
            return
            
        try:
            # Parse connection string
            # Format: postgresql://user:password@host:port/database
            self._pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_URL,
                min_size=5,
                max_size=20,
                command_timeout=settings.DATABASE_TIMEOUT,
                server_settings={
                    'application_name': 'neo-chat',
                },
                init=self._init_connection
            )
            
            logger.info(
                "Connected to PostgreSQL with pgvector",
                extra={
                    "event_type": "database_connected",
                    "metadata": {
                        "pool_size": "5-20",
                        "timeout": settings.DATABASE_TIMEOUT,
                        "pgvector_enabled": True
                    }
                }
            )
            
        except Exception as e:
            logger.error(
                f"Failed to connect to database: {e}",
                extra={
                    "event_type": "database_connection_failed",
                    "metadata": {"error": str(e)}
                }
            )
            raise
    
    async def _init_connection(self, conn) -> None:
        """Initialize connection with pgvector support.
        
        Registers pgvector types for the connection.
        
        Args:
            conn: asyncpg connection
        """
        if not self._vector_registered:
            try:
                # Register pgvector types
                from pgvector.asyncpg import register_vector
                await register_vector(conn)
                self._vector_registered = True
                logger.debug("pgvector types registered")
            except ImportError:
                logger.warning(
                    "pgvector package not installed, vector operations may not work correctly"
                )
            except Exception as e:
                logger.warning(f"Failed to register pgvector types: {e}")
    
    async def disconnect(self) -> None:
        """Close connection pool."""
        if self._pool is None:
            return
            
        try:
            await self._pool.close()
            self._pool = None
            
            logger.info(
                "Disconnected from database",
                extra={"event_type": "database_disconnected"}
            )
            
        except Exception as e:
            logger.error(
                f"Error disconnecting from database: {e}",
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
            async with db_client.acquire() as conn:
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
db_client = DatabaseClient()

# Legacy aliases for backward compatibility
supabase_client = db_client


def get_db_client(settings=None) -> DatabaseClient:
    """Get the global database client instance.
    
    Args:
        settings: Optional settings (ignored, for compatibility)
    
    Returns:
        DatabaseClient instance
    """
    return db_client


def get_supabase_client(settings=None) -> DatabaseClient:
    """Get the global database client instance.
    
    Legacy function name for backward compatibility.
    
    Args:
        settings: Optional settings (ignored, for compatibility)
    
    Returns:
        DatabaseClient instance
    """
    return db_client
