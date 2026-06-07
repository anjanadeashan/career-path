import logging
from supabase import create_client, Client
from app.config import Config

logger = logging.getLogger(__name__)

supabase_client: Client = None
supabase_auth_client: Client = None

def get_supabase_client() -> Client:
    """
    Initializes and returns the Supabase client.
    Uses the service role key when available so server-side operations
    bypass Row Level Security (RLS) policies.
    """
    global supabase_client
    if supabase_client is not None:
        return supabase_client

    url = Config.SUPABASE_URL
    # Prefer service role key (bypasses RLS for trusted server-side code),
    # fall back to anon key if not configured.
    key = Config.SUPABASE_SERVICE_KEY or Config.SUPABASE_KEY

    if not url or not key:
        logger.error("Supabase URL or Key is missing from Config!")
        raise ValueError("Supabase URL and Key are required. Check your configuration.")

    try:
        supabase_client = create_client(url, key)
        if Config.SUPABASE_SERVICE_KEY:
            logger.info("Supabase client initialized with service role key (RLS bypassed).")
        else:
            logger.warning("Supabase client initialized with anon key. RLS policies may block DB writes.")
        return supabase_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
        raise e

def get_supabase_auth_client() -> Client:
    """
    Initializes and returns a Supabase client using the anon key.
    OAuth flows (sign_in_with_oauth, exchange_code_for_session) must use
    the anon key — the service role key bypasses user session creation.
    """
    global supabase_auth_client
    if supabase_auth_client is not None:
        return supabase_auth_client

    url = Config.SUPABASE_URL
    key = Config.SUPABASE_KEY  # Always use anon key for auth operations

    if not url or not key:
        logger.error("Supabase URL or anon Key is missing from Config!")
        raise ValueError("Supabase URL and anon Key are required for auth operations.")

    try:
        supabase_auth_client = create_client(url, key)
        logger.info("Supabase auth client initialized with anon key.")
        return supabase_auth_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase auth client: {str(e)}")
        raise e
