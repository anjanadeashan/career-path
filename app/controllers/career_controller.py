import logging
from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify
from app.controllers.auth_helper import login_required
from app.services.claude_service import ClaudeService
from app.repositories.job_repository import JobRepository
from app.repositories.resume_repository import ResumeRepository

logger = logging.getLogger(__name__)
career_bp = Blueprint('career', __name__)

claude_service = ClaudeService()
job_repo = JobRepository()
resume_repo = ResumeRepository()

@career_bp.route('/advisor', methods=['GET'])
@login_required
def advisor():
    """Display the AI Career Advisor feedback and suggestions page."""
    user_id = session['user_id']
    
    # Check if a resume exists
    resume = resume_repo.get_latest_resume(user_id)
    
    # Fetch latest feedback if already precomputed
    feedback = job_repo.get_latest_career_feedback(user_id)
    
    return render_template(
        'advisor.html',
        feedback=feedback,
        has_resume=(resume is not None)
    )

@career_bp.route('/advisor/generate', methods=['POST'])
@login_required
def generate_advice():
    """Trigger the Claude AI advisor pipeline to analyze CV and update advice."""
    user_id = session['user_id']
    
    result = claude_service.get_career_advice(user_id)
    
    if result.get('success'):
        flash("AI Career Advisor updated feedback successfully!", "success")
        return jsonify(result)
    else:
        error_msg = result.get('error', 'Failed to generate career advice.')
        flash(error_msg, "danger")
        return jsonify({"success": False, "error": error_msg}), 400
