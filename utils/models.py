from sqlalchemy import create_engine, Column, Integer, Float, String, Date, ForeignKey, Table, DateTime, text, Boolean, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import ProgrammingError, OperationalError
from sqlalchemy.pool import NullPool
import enum
import os
from datetime import datetime, date
import time
from typing import List

# Add new enum class after existing enums
class WearableMetricType(str, enum.Enum):
    HEART_RATE = 'HEART_RATE'
    STEPS = 'STEPS'
    CALORIES = 'CALORIES'
    SLEEP = 'SLEEP'
    RECOVERY_SCORE = 'RECOVERY_SCORE'
    STRAIN_SCORE = 'STRAIN_SCORE'
    READINESS_SCORE = 'READINESS_SCORE'

# Create Base class for declarative models
Base = declarative_base()

# Achievement Types Enum
class AchievementType(str, enum.Enum):
    WEIGHT_MILESTONE = 'WEIGHT_MILESTONE'
    CONSECUTIVE_DAYS = 'CONSECUTIVE_DAYS'
    MOVEMENT_MASTERY = 'MOVEMENT_MASTERY'
    PROGRESSION_MILESTONE = 'PROGRESSION_MILESTONE'

class Achievement(Base):
    __tablename__ = 'achievements'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    type = Column(String, nullable=False)
    criteria_value = Column(Float)  # e.g., weight threshold or days streak
    icon_name = Column(String)  # Name of the achievement icon
    created_at = Column(DateTime, default=datetime.utcnow)

class EarnedAchievement(Base):
    __tablename__ = 'earned_achievements'

    id = Column(Integer, primary_key=True)
    achievement_id = Column(Integer, ForeignKey('achievements.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user_profiles.id'), nullable=False)
    date_earned = Column(DateTime, default=datetime.utcnow)
    movement_name = Column(String)  # Optional: specific movement this was earned for

    # Relationship
    achievement = relationship('Achievement')
    user = relationship('UserProfile')

# User following relationship table
following = Table(
    'following',
    Base.metadata,
    Column('follower_id', Integer, ForeignKey('user_profiles.id'), primary_key=True),
    Column('followed_id', Integer, ForeignKey('user_profiles.id'), primary_key=True)
)

class DifficultyLevel(str, enum.Enum):
    BEGINNER = 'BEGINNER'
    INTERMEDIATE = 'INTERMEDIATE'
    ADVANCED = 'ADVANCED'
    ELITE = 'ELITE'

class WearableDevice(Base):
    __tablename__ = 'wearable_devices'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user_profiles.id'), nullable=False)
    device_type = Column(String, nullable=False)  # e.g., 'WHOOP', 'FITBIT', 'GARMIN'
    device_id = Column(String, unique=True)
    last_sync = Column(DateTime)
    auth_token = Column(String)
    refresh_token = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship('UserProfile', back_populates='wearable_devices')
    wearable_data = relationship('WearableData', back_populates='device')

class WearableData(Base):
    __tablename__ = 'wearable_data'

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('wearable_devices.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    metric_type = Column(String, nullable=False)  # References WearableMetricType
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String)  # e.g., 'bpm', 'steps', 'calories'
    confidence = Column(Float)  # Confidence score of the measurement
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    device = relationship('WearableDevice', back_populates='wearable_data')

class UserProfile(Base):
    __tablename__ = 'user_profiles'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(LargeBinary, nullable=False)
    display_name = Column(String)
    bio = Column(String)
    avatar_style = Column(String, default='adventurer')
    avatar_background = Column(String, default='#F0F2F6')
    avatar_features = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Add wearable_devices relationship
    wearable_devices = relationship('WearableDevice', back_populates='user')

    # Existing relationships
    followers = relationship(
        'UserProfile',
        secondary=following,
        primaryjoin=(id == following.c.followed_id),
        secondaryjoin=(id == following.c.follower_id),
        backref='following'
    )
    workout_logs = relationship('WorkoutLog', back_populates='user')
    shared_workouts = relationship('SharedWorkout', back_populates='user')
    earned_achievements = relationship('EarnedAchievement', back_populates='user')

class Movement(Base):
    __tablename__ = 'movements'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    current_difficulty = Column(String, default=DifficultyLevel.BEGINNER.value)
    progression_threshold = Column(Integer, default=3)  # Number of successful sessions needed to progress

class WorkoutLog(Base):
    __tablename__ = 'workout_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user_profiles.id'), nullable=False)
    date = Column(Date, nullable=False)
    movement_id = Column(Integer, ForeignKey('movements.id'), nullable=False)
    weight = Column(Float, nullable=False)
    reps = Column(Integer, nullable=False)
    notes = Column(String)
    difficulty_level = Column(String, nullable=False)
    completed_successfully = Column(Integer, default=1)  # 1 for success, 0 for failure

    # Relationships
    user = relationship('UserProfile', back_populates='workout_logs')
    movement = relationship('Movement')

class SharedWorkout(Base):
    __tablename__ = 'shared_workouts'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user_profiles.id'), nullable=False)
    workout_log_id = Column(Integer, ForeignKey('workout_logs.id'), nullable=False)
    shared_at = Column(DateTime, default=datetime.utcnow)
    caption = Column(String)
    likes = Column(Integer, default=0)

    # Relationships
    user = relationship('UserProfile', back_populates='shared_workouts')
    workout_log = relationship('WorkoutLog')

def get_db_engine(max_retries=3, retry_delay=1):
    """Create database engine with retry logic"""
    print("Attempting to create database engine...")
    for attempt in range(max_retries):
        try:
            # Create engine without connection pooling and with SSL parameters
            engine = create_engine(
                os.environ['DATABASE_URL'],
                poolclass=NullPool,
                connect_args={
                    'sslmode': 'require',
                    'connect_timeout': 10
                }
            )
            # Test the connection using proper SQLAlchemy query
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Database engine created successfully!")
            return engine
        except OperationalError as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                raise
            time.sleep(retry_delay)

# Create database engine and session
engine = get_db_engine()
Session = sessionmaker(bind=engine)

def init_db():
    print("Initializing database...")
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1} to create tables...")
            Base.metadata.create_all(engine)
            print("Tables created successfully!")

            # Initialize default achievements
            session = Session()

            # Check if achievements already exist
            if session.query(Achievement).count() == 0:
                print("Adding default achievements...")
                default_achievements = [
                    Achievement(
                        name="Weight Master",
                        description="Lift 100kg or more in any movement",
                        type=AchievementType.WEIGHT_MILESTONE,
                        criteria_value=100.0,
                        icon_name="weight_master"
                    ),
                    Achievement(
                        name="Consistency King",
                        description="Log workouts for 7 consecutive days",
                        type=AchievementType.CONSECUTIVE_DAYS,
                        criteria_value=7,
                        icon_name="consistency_king"
                    ),
                    Achievement(
                        name="Movement Expert",
                        description="Reach ADVANCED level in any movement",
                        type=AchievementType.MOVEMENT_MASTERY,
                        criteria_value=0,
                        icon_name="movement_expert"
                    ),
                    Achievement(
                        name="Elite Status",
                        description="Reach ELITE level in any movement",
                        type=AchievementType.PROGRESSION_MILESTONE,
                        criteria_value=0,
                        icon_name="elite_status"
                    )
                ]
                session.add_all(default_achievements)
                session.commit()
                print("Default achievements added successfully!")

            session.close()
            print("Database initialization completed successfully!")
            break
        except (ProgrammingError, OperationalError) as e:
            print(f"Error during attempt {attempt + 1}: {str(e)}")
            if attempt == max_retries - 1:
                print(f"Failed to initialize database after {max_retries} attempts")
                raise
            print(f"Database initialization attempt {attempt + 1} failed, retrying...")
            time.sleep(retry_delay)