import logging
import os
import traceback
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.services.auth_service import AuthService
from app.services.supabase_client import get_supabase_auth_client

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    # If already logged in, redirect to profile
    if session.get('user_id'):
        return redirect(url_for('resume.profile'))
        
    if request.method == 'POST':
        # Check if JSON request or Form request
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
        else:
            email = request.form.get('email')
            password = request.form.get('password')
            
        if not email or not password:
            error_msg = "Email and password are required."
            if request.is_json:
                return jsonify({"success": False, "error": error_msg}), 400
            flash(error_msg, 'danger')
            return render_template('login.html')
            
        result = auth_service.login(email, password)
        
        if result.get('success'):
            # Clear pending verification flag on successful login
            session.pop('awaiting_verification', None)
            # Save token & user details in session
            session['user_id'] = result['user_id']
            session['user_email'] = result['email']
            session['user_name'] = result['full_name']
            session['user_role'] = result['role']
            session.permanent = True
            
            if request.is_json:
                return jsonify({
                    "success": True, 
                    "message": "Login successful", 
                    "role": result['role'],
                    "redirect": url_for('admin.dashboard') if result['role'] == 'admin' else url_for('resume.profile')
                })
                
            flash(f"Welcome back, {result['full_name']}!", 'success')
            if result['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('resume.profile'))
        else:
            error_msg = result.get('error', 'Invalid email or password.')
            if request.is_json:
                return jsonify({"success": False, "error": error_msg}), 401
            flash(error_msg, 'danger')
            
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if session.get('user_id'):
        return redirect(url_for('resume.profile'))
        
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            full_name = data.get('full_name')
            role = data.get('role', 'student')
        else:
            email = request.form.get('email')
            password = request.form.get('password')
            full_name = request.form.get('full_name')
            role = request.form.get('role', 'student')
            
        if not email or not password or not full_name:
            error_msg = "All fields are required."
            if request.is_json:
                return jsonify({"success": False, "error": error_msg}), 400
            flash(error_msg, 'danger')
            return render_template('register.html')
            
        result = auth_service.register(email, password, full_name, role)
        
        if result.get('success'):
            session['awaiting_verification'] = email
            if request.is_json:
                return jsonify({"success": True, "message": result['message'], "redirect": url_for('auth.login')})
            flash(result['message'], 'success')
            return redirect(url_for('auth.login'))
        else:
            error_msg = result.get('error', 'Registration failed.')
            if request.is_json:
                return jsonify({"success": False, "error": error_msg}), 400
            flash(error_msg, 'danger')
            
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    """Handle user logout."""
    auth_service.logout()
    session.clear()
    flash("You have been successfully logged out.", "success")
    return redirect(url_for('auth.login'))

@auth_bp.route('/clear-verification', methods=['POST'])
def clear_verification():
    """Manually clear the pending verification session banner."""
    session.pop('awaiting_verification', None)
    return redirect(url_for('auth.login'))

@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend the Supabase signup confirmation email to the user."""
    email = session.get('awaiting_verification')
    if email:
        result = auth_service.resend_verification(email)
        if result.get('success'):
            flash("Verification email resent successfully! Please check your inbox.", "success")
        else:
            flash(result.get('error', "Failed to resend verification email. Please try again later."), "danger")
    return redirect(url_for('auth.login'))

_OUR_PKCE_KEY = '_oauth_pkce_verifier'


def _find_pkce_verifier_in_session():
    """Find the PKCE code verifier stored by gotrue regardless of key naming convention."""
    # Try our explicit key first
    verifier = session.get(_OUR_PKCE_KEY)
    if verifier:
        return verifier
    # Fall back: gotrue stores it under a key containing 'code-verifier'
    for key in list(session.keys()):
        if 'code-verifier' in key:
            return session.get(key)
    return None


def _clear_pkce_state():
    """Remove all PKCE-related keys from the Flask session."""
    session.pop(_OUR_PKCE_KEY, None)
    for key in [k for k in list(session.keys()) if 'code-verifier' in k]:
        session.pop(key, None)


# 1. Route to redirect the user to Google Login Page
@auth_bp.route('/login/google')
def login_google():
    """Redirect user to Google login interface via Supabase OAuth."""
    try:
        # Clear stale PKCE state from any previous failed attempt
        _clear_pkce_state()

        app_url = os.environ.get('APP_URL', '').rstrip('/')
        if app_url:
            callback_url = f"{app_url}/auth/callback"
        else:
            callback_url = url_for('auth.google_callback', _external=True)

        logger.info(f"Starting Google OAuth. callback_url={callback_url}")
        auth_client = get_supabase_auth_client()

        response = auth_client.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": callback_url
            }
        })

        if response.url:
            # Gotrue stored the PKCE verifier via FlaskSessionStorage — copy it to our
            # own key so google_callback can pass it explicitly to exchange_code_for_session.
            code_verifier = _find_pkce_verifier_in_session()
            if code_verifier:
                session[_OUR_PKCE_KEY] = code_verifier
                logger.info("PKCE code verifier captured in session.")
            else:
                logger.warning(
                    f"PKCE code verifier not found. Session keys: {list(session.keys())}"
                )
            return redirect(response.url)

        flash("Failed to generate Google Login URL.", "danger")
        return redirect(url_for('auth.login'))

    except Exception as e:
        logger.error(f"Error initiating Google OAuth: {str(e)}\n{traceback.format_exc()}")
        flash(f"OAuth initiation failed: {str(e)}", "danger")
        return redirect(url_for('auth.login'))

# 2. Callback route to handle Google's redirect containing authorization tokens
@auth_bp.route('/auth/callback')
def google_callback():
    """Handle the OAuth callback redirect from Supabase and sign the user in."""
    # Check for OAuth error response from Supabase/Google
    error = request.args.get('error')
    error_description = request.args.get('error_description', '')
    if error:
        logger.error(f"OAuth callback received error: {error} — {error_description}")
        flash(f"Google login failed: {error_description or error}", "danger")
        return redirect(url_for('auth.login'))

    code = request.args.get('code')
    logger.info(f"OAuth callback hit. code present: {bool(code)}")

    if not code:
        logger.warning("OAuth callback called with no code and no error parameter.")
        flash("Google login failed: no authorization code received.", "danger")
        return redirect(url_for('auth.login'))

    try:
        auth_client = get_supabase_auth_client()
        # Read and consume the PKCE verifier saved during login_google
        code_verifier = _find_pkce_verifier_in_session()
        _clear_pkce_state()
        logger.info(f"Exchanging code. code_verifier present: {bool(code_verifier)}")

        exchange_params = {"auth_code": code}
        if code_verifier:
            exchange_params["code_verifier"] = code_verifier

        # Exchange the authorization code for a session
        response = auth_client.auth.exchange_code_for_session(exchange_params)

        if not response.session or not response.user:
            logger.error(f"exchange_code_for_session returned empty session/user. response={response}")
            flash("Google login failed: could not establish a session. Please try again.", "danger")
            return redirect(url_for('auth.login'))

        # Retrieve role and set flask session
        profile = auth_service.profile_repo.get_by_id(response.user.id)

        # Self-healing: if profile record doesn't exist, create it dynamically
        if not profile:
            auth_service.profile_repo.upsert_profile(
                user_id=response.user.id,
                email=response.user.email,
                full_name=response.user.user_metadata.get('full_name', 'Google User') if response.user.user_metadata else 'Google User',
                role='student'
            )
            role = 'student'
            full_name = response.user.user_metadata.get('full_name', 'Google User') if response.user.user_metadata else 'Google User'
        else:
            role = profile.get('role', 'student')
            full_name = profile.get('full_name', 'Google User')

        # Populate Flask Session
        session.pop('awaiting_verification', None)
        session['user_id'] = response.user.id
        session['user_email'] = response.user.email
        session['user_name'] = full_name
        session['user_role'] = role
        session.permanent = True

        logger.info(f"Google OAuth login successful for user {response.user.id}")
        flash(f"Successfully logged in with Google! Welcome, {full_name}!", "success")
        return redirect(url_for('resume.profile'))

    except Exception as e:
        logger.error(f"OAuth code exchange failed: {str(e)}\n{traceback.format_exc()}")
        flash("Google login failed: could not complete authentication. Please try again.", "danger")
        return redirect(url_for('auth.login'))
