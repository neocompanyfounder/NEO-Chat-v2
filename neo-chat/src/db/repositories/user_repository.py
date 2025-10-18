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
    
    async def get_by_phone(self, phone_number: str) -> Optional[User]:
        """Get user by phone number.
        
        Args:
            phone_number: User's phone number in E.164 format
            
        Returns:
            User if found, None otherwise
        """
        query = """
            SELECT id, phone_number, created_at, updated_at
            FROM users
            WHERE phone_number = $1
        """
        
        row = await self.db.fetchrow(query, phone_number)
        
        if row:
            return User(**dict(row))
        return None
    
    async def get_or_create(self, phone_number: str) -> User:
        """Get existing user or create new one.
        
        Args:
            phone_number: User's phone number in E.164 format
            
        Returns:
            Existing or newly created user
        """
        # Try to get existing user
        user = await self.get_by_phone(phone_number)
        
        if user:
            return user
        
        # Create new user
        return await self.create(UserCreate(phone_number=phone_number))
    
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
