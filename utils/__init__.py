"""Initialize the utils package with proper import ordering."""
# First import base components
from .models import Base, Session, init_db

# Then import model classes
from .models import (
    WorkoutLog,
    Movement,
    DifficultyLevel,
    UserProfile,
    Achievement,
    EarnedAchievement
)

__all__ = [
    'Base',
    'Session',
    'init_db',
    'WorkoutLog',
    'Movement',
    'DifficultyLevel',
    'UserProfile',
    'Achievement',
    'EarnedAchievement'
]