from sqlalchemy import create_engine, Column, Integer, Float, String, Date, ForeignKey, Table, DateTime, text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import ProgrammingError, OperationalError
from sqlalchemy.pool import NullPool
import enum
import os
from datetime import datetime
import time

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
    date_earned = Column(DateTime, default=datetime.utcnow)
    movement_name = Column(String)  # Optional: specific movement this was earned for

    # Relationship
    achievement = relationship('Achievement')

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

class UserProfile(Base):
    __tablename__ = 'user_profiles'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    display_name = Column(String)
    bio = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    followers = relationship(
        'UserProfile',
        secondary=following,
        primaryjoin=(id == following.c.followed_id),
        secondaryjoin=(id == following.c.follower_id),
        backref='following'
    )
    workout_logs = relationship('WorkoutLog', back_populates='user')
    shared_workouts = relationship('SharedWorkout', back_populates='user')

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
            return engine
        except OperationalError as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(retry_delay)

# Create database engine and session
engine = get_db_engine()
Session = sessionmaker(bind=engine)

def init_db():
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            Base.metadata.create_all(engine)

            # Initialize default achievements
            session = Session()

            # Check if achievements already exist
            if session.query(Achievement).count() == 0:
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

            session.close()
            break
        except (ProgrammingError, OperationalError) as e:
            if attempt == max_retries - 1:
                print(f"Failed to initialize database after {max_retries} attempts")
                raise
            print(f"Database initialization attempt {attempt + 1} failed, retrying...")
            time.sleep(retry_delay)