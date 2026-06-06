import logging
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)

class ProfileRepository(BaseRepository):
    """Repository handling profile database operations."""
    
    def get_by_id(self, user_id: str):
        """Fetch profile by user ID."""
        try:
            response = self.db.table('profiles').select('*').eq('id', user_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching profile by id {user_id}: {str(e)}")
            return None

    def update_profile(self, user_id: str, data: dict):
        """Update profile details."""
        try:
            response = self.db.table('profiles').update(data).eq('id', user_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error updating profile {user_id}: {str(e)}")
            return None

    def get_all_profiles(self):
        """Fetch all profiles (admin only)."""
        try:
            response = self.db.table('profiles').select('*').execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching all profiles: {str(e)}")
            return []
            
    def delete_profile(self, user_id: str):
        """Delete user profile."""
        try:
            response = self.db.table('profiles').delete().eq('id', user_id).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error deleting profile {user_id}: {str(e)}")
            return None

    def upsert_profile(self, user_id: str, full_name: str, role: str = 'student', email: str = None):
        """Upsert a user profile."""
        try:
            data = {
                'id': user_id,
                'full_name': full_name,
                'role': role
            }
            if email:
                data['email'] = email
            else:
                existing = self.get_by_id(user_id)
                if existing:
                    data['email'] = existing['email']
                else:
                    data['email'] = f"{user_id}@google-oauth.placeholder"
            
            response = self.db.table('profiles').upsert(data, on_conflict='id').execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error upserting profile {user_id}: {str(e)}")
            return None
