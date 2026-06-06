from app.services.supabase_client import get_supabase_client
from supabase import Client

class BaseRepository:
    """Base repository class providing access to the Supabase client."""
    def __init__(self):
        self.db: Client = get_supabase_client()
