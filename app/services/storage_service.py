import logging
import uuid
import mimetypes
from app.services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

class StorageService:
    """Service to interact with Supabase Storage for uploading and retrieving files."""

    def __init__(self):
        self.db_client = get_supabase_client()
        self.bucket_name = "resumes"
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Programmatically create a public bucket if it doesn't exist."""
        try:
            # Check if bucket exists by listing all buckets
            buckets = self.db_client.storage.list_buckets()
            bucket_names = [b.name for b in buckets] if buckets else []
            
            if self.bucket_name not in bucket_names:
                logger.info(f"Supabase Storage bucket '{self.bucket_name}' not found. Creating bucket...")
                # Create public bucket
                self.db_client.storage.create_bucket(self.bucket_name, options={"public": True})
                logger.info(f"Supabase Storage bucket '{self.bucket_name}' created successfully.")
        except Exception as e:
            logger.warning(f"Failed to check/create bucket '{self.bucket_name}': {str(e)}. "
                           f"Make sure you have created it in the Supabase Dashboard if uploads fail.")

    def upload_resume_file(self, user_id: str, file_name: str, file_bytes: bytes, content_type: str = None) -> str:
        """
        Uploads a resume file to Supabase Storage bucket.
        Returns the public URL of the uploaded file.
        """
        # Determine content type if not provided
        if not content_type:
            content_type, _ = mimetypes.guess_type(file_name)
            if not content_type:
                content_type = "application/octet-stream"

        # Unique file path inside bucket: user_id/uuid_filename
        clean_file_name = file_name.replace(" ", "_")
        unique_id = uuid.uuid4().hex[:8]
        file_path = f"{user_id}/{unique_id}_{clean_file_name}"

        try:
            logger.info(f"Uploading file '{file_name}' to Supabase Storage path '{file_path}'...")
            
            # Delete existing files in user's directory to save space (since only latest resume is active)
            try:
                files_in_user_dir = self.db_client.storage.from_(self.bucket_name).list(user_id)
                if files_in_user_dir:
                    files_to_remove = [f"{user_id}/{f['name']}" if isinstance(f, dict) else f"{user_id}/{f.name}" for f in files_in_user_dir]
                    self.db_client.storage.from_(self.bucket_name).remove(files_to_remove)
                    logger.info(f"Cleaned up {len(files_to_remove)} old resume files for user {user_id}.")
            except Exception as clean_err:
                logger.warning(f"Could not clean up old resume files for user {user_id}: {str(clean_err)}")

            # Upload the file
            self.db_client.storage.from_(self.bucket_name).upload(
                path=file_path,
                file=file_bytes,
                file_options={"content-type": content_type}
            )
            
            # Get public URL
            public_url = self.db_client.storage.from_(self.bucket_name).get_public_url(file_path)
            logger.info(f"Successfully uploaded resume file. Public URL: {public_url}")
            return public_url
            
        except Exception as e:
            logger.error(f"Error uploading file to Supabase Storage: {str(e)}", exc_info=True)
            raise e
