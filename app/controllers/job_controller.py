import logging
from flask import Blueprint, render_template, session
from app.controllers.auth_helper import login_required
from app.repositories.resume_repository import ResumeRepository
from app.services.job_role_service import calculate_role_matches, CATEGORIES

logger = logging.getLogger(__name__)
job_bp = Blueprint('job', __name__)
resume_repo = ResumeRepository()

@job_bp.route('/jobs', methods=['GET'])
@login_required
def jobs():
    """Display standard job role matches based on the user's skill profile."""
    user_id = session['user_id']

    resume = resume_repo.get_latest_resume(user_id)
    user_skills = resume_repo.get_skills_by_user(user_id)

    role_matches = calculate_role_matches(user_skills, user_id=user_id) if user_skills else []

    return render_template(
        'jobs.html',
        role_matches=role_matches,
        categories=CATEGORIES,
        has_resume=(resume is not None),
        has_skills=bool(user_skills)
    )
