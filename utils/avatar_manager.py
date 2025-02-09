import py_avataaars as pa
import json
from .models import Session, UserProfile
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError

class AvatarManager:
    def __init__(self):
        self.available_styles = [
            'adventurer', 'adventurer-neutral', 'avataaars',
            'big-ears', 'big-ears-neutral', 'big-smile',
            'bottts', 'croodles', 'croodles-neutral',
            'miniavs', 'personas'
        ]
        
        self.available_features = {
            'skin_color': ['light', 'medium', 'dark'],
            'hair_color': ['black', 'brown', 'blonde', 'red', 'gray'],
            'hair_style': ['short', 'long', 'bun', 'pixie', 'mohawk'],
            'facial_hair': ['none', 'beard', 'mustache'],
            'accessories': ['none', 'glasses', 'sunglasses', 'headband']
        }

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

    def get_available_options(self):
        """Return all available avatar customization options."""
        return {
            'styles': self.available_styles,
            'features': self.available_features
        }

    def update_avatar(self, user_id, style, background_color, features):
        """Update user's avatar settings."""
        try:
            with self._session_scope() as session:
                user = session.query(UserProfile).get(user_id)
                if not user:
                    return False, "User not found"

                user.avatar_style = style
                user.avatar_background = background_color
                user.avatar_features = json.dumps(features)
                
                return True, "Avatar updated successfully"
        except SQLAlchemyError as e:
            return False, f"Database error: {str(e)}"

    def get_avatar_settings(self, user_id):
        """Get current avatar settings for a user."""
        try:
            with self._session_scope() as session:
                user = session.query(UserProfile).get(user_id)
                if not user:
                    return None

                return {
                    'style': user.avatar_style,
                    'background': user.avatar_background,
                    'features': json.loads(user.avatar_features) if user.avatar_features else {}
                }
        except SQLAlchemyError:
            return None

    def generate_avatar_svg(self, settings):
        """Generate avatar SVG based on settings."""
        try:
            avatar = pa.PyAvataaar(
                style=settings['style'],
                background_color=settings['background'],
                **settings['features']
            )
            return avatar.render_svg()
        except Exception as e:
            print(f"Error generating avatar: {e}")
            return None
