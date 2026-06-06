import logging
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)

class JobRepository(BaseRepository):
    """Repository handling job posts, matching recommendations, skill gaps, and career feedback."""

    def get_all_jobs(self):
        """Fetch all job openings."""
        try:
            response = self.db.table('jobs').select('*').order('created_at', desc=True).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching jobs: {str(e)}")
            return []

    def get_job_by_id(self, job_id: str):
        """Fetch a specific job by ID."""
        try:
            response = self.db.table('jobs').select('*').eq('id', job_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching job by id {job_id}: {str(e)}")
            return None

    def create_job(self, data: dict):
        """Create a new job posting (admin)."""
        try:
            response = self.db.table('jobs').insert(data).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error creating job: {str(e)}")
            return None

    def delete_job(self, job_id: str):
        """Delete a job posting (admin)."""
        try:
            response = self.db.table('jobs').delete().eq('id', job_id).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error deleting job {job_id}: {str(e)}")
            return None

    def get_recommendations_for_user(self, user_id: str):
        """Fetch ranked recommendations for a specific user, with job details joined."""
        try:
            # Join recommendations with jobs table in Supabase syntax
            response = self.db.table('recommendations').select('*, jobs(*)').eq('user_id', user_id).order('ranking', desc=False).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching recommendations for user {user_id}: {str(e)}")
            return []

    def save_recommendations(self, user_id: str, recommendations: list):
        """Upsert a list of job recommendations for a user."""
        self.db.table('recommendations').delete().eq('user_id', user_id).execute()
        if not recommendations:
            return []
        response = self.db.table('recommendations').insert(recommendations).execute()
        if not response.data:
            raise RuntimeError(f"Recommendations insert returned no data for user {user_id}. Check Supabase RLS on 'recommendations' table.")
        return response.data

    def save_skill_gap(self, user_id: str, job_id: str, missing_skills: list, suggested_courses: list):
        """Upsert skill gap analysis results."""
        try:
            data = {
                'user_id': user_id,
                'job_id': job_id,
                'missing_skills': missing_skills,
                'suggested_courses': suggested_courses
            }
            # Upsert using constraints (unique_user_job_gap)
            response = self.db.table('skill_gaps').upsert(data, on_conflict='user_id,job_id').execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error saving skill gap for user {user_id}, job {job_id}: {str(e)}")
            return None

    def get_skill_gaps_for_user(self, user_id: str):
        """Fetch all skill gaps for a user."""
        try:
            response = self.db.table('skill_gaps').select('*, jobs(*)').eq('user_id', user_id).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching skill gaps for user {user_id}: {str(e)}")
            return []

    def get_skill_gap_for_job(self, user_id: str, job_id: str):
        """Fetch specific skill gap for user and job."""
        try:
            response = self.db.table('skill_gaps').select('*').eq('user_id', user_id).eq('job_id', job_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching skill gap for user {user_id}, job {job_id}: {str(e)}")
            return None

    def save_career_feedback(self, user_id: str, feedback_text: str, career_paths: list, recommended_certifications: list):
        """Save AI Career Advisor feedback."""
        try:
            data = {
                'user_id': user_id,
                'feedback_text': feedback_text,
                'career_paths': career_paths,
                'recommended_certifications': recommended_certifications
            }
            # Remove old feedback if exists, or just insert. Since we store historical/latest feedback:
            self.db.table('career_feedback').delete().eq('user_id', user_id).execute()
            response = self.db.table('career_feedback').insert(data).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error saving career feedback for user {user_id}: {str(e)}")
            return None

    def get_latest_career_feedback(self, user_id: str):
        """Fetch latest career feedback for a user."""
        try:
            response = self.db.table('career_feedback').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(1).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching career feedback for user {user_id}: {str(e)}")
            return None
