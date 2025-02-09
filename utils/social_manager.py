from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from .models import Session, UserProfile, WorkoutLog, SharedWorkout
from contextlib import contextmanager

class SocialManager:
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

    def create_profile(self, username, display_name=None, bio=None):
        """Create a new user profile."""
        try:
            with self._session_scope() as session:
                profile = UserProfile(
                    username=username,
                    display_name=display_name or username,
                    bio=bio
                )
                session.add(profile)
                return profile.id
        except SQLAlchemyError as e:
            raise Exception(f"Error creating profile: {str(e)}")

    def follow_user(self, follower_id, followed_id):
        """Follow another user."""
        try:
            with self._session_scope() as session:
                follower = session.query(UserProfile).get(follower_id)
                followed = session.query(UserProfile).get(followed_id)
                
                if not follower or not followed:
                    raise ValueError("User not found")
                
                if followed not in follower.following:
                    follower.following.append(followed)
                return True
        except SQLAlchemyError as e:
            raise Exception(f"Error following user: {str(e)}")

    def unfollow_user(self, follower_id, followed_id):
        """Unfollow a user."""
        try:
            with self._session_scope() as session:
                follower = session.query(UserProfile).get(follower_id)
                followed = session.query(UserProfile).get(followed_id)
                
                if not follower or not followed:
                    raise ValueError("User not found")
                
                if followed in follower.following:
                    follower.following.remove(followed)
                return True
        except SQLAlchemyError as e:
            raise Exception(f"Error unfollowing user: {str(e)}")

    def share_workout(self, user_id, workout_log_id, caption=None):
        """Share a workout."""
        try:
            with self._session_scope() as session:
                shared = SharedWorkout(
                    user_id=user_id,
                    workout_log_id=workout_log_id,
                    caption=caption
                )
                session.add(shared)
                return shared.id
        except SQLAlchemyError as e:
            raise Exception(f"Error sharing workout: {str(e)}")

    def get_user_feed(self, user_id, limit=10):
        """Get shared workouts from followed users."""
        try:
            with self._session_scope() as session:
                user = session.query(UserProfile).get(user_id)
                if not user:
                    raise ValueError("User not found")
                
                following_ids = [u.id for u in user.following]
                
                feed = session.query(SharedWorkout)\
                    .filter(SharedWorkout.user_id.in_(following_ids))\
                    .order_by(SharedWorkout.shared_at.desc())\
                    .limit(limit)\
                    .all()
                
                return feed
        except SQLAlchemyError as e:
            raise Exception(f"Error getting user feed: {str(e)}")

    def like_workout(self, shared_workout_id):
        """Like a shared workout."""
        try:
            with self._session_scope() as session:
                shared = session.query(SharedWorkout).get(shared_workout_id)
                if not shared:
                    raise ValueError("Shared workout not found")
                
                shared.likes += 1
                return True
        except SQLAlchemyError as e:
            raise Exception(f"Error liking workout: {str(e)}")

    def get_user_profile(self, user_id):
        """Get user profile with basic stats."""
        try:
            with self._session_scope() as session:
                profile = session.query(UserProfile).get(user_id)
                if not profile:
                    raise ValueError("User not found")
                
                followers_count = len(profile.followers)
                following_count = len(profile.following)
                shared_workouts_count = len(profile.shared_workouts)
                
                return {
                    "username": profile.username,
                    "display_name": profile.display_name,
                    "bio": profile.bio,
                    "followers_count": followers_count,
                    "following_count": following_count,
                    "shared_workouts_count": shared_workouts_count
                }
        except SQLAlchemyError as e:
            raise Exception(f"Error getting user profile: {str(e)}")
