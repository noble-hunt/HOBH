from sqlalchemy import create_engine, Column, Integer, Float, String, Date, ForeignKey, Table, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import ProgrammingError
import enum
import os
from datetime import datetime

Base = declarative_base()

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

# Create database engine and session
engine = create_engine(os.environ['DATABASE_URL'])
Session = sessionmaker(bind=engine)

def init_db():
    try:
        # Drop existing tables and recreate them
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
    except ProgrammingError as e:
        print(f"Error initializing database: {e}")
        raise