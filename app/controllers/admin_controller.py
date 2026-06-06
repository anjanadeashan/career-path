import logging
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.controllers.auth_helper import admin_required
from app.repositories.job_repository import JobRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.resume_repository import ResumeRepository

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__)

job_repo = JobRepository()
profile_repo = ProfileRepository()
resume_repo = ResumeRepository()

@admin_bp.route('/admin', methods=['GET'])
@admin_required
def dashboard():
    """Display the Admin Dashboard with analytics and listings."""
    # 1. Fetch data lists
    profiles = profile_repo.get_all_profiles()
    resumes = resume_repo.get_all_resumes()
    jobs = job_repo.get_all_jobs()
    
    # 2. Compute basic analytical numbers
    total_users = len(profiles)
    total_resumes = len(resumes)
    total_jobs = len(jobs)
    
    # Calculate role breakdown
    student_count = sum(1 for p in profiles if p.get('role') == 'student')
    admin_count = sum(1 for p in profiles if p.get('role') == 'admin')
    
    # Format jobs list requirements for easy displaying
    for job in jobs:
        reqs = job.get('requirements', [])
        if isinstance(reqs, str):
            try:
                job['requirements_list'] = json.loads(reqs)
            except Exception:
                job['requirements_list'] = [reqs]
        else:
            job['requirements_list'] = reqs
            
    return render_template(
        'admin.html',
        profiles=profiles,
        resumes=resumes,
        jobs=jobs,
        total_users=total_users,
        total_resumes=total_resumes,
        total_jobs=total_jobs,
        student_count=student_count,
        admin_count=admin_count
    )

@admin_bp.route('/admin/jobs/new', methods=['POST'])
@admin_required
def create_job():
    """Create a new job posting from the admin form."""
    title = request.form.get('title')
    company = request.form.get('company')
    location = request.form.get('location')
    job_type = request.form.get('job_type', 'Full-time')
    description = request.form.get('description')
    
    # Parse requirements from comma separated list to JSON list
    requirements_raw = request.form.get('requirements', '')
    requirements = [r.strip() for r in requirements_raw.split(',') if r.strip()]
    
    if not title or not company or not description:
        flash("Title, company, and description are required.", "danger")
        return redirect(url_for('admin.dashboard'))
        
    job_data = {
        'title': title,
        'company': company,
        'location': location,
        'job_type': job_type,
        'description': description,
        'requirements': requirements # JSONB array
    }
    
    result = job_repo.create_job(job_data)
    if result:
        flash(f"Job posting '{title}' at {company} created successfully!", "success")
    else:
        flash("Failed to create job posting.", "danger")
        
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/jobs/delete/<job_id>', methods=['POST'])
@admin_required
def delete_job(job_id):
    """Delete a job posting."""
    result = job_repo.delete_job(job_id)
    if result:
        flash("Job posting deleted successfully.", "success")
    else:
        flash("Failed to delete job posting.", "danger")
        
    return redirect(url_for('admin.dashboard'))
