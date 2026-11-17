from typing import Optional
from supabase import create_client, Client
from backend.core.config import settings

_supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    """
    Returns the singleton Supabase administrative client using the Service Role Key.
    Raises RuntimeError with clear actionable instructions if credentials are unset.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "SUPABASE CONFIGURATION ERROR: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is not set in backend/.env. "
            "Please configure your Supabase credentials before executing database operations."
        )

    try:
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        return _supabase_client
    except Exception as e:
        raise RuntimeError(
            f"Failed to connect to Supabase at {settings.SUPABASE_URL}: {str(e)}. "
            "Verify your network connection and Supabase project status."
        )
