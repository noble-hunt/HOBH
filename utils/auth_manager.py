from sqlalchemy.exc import SQLAlchemyError
from .models import Session, UserProfile
from contextlib import contextmanager
import hashlib
import os

class AuthManager:
    def __init__(self):
        pass

    @contextmanager
    def _session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _hash_password(self, password, salt=None):
        """Hash password with salt."""
        if not salt:
            salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        return salt + key

    def _verify_password(self, stored_password, provided_password):
        """Verify a stored password against one provided by user."""
        salt = stored_password[:32]
        stored_key = stored_password[32:]
        new_key = hashlib.pbkdf2_hmac(
            'sha256',
            provided_password.encode('utf-8'),
            salt,
            100000
        )
        return stored_key == new_key

    def create_user(self, username, password, display_name=None):
        """Create a new user."""
        try:
            with self._session_scope() as session:
                # Check if username already exists
                existing_user = session.query(UserProfile).filter_by(username=username).first()
                if existing_user:
                    return None, "Username already exists"

                hashed_password = self._hash_password(password)
                user = UserProfile(
                    username=username,
                    password=hashed_password,
                    display_name=display_name or username
                )
                session.add(user)
                session.commit()
                return user.id, None
        except SQLAlchemyError as e:
            return None, f"Database error: {str(e)}"

    def authenticate_user(self, username, password):
        """Authenticate a user."""
        try:
            with self._session_scope() as session:
                user = session.query(UserProfile).filter_by(username=username).first()
                if not user:
                    return None, "Invalid username or password"

                if not self._verify_password(user.password, password):
                    return None, "Invalid username or password"

                return user.id, None
        except SQLAlchemyError as e:
            return None, f"Database error: {str(e)}"

    def get_user(self, user_id):
        """Get user by ID."""
        try:
            with self._session_scope() as session:
                user = session.query(UserProfile).get(user_id)
                if user:
                    return {
                        'id': user.id,
                        'username': user.username,
                        'display_name': user.display_name
                    }
                return None
        except SQLAlchemyError:
            return None
