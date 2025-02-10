"""Gamification system for workout progress tracking."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from utils.models import (
    WorkoutLog,
    Movement,
    UserProfile,
    Achievement,
    EarnedAchievement
)

@dataclass
class LevelInfo:
    """Level information and requirements."""
    level: int
    title: str
    xp_required: int
    rewards: List[str]

@dataclass
class ProgressUpdate:
    """Progress update information."""
    xp_gained: int
    new_level: Optional[LevelInfo] = None
    achievements_earned: List[str] = None
    total_xp: int = 0

class GamificationManager:
    """Manages gamification features and progress tracking."""

    def __init__(self, session: Session):
        self.session = session
        self.levels = self._initialize_levels()
        self.xp_multipliers = {
            'BEGINNER': 1.0,
            'INTERMEDIATE': 1.5,
            'ADVANCED': 2.0,
            'ELITE': 3.0
        }

    def _initialize_levels(self) -> Dict[int, LevelInfo]:
        """Initialize level requirements and rewards."""
        levels = {}
        base_xp = 1000
        titles = [
            "Novice Lifter", "Amateur Athlete", "Dedicated Trainee",
            "Elite Performer", "Master of Iron", "Olympic Prospect"
        ]
        
        for level in range(1, 31):
            # XP required increases exponentially
            xp_required = int(base_xp * (1.5 ** (level - 1)))
            title_index = min(len(titles) - 1, (level - 1) // 5)
            
            # Define rewards for each level
            rewards = [
                f"'{titles[title_index]}' Title Unlocked",
                f"Level {level} Badge",
                "Custom Avatar Frame" if level % 5 == 0 else None,
                "Special Effect Animation" if level % 10 == 0 else None
            ]
            rewards = [r for r in rewards if r]
            
            levels[level] = LevelInfo(
                level=level,
                title=f"{titles[title_index]} {level}",
                xp_required=xp_required,
                rewards=rewards
            )
        
        return levels

    def calculate_workout_xp(self, workout: WorkoutLog) -> int:
        """Calculate XP for a completed workout."""
        base_xp = 100  # Base XP for any workout
        
        # Apply difficulty multiplier
        difficulty_multiplier = self.xp_multipliers.get(
            workout.difficulty,
            1.0
        )
        
        # Calculate volume-based bonus
        volume = workout.weight * workout.reps
        volume_bonus = min(100, volume / 10)  # Cap volume bonus at 100 XP
        
        # Success bonus
        success_bonus = 50 if workout.completed else 0
        
        total_xp = int((base_xp + volume_bonus) * difficulty_multiplier + success_bonus)
        return total_xp

    def get_current_level(self, total_xp: int) -> LevelInfo:
        """Get current level based on total XP."""
        current_level = 1
        for level, info in self.levels.items():
            if total_xp >= info.xp_required:
                current_level = level
            else:
                break
        return self.levels[current_level]

    def process_workout(self, workout: WorkoutLog) -> ProgressUpdate:
        """Process a completed workout and return progress updates."""
        # Get user profile
        user_profile = self.session.query(UserProfile)\
            .filter_by(id=workout.user_id)\
            .first()
        
        if not user_profile:
            raise ValueError("User profile not found")
            
        # Calculate XP gained
        xp_gained = self.calculate_workout_xp(workout)
        
        # Update total XP
        old_total_xp = user_profile.total_xp or 0
        new_total_xp = old_total_xp + xp_gained
        user_profile.total_xp = new_total_xp
        
        # Check for level up
        old_level = self.get_current_level(old_total_xp)
        new_level = self.get_current_level(new_total_xp)
        
        # Check for achievements
        achievements_earned = self._check_achievements(workout)
        
        # Save changes
        self.session.commit()
        
        return ProgressUpdate(
            xp_gained=xp_gained,
            new_level=new_level if new_level.level > old_level.level else None,
            achievements_earned=achievements_earned,
            total_xp=new_total_xp
        )

    def _check_achievements(self, workout: WorkoutLog) -> List[str]:
        """Check and award achievements for a workout."""
        earned_achievements = []
        
        # Check weight-based achievements
        if workout.weight >= 100:
            self._award_achievement(
                workout.user_id,
                "weight_master",
                "Weight Master",
                "Lift 100kg or more in any movement",
                workout.movement.name if workout.movement else None
            )
            earned_achievements.append("Weight Master")
            
        # Check consistency achievements
        recent_workouts = self.session.query(WorkoutLog)\
            .filter(
                WorkoutLog.user_id == workout.user_id,
                WorkoutLog.date >= datetime.now() - timedelta(days=7)
            )\
            .distinct(func.date(WorkoutLog.date))\
            .count()
            
        if recent_workouts >= 7:
            self._award_achievement(
                workout.user_id,
                "consistency_king",
                "Consistency King",
                "Log workouts for 7 consecutive days"
            )
            earned_achievements.append("Consistency King")
            
        # Check difficulty-based achievements
        if workout.difficulty == "ADVANCED":
            self._award_achievement(
                workout.user_id,
                "movement_expert",
                "Movement Expert",
                f"Reach ADVANCED level in {workout.movement.name if workout.movement else 'a movement'}",
                workout.movement.name if workout.movement else None
            )
            earned_achievements.append("Movement Expert")
            
        if workout.difficulty == "ELITE":
            self._award_achievement(
                workout.user_id,
                "elite_status",
                "Elite Status",
                f"Reach ELITE level in {workout.movement.name if workout.movement else 'a movement'}",
                workout.movement.name if workout.movement else None
            )
            earned_achievements.append("Elite Status")
            
        return earned_achievements

    def _award_achievement(
        self,
        user_id: int,
        achievement_id: str,
        name: str,
        description: str,
        movement_name: Optional[str] = None
    ) -> None:
        """Award an achievement to a user if not already earned."""
        # Check if achievement already exists
        achievement = self.session.query(Achievement)\
            .filter_by(achievement_id=achievement_id)\
            .first()
            
        if not achievement:
            # Create achievement if it doesn't exist
            achievement = Achievement(
                achievement_id=achievement_id,
                name=name,
                description=description
            )
            self.session.add(achievement)
            self.session.flush()
            
        # Check if user already earned this achievement
        earned = self.session.query(EarnedAchievement)\
            .filter_by(
                user_id=user_id,
                achievement_id=achievement.id
            )\
            .first()
            
        if not earned:
            # Award achievement
            earned_achievement = EarnedAchievement(
                user_id=user_id,
                achievement_id=achievement.id,
                date_earned=datetime.now(),
                movement_name=movement_name
            )
            self.session.add(earned_achievement)

    def get_user_progress(self, user_id: int) -> Dict:
        """Get user's progress information."""
        user_profile = self.session.query(UserProfile)\
            .filter_by(id=user_id)\
            .first()
            
        if not user_profile:
            raise ValueError("User profile not found")
            
        total_xp = user_profile.total_xp or 0
        current_level = self.get_current_level(total_xp)
        next_level = self.levels.get(current_level.level + 1)
        
        # Calculate progress to next level
        progress = 0
        if next_level:
            xp_for_current = current_level.xp_required
            xp_for_next = next_level.xp_required
            xp_progress = total_xp - xp_for_current
            xp_needed = xp_for_next - xp_for_current
            progress = min(100, int((xp_progress / xp_needed) * 100))
            
        return {
            'total_xp': total_xp,
            'current_level': current_level,
            'next_level': next_level,
            'progress_to_next': progress,
            'recent_achievements': self._get_recent_achievements(user_id)
        }

    def _get_recent_achievements(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Get user's recently earned achievements."""
        recent = self.session.query(EarnedAchievement)\
            .join(Achievement)\
            .filter(EarnedAchievement.user_id == user_id)\
            .order_by(EarnedAchievement.date_earned.desc())\
            .limit(limit)\
            .all()
            
        return [
            {
                'name': earned.achievement.name,
                'description': earned.achievement.description,
                'date_earned': earned.date_earned,
                'movement_name': earned.movement_name
            }
            for earned in recent
        ]
