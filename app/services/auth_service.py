import logging
from app.services.supabase_client import get_supabase_client
from app.repositories.profile_repository import ProfileRepository

logger = logging.getLogger(__name__)

class AuthService:
    """Service handling user authentication and registration via Supabase Auth."""

    def __init__(self):
        self.db = get_supabase_client()
        self.profile_repo = ProfileRepository()

    def register(self, email: str, password: str, full_name: str, role: str = 'student'):
        """
        Register a new user in Supabase.
        The trigger `handle_new_user` in the DB will automatically copy metadata to public.profiles.
        """
        try:
            signup_options = {
                "data": {
                    "full_name": full_name,
                    "role": role
                }
            }
            response = self.db.auth.sign_up({
                "email": email,
                "password": password,
                "options": signup_options
            })
            
            if response.user:
                return {
                    "success": True,
                    "user_id": response.user.id,
                    "email": response.user.email,
                    "message": "Registration successful! 📧 A verification link has been sent to your email address. Please click the link to confirm and activate your account before logging in."
                }
            return {"success": False, "error": "Failed to create user."}
        except Exception as e:
            logger.error(f"Error during registration: {str(e)}")
            return {"success": False, "error": str(e)}

    def login(self, email: str, password: str):
        """Log in a user and retrieve their access token and profile role."""
        try:
            response = self.db.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.session and response.user:
                # Retrieve the full profile from the profiles table to determine the role
                profile = self.profile_repo.get_by_id(response.user.id)
                role = profile.get('role', 'student') if profile else 'student'
                full_name = profile.get('full_name', '') if profile else ''
                
                return {
                    "success": True,
                    "user_id": response.user.id,
                    "email": response.user.email,
                    "full_name": full_name,
                    "role": role,
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token
                }
            return {"success": False, "error": "Invalid email or password."}
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error during login: {error_msg}")
            if "email not confirmed" in error_msg.lower():
                return {"success": False, "error": "Please confirm your email address before signing in. Check your inbox for a confirmation link."}
            return {"success": False, "error": error_msg}

    def login_with_token(self, access_token: str):
        """Log in a user using a Supabase OAuth access token and retrieve their profile."""
        try:
            # Fetch user details from Supabase using the provided access token
            response = self.db.auth.get_user(access_token)
            
            if response and response.user:
                # Retrieve the full profile from the profiles table
                profile = self.profile_repo.get_by_id(response.user.id)
                role = profile.get('role', 'student') if profile else 'student'
                
                # Google auth might store full name in user_metadata
                full_name = profile.get('full_name', '') if profile else response.user.user_metadata.get('full_name', '')
                
                return {
                    "success": True,
                    "user_id": response.user.id,
                    "email": response.user.email,
                    "full_name": full_name,
                    "role": role,
                    "access_token": access_token
                }
            return {"success": False, "error": "Invalid or expired token."}
        except Exception as e:
            logger.error(f"Error during OAuth login: {str(e)}")
            return {"success": False, "error": str(e)}

    def logout(self):
        """Log out the current user session from Supabase."""
        try:
            self.db.auth.sign_out()
            return {"success": True}
        except Exception as e:
            logger.error(f"Error during logout: {str(e)}")
            return {"success": False, "error": str(e)}

    def resend_verification(self, email: str):
        """Resend signup confirmation email."""
        try:
            # Supabase API for resend: type is 'signup'
            self.db.auth.resend({
                "type": "signup",
                "email": email
            })
            return {"success": True}
        except Exception as e:
            logger.error(f"Error resending verification email: {str(e)}")
            return {"success": False, "error": str(e)}
