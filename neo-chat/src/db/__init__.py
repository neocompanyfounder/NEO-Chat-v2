"""Database layer for NEO Chat."""

from .supabase_client import supabase_client, get_supabase_client

__all__ = ["supabase_client", "get_supabase_client"]
