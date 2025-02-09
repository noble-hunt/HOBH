from datetime import datetime, timedelta
from .models import Session, Achievement, EarnedAchievement, AchievementType, DifficultyLevel
from sqlalchemy import func
from contextlib import contextmanager

class AchievementManager:
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

    def check_and_award_achievements(self, workout_log):
        """Check if any achievements should be awarded based on the workout log."""
        with self._session_scope() as session:
            # Check weight milestone achievements
            self._check_weight_milestone(session, workout_log)
            
            # Check consecutive days achievements
            self._check_consecutive_days(session)
            
            # Check movement mastery achievements
            self._check_movement_mastery(session, workout_log)
            
            # Check progression milestones
            self._check_progression_milestone(session, workout_log)

    def _check_weight_milestone(self, session, workout_log):
        """Check and award weight-based achievements."""
        weight_achievements = session.query(Achievement)\
            .filter_by(type=AchievementType.WEIGHT_MILESTONE)\
            .all()

        for achievement in weight_achievements:
            if workout_log.weight >= achievement.criteria_value:
                self._award_achievement(session, achievement, workout_log.movement.name)

    def _check_consecutive_days(self, session):
        """Check and award streak-based achievements."""
        streak_achievements = session.query(Achievement)\
            .filter_by(type=AchievementType.CONSECUTIVE_DAYS)\
            .all()

        # Get workout logs for the past 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        workout_dates = session.query(func.date(WorkoutLog.date))\
            .filter(WorkoutLog.date >= thirty_days_ago)\
            .distinct()\
            .order_by(WorkoutLog.date)\
            .all()

        # Calculate current streak
        current_streak = 0
        today = datetime.now().date()
        
        for i in range(len(workout_dates)):
            if i == 0:
                current_streak = 1
            else:
                prev_date = workout_dates[i-1][0]
                curr_date = workout_dates[i][0]
                if (curr_date - prev_date).days == 1:
                    current_streak += 1
                else:
                    current_streak = 1

        # Check if streak achievements should be awarded
        for achievement in streak_achievements:
            if current_streak >= achievement.criteria_value:
                self._award_achievement(session, achievement)

    def _check_movement_mastery(self, session, workout_log):
        """Check and award difficulty level achievements."""
        if workout_log.difficulty_level == DifficultyLevel.ADVANCED.value:
            mastery_achievement = session.query(Achievement)\
                .filter_by(type=AchievementType.MOVEMENT_MASTERY)\
                .first()
            if mastery_achievement:
                self._award_achievement(session, mastery_achievement, workout_log.movement.name)

    def _check_progression_milestone(self, session, workout_log):
        """Check and award progression-based achievements."""
        if workout_log.difficulty_level == DifficultyLevel.ELITE.value:
            elite_achievement = session.query(Achievement)\
                .filter_by(type=AchievementType.PROGRESSION_MILESTONE)\
                .first()
            if elite_achievement:
                self._award_achievement(session, elite_achievement, workout_log.movement.name)

    def _award_achievement(self, session, achievement, movement_name=None):
        """Award an achievement if it hasn't been earned yet."""
        existing = session.query(EarnedAchievement)\
            .filter_by(
                achievement_id=achievement.id,
                movement_name=movement_name
            ).first()

        if not existing:
            earned = EarnedAchievement(
                achievement_id=achievement.id,
                movement_name=movement_name
            )
            session.add(earned)
            return True
        return False

    def get_earned_achievements(self):
        """Get all earned achievements with their details."""
        with self._session_scope() as session:
            earned = session.query(EarnedAchievement)\
                .join(Achievement)\
                .order_by(EarnedAchievement.date_earned.desc())\
                .all()
            
            return [{
                'name': earned.achievement.name,
                'description': earned.achievement.description,
                'date_earned': earned.date_earned,
                'movement_name': earned.movement_name,
                'icon_name': earned.achievement.icon_name
            } for earned in earned]
