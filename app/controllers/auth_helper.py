from functools import wraps
from flask import session, redirect, url_for, flash, abort

def login_required(f):
    """Decorator to protect routes requiring authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to protect routes requiring admin permissions."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login'))
        if session.get('user_role') != 'admin':
            flash("You do not have permission to view that page.", "danger")
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
