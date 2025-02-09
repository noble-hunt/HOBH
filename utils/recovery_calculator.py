import numpy as np
from datetime import datetime, timedelta
from .models import Session, WorkoutLog
from sqlalchemy import func
from typing import Dict, List, Tuple

class RecoveryCalculator:
    def __init__(self):
        self.volume_weight = 0.4  # Weight for volume component
        self.intensity_weight = 0.3  # Weight for intensity component
        self.frequency_weight = 0.3  # Weight for frequency component
        
        # Constants for strain calculation
        self.MAX_DAILY_VOLUME = 10000  # Maximum expected daily volume (kg)
        self.RECOVERY_WINDOW_DAYS = 7  # Days to look back for recovery calculation
        
    def calculate_strain_score(self, user_id: int, date: datetime) -> Dict:
        """
        Calculate training strain score based on:
        - Volume (total weight × reps)
        - Intensity (weight relative to PR)
        - Frequency (number of training sessions)
        
        Returns a score from 1-10 where:
        1-3: Low strain
        4-6: Moderate strain
        7-8: High strain
        9-10: Very high strain
        """
        try:
            with Session() as session:
                # Get workout data for the specified date
                daily_workouts = session.query(WorkoutLog).filter(
                    WorkoutLog.user_id == user_id,
                    func.date(WorkoutLog.date) == date.date()
                ).all()
                
                if not daily_workouts:
                    return {
                        "strain_score": 0,
                        "components": {
                            "volume": 0,
                            "intensity": 0,
                            "frequency": 0
                        },
                        "message": "No training data for this date"
                    }
                
                # Calculate components
                volume_score = self._calculate_volume_score(daily_workouts)
                intensity_score = self._calculate_intensity_score(session, daily_workouts)
                frequency_score = self._calculate_frequency_score(session, user_id, date)
                
                # Calculate weighted average
                strain_score = (
                    volume_score * self.volume_weight +
                    intensity_score * self.intensity_weight +
                    frequency_score * self.frequency_weight
                )
                
                # Scale to 1-10 range and round to one decimal
                strain_score = round(min(max(strain_score, 1), 10), 1)
                
                return {
                    "strain_score": strain_score,
                    "components": {
                        "volume": round(volume_score, 2),
                        "intensity": round(intensity_score, 2),
                        "frequency": round(frequency_score, 2)
                    },
                    "message": self._get_strain_message(strain_score)
                }
        except Exception as e:
            return {
                "strain_score": 0,
                "error": str(e),
                "message": "Error calculating strain score"
            }
    
    def calculate_recovery_score(self, user_id: int, date: datetime) -> Dict:
        """
        Calculate recovery score based on:
        - Time since last workout
        - Previous workout intensity
        - Cumulative training load
        
        Returns a score from 1-10 where:
        1-3: Poor recovery
        4-6: Moderate recovery
        7-8: Good recovery
        9-10: Excellent recovery
        """
        try:
            with Session() as session:
                # Get recent workouts within recovery window
                recent_workouts = session.query(WorkoutLog).filter(
                    WorkoutLog.user_id == user_id,
                    WorkoutLog.date >= date - timedelta(days=self.RECOVERY_WINDOW_DAYS),
                    WorkoutLog.date < date
                ).order_by(WorkoutLog.date.desc()).all()
                
                if not recent_workouts:
                    return {
                        "recovery_score": 10,
                        "message": "Fully recovered - No recent training load"
                    }
                
                # Calculate recovery score components
                time_score = self._calculate_time_score(recent_workouts[0].date, date)
                load_score = self._calculate_cumulative_load_score(recent_workouts)
                
                # Combine scores with weights
                recovery_score = (time_score * 0.6 + load_score * 0.4)
                recovery_score = round(min(max(recovery_score, 1), 10), 1)
                
                return {
                    "recovery_score": recovery_score,
                    "message": self._get_recovery_message(recovery_score)
                }
        except Exception as e:
            return {
                "recovery_score": 0,
                "error": str(e),
                "message": "Error calculating recovery score"
            }
    
    def _calculate_volume_score(self, workouts: List[WorkoutLog]) -> float:
        """Calculate volume component of strain score."""
        total_volume = sum(w.weight * w.reps for w in workouts)
        return (total_volume / self.MAX_DAILY_VOLUME) * 10
    
    def _calculate_intensity_score(self, session, workouts: List[WorkoutLog]) -> float:
        """Calculate intensity component of strain score."""
        if not workouts:
            return 0
            
        intensity_scores = []
        for workout in workouts:
            # Get PR for this movement
            pr_weight = session.query(func.max(WorkoutLog.weight)).filter(
                WorkoutLog.movement_id == workout.movement_id,
                WorkoutLog.user_id == workout.user_id
            ).scalar() or workout.weight
            
            # Calculate relative intensity
            relative_intensity = workout.weight / pr_weight if pr_weight else 1
            intensity_scores.append(relative_intensity)
            
        return np.mean(intensity_scores) * 10 if intensity_scores else 0
    
    def _calculate_frequency_score(self, session, user_id: int, date: datetime) -> float:
        """Calculate frequency component of strain score."""
        # Count workouts in the past 7 days
        workout_count = session.query(func.count(WorkoutLog.id)).filter(
            WorkoutLog.user_id == user_id,
            WorkoutLog.date >= date - timedelta(days=7),
            WorkoutLog.date <= date
        ).scalar()
        
        # Scale frequency score (assuming max 14 sessions per week)
        return min((workout_count / 14) * 10, 10)
    
    def _calculate_time_score(self, last_workout_date: datetime, current_date: datetime) -> float:
        """Calculate recovery score based on time since last workout."""
        hours_since_workout = (current_date - last_workout_date).total_seconds() / 3600
        
        if hours_since_workout < 24:
            return max(1, (hours_since_workout / 24) * 10)
        elif hours_since_workout < 48:
            return min(10, (hours_since_workout / 24) * 5)
        else:
            return 10
    
    def _calculate_cumulative_load_score(self, recent_workouts: List[WorkoutLog]) -> float:
        """Calculate recovery score based on cumulative training load."""
        if not recent_workouts:
            return 10
            
        # Calculate daily loads and weight them by recency
        daily_loads = []
        today = recent_workouts[0].date.date()
        
        for workout in recent_workouts:
            days_ago = (today - workout.date.date()).days
            daily_load = workout.weight * workout.reps
            weighted_load = daily_load * (0.8 ** days_ago)  # Exponential decay
            daily_loads.append(weighted_load)
            
        # Scale cumulative load to recovery score
        total_load = sum(daily_loads)
        recovery_score = 10 * (1 - min(total_load / (self.MAX_DAILY_VOLUME * 3), 0.9))
        return max(1, recovery_score)
    
    def _get_strain_message(self, score: float) -> str:
        """Get descriptive message for strain score."""
        if score <= 3:
            return "Low training strain - You can increase intensity"
        elif score <= 6:
            return "Moderate training strain - Good training stimulus"
        elif score <= 8:
            return "High training strain - Monitor recovery closely"
        else:
            return "Very high training strain - Consider reducing load"
            
    def _get_recovery_message(self, score: float) -> str:
        """Get descriptive message for recovery score."""
        if score <= 3:
            return "Poor recovery - Consider extra rest or light training"
        elif score <= 6:
            return "Moderate recovery - Proceed with caution"
        elif score <= 8:
            return "Good recovery - Ready for moderate training"
        else:
            return "Excellent recovery - Ready for intense training"
