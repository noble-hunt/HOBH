from sqlalchemy import create_engine, Column, Integer, Float, String, Date, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import ProgrammingError
import enum
import os

Base = declarative_base()

class DifficultyLevel(enum.Enum):
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    ELITE = 4

class Movement(Base):
    __tablename__ = 'movements'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    current_difficulty = Column(Enum(DifficultyLevel), default=DifficultyLevel.BEGINNER)
    progression_threshold = Column(Integer, default=3)  # Number of successful sessions needed to progress

class WorkoutLog(Base):
    __tablename__ = 'workout_logs'

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    movement_id = Column(Integer, ForeignKey('movements.id'), nullable=False)
    weight = Column(Float, nullable=False)
    reps = Column(Integer, nullable=False)
    notes = Column(String)
    difficulty_level = Column(Enum(DifficultyLevel), nullable=False)
    completed_successfully = Column(Integer, default=1)  # 1 for success, 0 for failure

# Create database engine and session
engine = create_engine(os.environ['DATABASE_URL'])
Session = sessionmaker(bind=engine)

# Create tables
def init_db():
    try:
        # Try to create tables only if they don't exist
        Base.metadata.create_all(engine, checkfirst=True)
    except ProgrammingError as e:
        print(f"Error initializing database: {e}")
        raise