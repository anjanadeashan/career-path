import logging
from flask import Flask, session, g
from app.config import Config
from app.services.supabase_client import get_supabase_client

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory for the Flask app."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Validate configurations
    Config.validate()

    # Register blueprints (controllers)
    from app.controllers.auth_controller import auth_bp
    from app.controllers.resume_controller import resume_bp
    from app.controllers.job_controller import job_bp
    from app.controllers.career_controller import career_bp
    from app.controllers.admin_controller import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(resume_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(career_bp)
    app.register_blueprint(admin_bp)
    
    # Context processor to inject user session info in all templates
    @app.context_processor
    def inject_user():
        return {
            'session_user_id': session.get('user_id'),
            'session_user_email': session.get('user_email'),
            'session_user_name': session.get('user_name'),
            'session_user_role': session.get('user_role', 'student')
        }

    # Before request hook to populate g.user if logged in
    @app.before_request
    def load_logged_in_user():
        g.user_id = session.get('user_id')
        g.user_role = session.get('user_role', 'student')
        
    @app.route('/')
    def index():
        from flask import render_template
        return render_template('index.html')

    return app
