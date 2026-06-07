import logging
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from app.config import Config

logger = logging.getLogger(__name__)

supabase_client: Client = None


class FlaskSessionStorage:
    """
    PKCE verifier storage backed by Flask session (cookie).
    Survives across serverless requests — fixes PKCE code exchange on Vercel.
    """
    def get_item(self, key: str):
        from flask import session
        return session.get(f'_sb_{key}')

    def set_item(self, key: str, value: str) -> None:
        from flask import session
        session[f'_sb_{key}'] = value

    def remove_item(self, key: str) -> None:
        from flask import session
        session.pop(f'_sb_{key}', None)


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
    Returns a per-request Supabase auth client whose PKCE verifier is stored
    in Flask session so it survives across serverless function invocations.
    """
    url = Config.SUPABASE_URL
    key = Config.SUPABASE_KEY

    if not url or not key:
        logger.error("Supabase URL or anon Key is missing from Config!")
        raise ValueError("Supabase URL and anon Key are required for auth operations.")

    try:
        client = create_client(url, key, options=ClientOptions(storage=FlaskSessionStorage()))
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase auth client: {str(e)}")
        raise e
