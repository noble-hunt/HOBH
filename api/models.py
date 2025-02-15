from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    email = Column(String, unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    workouts = relationship("WorkoutLog", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")

class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    movement_name = Column(String)
    weight = Column(Float)
    reps = Column(Integer)
    date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    completed_successfully = Column(Boolean, default=True)

    user = relationship("User", back_populates="workouts")

class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    achievement_name = Column(String)
    achieved_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="achievements")
