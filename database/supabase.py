from supabase import create_client, Client
from core.config import settings
import logging

logger = logging.getLogger(__name__)

def get_supabase() -> Client | None:
    """Get Supabase client with anon key (for queries without RLS bypass)"""
    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        try:
            return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            return None
    logger.warning("Supabase URL or Key not found in environment.")
    return None

def get_supabase_admin() -> Client | None:
    """Get Supabase client with service role key (for bypass RLS - use for inserts/updates)"""
    if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
        try:
            return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize Supabase admin client: {e}")
            return None
    logger.warning("Supabase URL or Service Role Key not found in environment.")
    return None

supabase_client = get_supabase()
