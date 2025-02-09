from sqlalchemy import create_engine, Column, Integer, Float, String, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import ProgrammingError
import enum
import os

Base = declarative_base()

class DifficultyLevel(str, enum.Enum):
    BEGINNER = 'BEGINNER'
    INTERMEDIATE = 'INTERMEDIATE'
    ADVANCED = 'ADVANCED'
    ELITE = 'ELITE'

class Movement(Base):
    __tablename__ = 'movements'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    current_difficulty = Column(String, default=DifficultyLevel.BEGINNER.value)
    progression_threshold = Column(Integer, default=3)  # Number of successful sessions needed to progress

class WorkoutLog(Base):
    __tablename__ = 'workout_logs'

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    movement_id = Column(Integer, ForeignKey('movements.id'), nullable=False)
    weight = Column(Float, nullable=False)
    reps = Column(Integer, nullable=False)
    notes = Column(String)
    difficulty_level = Column(String, nullable=False)
    completed_successfully = Column(Integer, default=1)  # 1 for success, 0 for failure

# Create database engine and session
engine = create_engine(os.environ['DATABASE_URL'])
Session = sessionmaker(bind=engine)

def init_db():
    try:
        # Create tables
        Base.metadata.create_all(engine, checkfirst=True)
    except ProgrammingError as e:
        print(f"Error initializing database: {e}")
        raise