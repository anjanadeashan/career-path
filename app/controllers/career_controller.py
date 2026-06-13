import json
import logging
import re
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


def _parse_advisor_meta(feedback: dict) -> dict:
    """Extract enriched meta fields from the hidden HTML comment embedded in feedback_text."""
    if not feedback:
        return feedback
    raw = feedback.get('feedback_text', '')
    match = re.search(r'<!--advisor_meta:(\{.*?\})-->', raw, re.DOTALL)
    if match:
        try:
            meta = json.loads(match.group(1))
            feedback['profile_score'] = meta.get('profile_score', 0)
            feedback['top_skill_gaps'] = meta.get('top_skill_gaps', [])
            feedback['career_aspiration'] = meta.get('career_aspiration', {})
            feedback['transition_type'] = meta.get('transition_type', '')
            feedback['feedback_text'] = raw[:match.start()].rstrip()
        except (json.JSONDecodeError, KeyError):
            feedback.setdefault('profile_score', 0)
            feedback.setdefault('top_skill_gaps', [])
            feedback.setdefault('career_aspiration', {})
            feedback.setdefault('transition_type', '')
    else:
        feedback.setdefault('profile_score', 0)
        feedback.setdefault('top_skill_gaps', [])
        feedback.setdefault('career_aspiration', {})
        feedback.setdefault('transition_type', '')
    return feedback


@career_bp.route('/advisor', methods=['GET'])
@login_required
def advisor():
    """Display the AI Career Advisor feedback and suggestions page."""
    user_id = session['user_id']

    resume = resume_repo.get_latest_resume(user_id)
    feedback = job_repo.get_latest_career_feedback(user_id)
    feedback = _parse_advisor_meta(feedback)

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
