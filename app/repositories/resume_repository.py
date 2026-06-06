import logging
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)

class ResumeRepository(BaseRepository):
    """Repository handling resume uploads, parsing logs, and extracted skills database operations."""

    def save_resume(self, user_id: str, file_name: str, raw_text: str, extracted_data: dict, file_url: str = None):
        """Save parsed resume text and structured details."""
        self.db.table('resumes').delete().eq('user_id', user_id).execute()
        
        # Safely nest file_url in extracted_data as a fallback
        if file_url:
            if not extracted_data:
                extracted_data = {}
            extracted_data['file_url'] = file_url
            
        data = {
            'user_id': user_id,
            'file_name': file_name,
            'raw_text': raw_text,
            'extracted_data': extracted_data
        }
        
        # Self-healing attempt to save using separate file_url column if it has been added to DB schema
        try:
            data_with_col = data.copy()
            data_with_col['file_url'] = file_url
            response = self.db.table('resumes').insert(data_with_col).execute()
        except Exception as col_err:
            logger.warning(f"Could not save using 'file_url' column: {str(col_err)}. Falling back to writing without it.")
            response = self.db.table('resumes').insert(data).execute()
            
        if not response.data:
            raise RuntimeError(f"Resume insert returned no data for user {user_id}. Check Supabase RLS policies on the 'resumes' table.")
        return response.data[0]

    def get_latest_resume(self, user_id: str):
        """Fetch the latest active resume for a user."""
        try:
            response = self.db.table('resumes').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(1).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching resume for user {user_id}: {str(e)}")
            return None

    def get_all_resumes(self):
        """Fetch all resumes (admin). Join with profile details."""
        try:
            response = self.db.table('resumes').select('*, profiles(*)').execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching all resumes: {str(e)}")
            return []

    def get_skills_by_user(self, user_id: str):
        """Fetch all extracted skills for a user."""
        try:
            response = self.db.table('extracted_skills').select('*').eq('user_id', user_id).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching skills for user {user_id}: {str(e)}")
            return []

    def save_skills(self, user_id: str, skills: list):
        """
        Bulk insert/upsert list of skills.
        skills is a list of dicts: [{'skill_name': 'Python', 'skill_type': 'technical'}, ...]
        """
        self.db.table('extracted_skills').delete().eq('user_id', user_id).execute()
        if not skills:
            return []
        payload = [
            {
                'user_id': user_id,
                'skill_name': skill['skill_name'],
                'skill_type': skill.get('skill_type', 'technical')
            }
            for skill in skills
        ]
        response = self.db.table('extracted_skills').insert(payload).execute()
        if not response.data:
            raise RuntimeError(f"Skills insert returned no data for user {user_id}. Check Supabase RLS policies on the 'extracted_skills' table.")
        return response.data
            
    def add_custom_skill(self, user_id: str, skill_name: str, skill_type: str = 'technical'):
        """Manually add a single custom skill to profile."""
        try:
            data = {
                'user_id': user_id,
                'skill_name': skill_name,
                'skill_type': skill_type
            }
            response = self.db.table('extracted_skills').upsert(data, on_conflict='user_id,skill_name').execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error adding custom skill {skill_name} for user {user_id}: {str(e)}")
            return None

    def delete_skill(self, user_id: str, skill_name: str):
        """Delete a single skill from profile."""
        try:
            response = self.db.table('extracted_skills').delete().eq('user_id', user_id).eq('skill_name', skill_name).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error deleting skill {skill_name} for user {user_id}: {str(e)}")
            return None

    def save_resume_role_matches(self, user_id: str, role_matches: list):
        """Append/Save role matches cache to the user's resume extracted_data field."""
        try:
            resume = self.get_latest_resume(user_id)
            if resume:
                extracted_data = resume.get('extracted_data') or {}
                extracted_data['role_matches'] = role_matches
                # Update in DB
                self.db.table('resumes').update({
                    'extracted_data': extracted_data
                }).eq('id', resume['id']).execute()
                logger.info(f"Saved {len(role_matches)} cached role matches inside resume metadata for user {user_id}.")
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving resume role matches for user {user_id}: {str(e)}")
            return False

    def clear_role_matches_cache(self, user_id: str):
        """Clear the cached job role matches to force recalculation on the next load."""
        try:
            resume = self.get_latest_resume(user_id)
            if resume:
                extracted_data = resume.get('extracted_data') or {}
                if 'role_matches' in extracted_data:
                    del extracted_data['role_matches']
                    # Update in DB
                    self.db.table('resumes').update({
                        'extracted_data': extracted_data
                    }).eq('id', resume['id']).execute()
                    logger.info(f"Cleared cached role matches for user {user_id}.")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error clearing resume role matches cache for user {user_id}: {str(e)}")
            return False
