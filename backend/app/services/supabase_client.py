"""Supabase client for user profiles and session persistence."""

from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_ANON_KEY

_client: Client | None = None


def get_client() -> Client | None:
    global _client
    if _client is None and SUPABASE_URL and SUPABASE_ANON_KEY:
        _client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    return _client
