"""Database layer for NEO Chat with PostgreSQL and pgvector support."""

from .supabase_client import (
    db_client,
    get_db_client,
    supabase_client,  # Legacy alias for backward compatibility
    get_supabase_client,  # Legacy alias for backward compatibility
    DatabaseClient
)

__all__ = [
    "db_client",
    "get_db_client",
    "DatabaseClient",
    # Legacy exports for backward compatibility
    "supabase_client",
    "get_supabase_client",
]
