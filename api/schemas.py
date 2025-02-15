from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# Auth schemas
class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    username: str
    password: str

# User schemas
class UserBase(BaseModel):
    username: str
    email: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Workout schemas
class WorkoutBase(BaseModel):
    movement_name: str
    weight: float
    reps: int
    notes: Optional[str] = None
    completed_successfully: bool = True

class WorkoutCreate(WorkoutBase):
    date: Optional[datetime] = None

class WorkoutResponse(WorkoutBase):
    id: int
    user_id: int
    date: datetime

    class Config:
        from_attributes = True

# Progress schemas
class ProgressStats(BaseModel):
    total_workouts: int
    successful_workouts: int
    total_volume: float
    recent_prs: List[WorkoutResponse]
    
    class Config:
        from_attributes = True
