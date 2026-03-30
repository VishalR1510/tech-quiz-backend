from supabase import create_client, Client
from core.config import settings
import logging

logger = logging.getLogger(__name__)

def get_supabase() -> Client | None:
    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        try:
            return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            return None
    logger.warning("Supabase URL or Key not found in environment. Using mock Database/Client if applicable.")
    return None

supabase_client = get_supabase()
