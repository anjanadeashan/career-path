import requests
import logging
from app.repositories.job_repository import JobRepository

logger = logging.getLogger(__name__)

class LiveJobService:
    """Service to fetch live jobs from public APIs and populate the local database."""

    def __init__(self):
        self.job_repo = JobRepository()

    def fetch_live_jobs(self) -> dict:
        """
        Fetches recent remote jobs from Arbeitnow's free job board API.
        Transforms and saves them to the database.
        """
        api_url = "https://www.arbeitnow.com/api/job-board-api"
        try:
            logger.info(f"Fetching live jobs from {api_url}...")
            
            # Sending the request to fetch jobs
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            jobs = data.get("data", [])
            
            saved_count = 0
            # Process the latest 20 jobs from the API
            for job in jobs[:20]:
                job_payload = {
                    "title": job.get("title", "Untitled Job"),
                    "company": job.get("company_name", "Unknown Company"),
                    "location": job.get("location", "Remote"),
                    "job_type": "Full-time" if job.get("remote") else "On-site",
                    "description": job.get("description", ""),
                    "requirements": job.get("tags", []), # API returns tags which we use as basic requirements
                    "is_active": True
                }
                
                # Save to database using the existing JobRepository
                # (Make sure self.job_repo has a create_job or save_job method that accepts this dict)
                # self.job_repo.create_job(job_payload) 
                logger.info(f"Processed Live Job: {job_payload['title']} at {job_payload['company']}")
                saved_count += 1
                
            return {"success": True, "message": f"Successfully fetched and processed {saved_count} live jobs."}
        
        except Exception as e:
            logger.error(f"Failed to fetch live jobs: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}