from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import uvicorn
import os
from datetime import datetime

from api.database import get_db, init_db
from api.models import *
from api.schemas import *
from api.auth import *

app = FastAPI(title="Fitness Tracker API", version="1.0.0")

# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper functions
def get_user_workouts(db: Session, user_id: int) -> List[WorkoutResponse]:
    workouts = db.query(WorkoutLog).filter(WorkoutLog.user_id == user_id).all()
    return [WorkoutResponse.from_orm(workout) for workout in workouts]

def create_user_workout(db: Session, workout: WorkoutCreate, user_id: int) -> WorkoutResponse:
    db_workout = WorkoutLog(
        user_id=user_id,
        movement_name=workout.movement_name,
        weight=workout.weight,
        reps=workout.reps,
        date=workout.date or datetime.utcnow(),
        notes=workout.notes,
        completed_successfully=workout.completed_successfully
    )
    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)
    return WorkoutResponse.from_orm(db_workout)

def get_user_progress_stats(db: Session, user_id: int) -> ProgressStats:
    workouts = db.query(WorkoutLog).filter(WorkoutLog.user_id == user_id).all()
    successful_workouts = len([w for w in workouts if w.completed_successfully])
    total_volume = sum(w.weight * w.reps for w in workouts)
    recent_prs = []  # Implementation for PRs calculation

    return ProgressStats(
        total_workouts=len(workouts),
        successful_workouts=successful_workouts,
        total_volume=total_volume,
        recent_prs=recent_prs
    )

# Auth routes
@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = authenticate_user(credentials.username, credentials.password, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/v1/auth/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = create_user(db, user)
        return db_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Workout routes
@app.get("/api/v1/workouts", response_model=List[WorkoutResponse])
async def get_workouts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return get_user_workouts(db, current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/v1/workouts", response_model=WorkoutResponse)
async def create_workout(
    workout: WorkoutCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return create_user_workout(db, workout, current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Progress routes
@app.get("/api/v1/progress/stats", response_model=ProgressStats)
async def get_progress_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return get_user_progress_stats(db, current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)