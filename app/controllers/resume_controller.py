import logging
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.controllers.auth_helper import login_required
from app.services.parsing_service import ParsingService
from app.services.nlp_service import NlpService
from app.services.recommendation_service import RecommendationService
from app.services.claude_service import ClaudeService
from app.services.storage_service import StorageService
from app.repositories.resume_repository import ResumeRepository

logger = logging.getLogger(__name__)
resume_bp = Blueprint('resume', __name__)

parsing_service = ParsingService()
_nlp_service = None
rec_service = RecommendationService()

def get_nlp_service():
    global _nlp_service
    if _nlp_service is None:
        _nlp_service = NlpService()
    return _nlp_service
claude_service = ClaudeService()
storage_service = StorageService()
resume_repo = ResumeRepository()

@resume_bp.route('/profile', methods=['GET'])
@login_required
def profile():
    """Display user profile, skills, and uploaded resumes."""
    user_id = session['user_id']
    resume = resume_repo.get_latest_resume(user_id)
    skills = resume_repo.get_skills_by_user(user_id)
    
    # Separate skills for displaying on frontend
    tech_skills = [s for s in skills if s.get('skill_type') == 'technical']
    soft_skills = [s for s in skills if s.get('skill_type') == 'soft']
    
    return render_template(
        'profile.html',
        resume=resume,
        tech_skills=tech_skills,
        soft_skills=soft_skills
    )

@resume_bp.route('/profile/upload', methods=['POST'])
@login_required
def upload_resume():
    """Upload and parse a resume file (PDF or DOCX)."""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    user_id = session['user_id']

    if 'resume' not in request.files:
        if is_ajax:
            return jsonify({"success": False, "error": "No file part provided."}), 400
        flash("No file part provided.", "danger")
        return redirect(url_for('resume.profile'))

    file = request.files['resume']
    if file.filename == '':
        if is_ajax:
            return jsonify({"success": False, "error": "No file selected."}), 400
        flash("No file selected.", "danger")
        return redirect(url_for('resume.profile'))

    try:
        file.seek(0)
        file_bytes = file.read()
        file.seek(0)

        # 1. Upload to Supabase Storage
        file_url = None
        try:
            file_url = storage_service.upload_resume_file(
                user_id=user_id,
                file_name=file.filename,
                file_bytes=file_bytes,
                content_type=file.content_type
            )
        except Exception as storage_err:
            logger.error(f"Failed to upload file to Supabase Storage: {str(storage_err)}")

        # 2. Parse document text
        raw_text = parsing_service.extract_text(file, file.filename)

        # 3. Extract skills and structured sections
        extracted_skills = []
        structured_data = {}

        if claude_service.client:
            try:
                logger.info(f"Using Claude AI parser for resume upload of user {user_id}")
                parsed_data = claude_service.parse_resume(raw_text)
                extracted_skills = parsed_data.get('skills', [])
                structured_data = parsed_data.get('extracted_data', {})
                logger.info(f"Successfully parsed resume using Claude for user {user_id}. Extracted {len(extracted_skills)} skills.")
            except Exception as claude_err:
                logger.error(f"Claude resume parsing failed: {str(claude_err)}. Falling back to local NLP parsing.", exc_info=True)
                extracted_skills = []

        if not extracted_skills:
            logger.info(f"Using local NLP parser for user {user_id}")
            extracted_skills = get_nlp_service().extract_skills(raw_text)
            structured_data = get_nlp_service().extract_structured_data(raw_text)

        # 4. Save to database
        resume_repo.save_resume(user_id, file.filename, raw_text, structured_data, file_url)
        resume_repo.save_skills(user_id, extracted_skills)

        # 5. Trigger recommendations recalculation
        try:
            rec_service.generate_recommendations_for_user(user_id)
            message = "Resume uploaded and parsed successfully! Recommendations updated."
            warning = False
        except Exception as rec_err:
            logger.warning(f"Resume saved but recommendations failed: {str(rec_err)}")
            message = "Resume uploaded and skills extracted! Recommendations could not be generated — check that jobs exist in the system."
            warning = True

        if is_ajax:
            return jsonify({
                "success": True,
                "message": message,
                "warning": warning,
                "skills_count": len(extracted_skills)
            })

        flash(message, "warning" if warning else "success")

    except ValueError as val_err:
        if is_ajax:
            return jsonify({"success": False, "error": str(val_err)}), 422
        flash(str(val_err), "warning")
    except Exception as e:
        logger.error(f"Failed to process resume upload: {str(e)}", exc_info=True)
        if is_ajax:
            return jsonify({"success": False, "error": f"Upload failed: {str(e)}"}), 500
        flash(f"Upload failed: {str(e)}", "danger")

    return redirect(url_for('resume.profile'))

@resume_bp.route('/profile/skills/add', methods=['POST'])
@login_required
def add_skill():
    """Manually add a skill to the user profile."""
    user_id = session['user_id']
    
    if request.is_json:
        data = request.get_json()
        skill_name = data.get('skill_name')
        skill_type = data.get('skill_type', 'technical')
    else:
        skill_name = request.form.get('skill_name')
        skill_type = request.form.get('skill_type', 'technical')
        
    if not skill_name:
        if request.is_json:
            return jsonify({"success": False, "error": "Skill name is required"}), 400
        flash("Skill name cannot be empty.", "warning")
        return redirect(url_for('resume.profile'))
        
    result = resume_repo.add_custom_skill(user_id, skill_name.strip(), skill_type)
    
    # Recalculate recommendations after modifying skills
    rec_service.generate_recommendations_for_user(user_id)
    # Clear the role matches cache to force recalculation on next jobs page load
    resume_repo.clear_role_matches_cache(user_id)
    
    if request.is_json:
        return jsonify({"success": True, "skill": result})
        
    flash(f"Skill '{skill_name}' added successfully.", "success")
    return redirect(url_for('resume.profile'))

@resume_bp.route('/profile/skills/delete', methods=['POST'])
@login_required
def delete_skill():
    """Manually delete a skill from the user profile."""
    user_id = session['user_id']
    
    if request.is_json:
        data = request.get_json()
        skill_name = data.get('skill_name')
    else:
        skill_name = request.form.get('skill_name')
        
    if not skill_name:
        if request.is_json:
            return jsonify({"success": False, "error": "Skill name is required"}), 400
        return redirect(url_for('resume.profile'))
        
    resume_repo.delete_skill(user_id, skill_name)
    
    # Recalculate recommendations after modifying skills
    rec_service.generate_recommendations_for_user(user_id)
    # Clear the role matches cache to force recalculation on next jobs page load
    resume_repo.clear_role_matches_cache(user_id)
    
    if request.is_json:
        return jsonify({"success": True, "message": f"Skill '{skill_name}' deleted."})
        
    flash(f"Skill '{skill_name}' removed.", "success")
    return redirect(url_for('resume.profile'))
