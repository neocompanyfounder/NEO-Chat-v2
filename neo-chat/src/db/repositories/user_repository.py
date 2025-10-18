"""User repository for database operations."""

from typing import Optional
from uuid import UUID

from ...models.user import User, UserCreate, UserUpdate
from ...utils.logger import logger
from ..supabase_client import SupabaseClient


class UserRepository:
    """Repository for user database operations."""
    
    def __init__(self, db_client: SupabaseClient):
        """Initialize repository.
        
        Args:
            db_client: Supabase database client
        """
        self.db = db_client
    
    async def create(self, user: UserCreate) -> User:
        """Create a new user.
        
        Args:
            user: User creation data
            
        Returns:
            Created user
        """
        query = """
            INSERT INTO users (phone_number)
            VALUES ($1)
            RETURNING id, phone_number, created_at, updated_at
        """
        
        row = await self.db.fetchrow(query, user.phone_number)
        
        logger.info(
            f"Created user: {user.phone_number}",
            extra={
                "event_type": "user_created",
                "user_id": str(row['id']),
                "metadata": {"phone_number": user.phone_number}
            }
        )
        
        return User(**dict(row))
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            User if found, None otherwise
        """
        query = """
            SELECT id, phone_number, created_at, updated_at
            FROM users
            WHERE id = $1
        """
        
        row = await self.db.fetchrow(query, user_id, user_id=str(user_id))
        
        if row:
            return User(**dict(row))
        return None
    
    async def get_by_phone(self, phone_number: str) -> Optional[dict]:
        """Get user by phone number.
        
        Args:
            phone_number: User's phone number in E.164 format
            
        Returns:
            User dict if found, None otherwise
        """
        query = """
            SELECT id, phone_number, name, created_at, updated_at
            FROM users
            WHERE phone_number = $1
        """
        
        row = await self.db.fetchrow(query, phone_number)
        
        if row:
            return dict(row)
        return None
    
    async def get_or_create(self, phone_number: str, name: Optional[str] = None) -> dict:
        """Get existing user or create new one.
        
        Args:
            phone_number: User's phone number in E.164 format
            name: Optional user name
            
        Returns:
            Existing or newly created user as dict
        """
        # Try to get existing user
        query_select = """
            SELECT id, phone_number, name, created_at, updated_at
            FROM users
            WHERE phone_number = $1
        """
        
        row = await self.db.fetchrow(query_select, phone_number)
        
        if row:
            return dict(row)
        
        # Create new user
        query_insert = """
            INSERT INTO users (phone_number, name)
            VALUES ($1, $2)
            RETURNING id, phone_number, name, created_at, updated_at
        """
        
        row = await self.db.fetchrow(query_insert, phone_number, name)
        
        logger.info(
            f"Created user: {phone_number}",
            extra={
                "event_type": "user_created",
                "user_id": str(row['id']),
                "metadata": {"phone_number": phone_number, "name": name}
            }
        )
        
        return dict(row)
    
    async def update(self, user_id: UUID, user_update: UserUpdate) -> Optional[User]:
        """Update user.
        
        Args:
            user_id: User's unique identifier
            user_update: Update data
            
        Returns:
            Updated user if found, None otherwise
        """
        if not user_update.phone_number:
            return await self.get_by_id(user_id)
        
        query = """
            UPDATE users
            SET phone_number = $1, updated_at = NOW()
            WHERE id = $2
            RETURNING id, phone_number, created_at, updated_at
        """
        
        row = await self.db.fetchrow(
            query,
            user_update.phone_number,
            user_id,
            user_id=str(user_id)
        )
        
        if row:
            logger.info(
                f"Updated user: {user_id}",
                extra={
                    "event_type": "user_updated",
                    "user_id": str(user_id)
                }
            )
            return User(**dict(row))
        return None
    
    async def delete(self, user_id: UUID) -> bool:
        """Delete user and all associated data.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            True if deleted, False if not found
        """
        query = "DELETE FROM users WHERE id = $1"
        
        result = await self.db.execute(query, user_id, user_id=str(user_id))
        
        deleted = result == "DELETE 1"
        
        if deleted:
            logger.info(
                f"Deleted user: {user_id}",
                extra={
                    "event_type": "user_deleted",
                    "user_id": str(user_id)
                }
            )
        
        return deleted
    
    async def list_users(self, limit: int = 10, offset: int = 0) -> list:
        """List all users with pagination.
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            List of user dicts
        """
        query = """
            SELECT id, phone_number, name, created_at, updated_at
            FROM users
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """
        
        rows = await self.db.fetch(query, limit, offset)
        
        return [dict(row) for row in rows]
