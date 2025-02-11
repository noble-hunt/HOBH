import json
from .models import Session, UserProfile
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
import traceback

try:
    import py_avataaars as pa
    AVATAAARS_AVAILABLE = True
except ImportError:
    print("Warning: py-avataaars not available")
    AVATAAARS_AVAILABLE = False

class AvatarManager:
    def __init__(self, session):
        """Initialize AvatarManager with database session."""
        self.session = session
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

    def get_avatar_image(self, user_id):
        """Get the avatar image for a user."""
        try:
            # Get current avatar settings
            settings = self.get_avatar_settings(user_id)
            if not settings:
                return None

            # Generate SVG using settings
            svg_data = self.generate_avatar_svg(settings)
            return svg_data

        except Exception as e:
            print(f"Error generating avatar image: {str(e)}")
            print(traceback.format_exc())
            return None

    def get_available_options(self):
        """Return all available avatar customization options."""
        return {
            'styles': self.available_styles,
            'features': self.available_features
        }

    def update_avatar(self, user_id, style, background_color, features):
        """Update user's avatar settings."""
        try:
            user = self.session.query(UserProfile).get(user_id)
            if not user:
                return False, "User not found"

            user.avatar_style = style
            user.avatar_background = background_color
            user.avatar_features = json.dumps(features)
            self.session.commit()

            return True, "Avatar updated successfully"
        except SQLAlchemyError as e:
            return False, f"Database error: {str(e)}"

    def get_avatar_settings(self, user_id):
        """Get current avatar settings for a user."""
        try:
            user = self.session.query(UserProfile).get(user_id)
            if not user:
                return None

            return {
                'style': user.avatar_style,
                'background': user.avatar_background,
                'features': json.loads(user.avatar_features) if user.avatar_features else {}
            }
        except SQLAlchemyError as e:
            print(f"Error getting avatar settings: {str(e)}")
            return None

    def generate_avatar_svg(self, settings):
        """Generate avatar SVG based on settings."""
        if not AVATAAARS_AVAILABLE:
            return None

        try:
            # Create a basic avatar with default features
            avatar = pa.PyAvataaar(
                style=pa.AvatarStyle.TRANSPARENT,
                background_color=settings.get('background', '#F0F2F6')
            )

            # Set features if available
            features = settings.get('features', {})

            # Set skin color
            if 'skin_color' in features:
                try:
                    skin_color = features['skin_color'].upper()
                    avatar.skin_color = getattr(pa.SkinColor, skin_color)
                except (AttributeError, ValueError):
                    pass

            # Set hair color
            if 'hair_color' in features:
                try:
                    hair_color = features['hair_color'].upper()
                    avatar.hair_color = getattr(pa.HairColor, hair_color)
                except (AttributeError, ValueError):
                    pass

            # Set hair style
            if 'hair_style' in features:
                try:
                    hair_style = features['hair_style'].upper()
                    avatar.hair_type = getattr(pa.HairType, hair_style)
                except (AttributeError, ValueError):
                    pass

            # Set facial hair
            if 'facial_hair' in features and features['facial_hair'] != 'none':
                try:
                    facial_hair = features['facial_hair'].upper()
                    avatar.facial_hair_type = getattr(pa.FacialHairType, facial_hair)
                except (AttributeError, ValueError):
                    pass

            # Set accessories
            if 'accessories' in features and features['accessories'] != 'none':
                try:
                    accessories = features['accessories'].upper()
                    avatar.accessories_type = getattr(pa.AccessoriesType, accessories)
                except (AttributeError, ValueError):
                    pass

            return avatar.render_svg()
        except Exception as e:
            print(f"Error generating avatar: {e}")
            print(traceback.format_exc())
            return None