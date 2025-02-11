"""Data management module for the application."""
import pandas as pd
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound
import traceback
import sys

# Import models through the package init to ensure proper initialization
from utils import (
    Session,
    Movement,
    WorkoutLog,
    init_db,
    DifficultyLevel
)
from utils.achievement_manager import AchievementManager
from contextlib import contextmanager
from utils.prediction import PRPredictor

# Debug logging
print("DataManager Module Loading")
print(f"Python version: {sys.version}")
print(f"Module search path: {sys.path}")
print(f"WorkoutLog imported as: {WorkoutLog}")
print(f"WorkoutLog module: {WorkoutLog.__module__}")

class DataManager:
    def __init__(self):
        """Initialize the DataManager with movement list and required components."""
        # Primary movements for home screen status
        self.primary_movements = [
            "Strict Press", "Push Press", "Clean", "Jerk",
            "Snatch", "Overhead Squat", "Front Squat", 
            "Back Squat", "Deadlift", "Bench Press"
        ]

        # All movements including CrossFit movements
        self.movements = [
            # Olympic Lifts
            "Strict Press", "Push Press", "Clean", "Jerk",
            "Clean and Jerk", "Snatch", "Overhead Squat",
            "Back Squat", "Front Squat", "Deadlift", 
            "Bench Press", "Sumo Deadlift", "RDL",

            # Bodyweight Movements
            "Burpees", "Pull-ups", "Toes To Bar",
            "Handstand Push-ups", "Push-ups", "Air Squats",
            "Bodyweight Lunges",

            # Dumbbell/Kettlebell Movements
            "KB Swings", "DB Snatches", "DB Clean & Jerks",
            "DB Thrusters", "Barbell Thrusters",

            # Cardio Equipment
            "Row Calories", "Bike Erg Calories",
            "Ski Erg Calories", "Echo Bike Calories"
        ]
        try:
            print("Initializing DataManager")
            self.achievement_manager = AchievementManager()
            self._initialize_database()
            print("DataManager initialization complete")
        except Exception as e:
            print(f"Error initializing DataManager: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            raise

    @contextmanager
    def _session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_recent_logs(self, user_id, limit=5):
        """Get recent workout logs for a specific user with eager loading."""
        try:
            print(f"Debug - Getting recent logs for user {user_id}")
            from sqlalchemy.orm import joinedload

            with self._session_scope() as session:
                # Query with eager loading
                logs = session.query(WorkoutLog)\
                    .options(joinedload(WorkoutLog.movement))\
                    .filter_by(user_id=user_id)\
                    .order_by(WorkoutLog.date.desc())\
                    .limit(limit)\
                    .all()

                # Materialize all the data we need while session is open
                materialized_logs = []
                for log in logs:
                    materialized_logs.append({
                        'id': log.id,
                        'date': log.date,
                        'weight': log.weight,
                        'reps': log.reps,
                        'notes': log.notes,
                        'difficulty_level': log.difficulty_level,
                        'completed_successfully': log.completed_successfully,
                        'movement': {
                            'id': log.movement.id,
                            'name': log.movement.name,
                            'current_difficulty': log.movement.current_difficulty
                        } if log.movement else None
                    })

                print(f"Debug - Retrieved {len(materialized_logs)} logs")
                return materialized_logs

        except Exception as e:
            print(f"Error retrieving recent logs: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return []

    def _initialize_database(self):
        """Initialize database with required tables and initial data."""
        try:
            init_db()
            with self._session_scope() as session:
                # Add movements if they don't exist
                existing_movements = session.query(Movement).all()
                existing_names = {m.name for m in existing_movements}

                for movement_name in self.movements:
                    if movement_name not in existing_names:
                        movement = Movement(name=movement_name)
                        session.add(movement)
        except Exception as e:
            print(f"Error in _initialize_database: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            raise

    def log_movement(self, user_id, movement, weight, reps, date, notes="", completed_successfully=1):
        """Log a movement with proper type handling and error reporting."""
        try:
            print(f"Debug - Starting log_movement")
            print(f"Debug - WorkoutLog class available: {WorkoutLog}")
            print(f"Debug - Movement input: {movement}, type: {type(movement)}")
            print(f"Debug - User ID: {user_id}")

            # Ensure movement is a string
            movement = str(movement).strip()

            # Case-insensitive movement validation
            valid_movements = {m.lower(): m for m in self.movements}
            movement_lower = movement.lower()

            if movement_lower not in valid_movements:
                raise ValueError(f"Invalid movement: {movement}. Valid movements are: {', '.join(self.movements)}")

            # Use the correctly cased movement name
            movement_name = valid_movements[movement_lower]

            print(f"Debug - Looking up movement: {movement_name}")

            with self._session_scope() as session:
                # Verify WorkoutLog is still accessible
                print(f"Debug - Verifying WorkoutLog in session context: {WorkoutLog}")

                movement_record = session.query(Movement).filter(
                    func.lower(Movement.name) == movement_lower
                ).first()

                if not movement_record:
                    raise ValueError(f"Movement '{movement}' not found in database")

                # Create new workout log
                try:
                    workout_log = WorkoutLog(
                        user_id=user_id,
                        date=date,
                        movement_id=movement_record.id,
                        weight=float(weight),
                        reps=int(reps),
                        notes=notes,
                        difficulty_level=movement_record.current_difficulty,
                        completed_successfully=completed_successfully
                    )
                    print(f"Debug - Created workout log: {workout_log}")
                except Exception as e:
                    print(f"Error creating WorkoutLog: {str(e)}")
                    print(f"Traceback: {traceback.format_exc()}")
                    raise

                session.add(workout_log)
                session.flush()  # Flush to get the ID

                # Update progression after logging
                self._update_movement_progression(session, movement_record)

                # Check for achievements
                self.achievement_manager.check_and_award_achievements(workout_log)

                print("Movement logged successfully")
                return True

        except Exception as e:
            print(f"Detailed error in log_movement: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            print(f"Type of movement: {type(movement)}")
            print(f"Type of WorkoutLog: {type(WorkoutLog) if 'WorkoutLog' in locals() else 'Not defined'}")
            print(f"Module containing WorkoutLog: {WorkoutLog.__module__ if 'WorkoutLog' in locals() else 'Not available'}")
            raise Exception(f"Error logging movement: {str(e)}")

    def _update_movement_progression(self, session, movement_record):
        """Update movement difficulty based on recent performance"""
        recent_logs = session.query(WorkoutLog)\
            .filter_by(movement_id=movement_record.id)\
            .order_by(WorkoutLog.date.desc())\
            .limit(movement_record.progression_threshold)\
            .all()

        if len(recent_logs) >= movement_record.progression_threshold:
            successful_sessions = sum(log.completed_successfully for log in recent_logs)

            # Progress if all recent sessions were successful
            current_difficulty = DifficultyLevel(movement_record.current_difficulty)

            # Progress if all recent sessions were successful
            if successful_sessions == movement_record.progression_threshold:
                if current_difficulty != DifficultyLevel.ELITE:
                    next_level = list(DifficultyLevel)[list(DifficultyLevel).index(current_difficulty) + 1]
                    movement_record.current_difficulty = next_level.value
            # Regress if more than half were unsuccessful
            elif successful_sessions < (movement_record.progression_threshold // 2):
                if current_difficulty != DifficultyLevel.BEGINNER:
                    prev_level = list(DifficultyLevel)[list(DifficultyLevel).index(current_difficulty) - 1]
                    movement_record.current_difficulty = prev_level.value

    def get_primary_movements(self):
        """Get the list of primary movements for home screen display."""
        return self.primary_movements

    def get_all_movements(self): #Renamed to avoid conflict
        """Get the full list of available movements."""
        return self.movements

    def get_movement_difficulty(self, movement):
        try:
            with self._session_scope() as session:
                movement_record = session.query(Movement).filter_by(name=movement).first()
                if movement_record:
                    return DifficultyLevel(movement_record.current_difficulty)
                return DifficultyLevel.BEGINNER
        except SQLAlchemyError as e:
            print(f"Error retrieving movement difficulty: {e}")
            return DifficultyLevel.BEGINNER

    def get_prs(self):
        prs = {}
        try:
            with self._session_scope() as session:
                for movement in self.movements:
                    movement_record = session.query(Movement).filter_by(name=movement).first()
                    if movement_record:
                        max_weight = session.query(WorkoutLog.weight)\
                            .filter_by(movement_id=movement_record.id)\
                            .order_by(WorkoutLog.weight.desc())\
                            .first()
                        prs[movement] = max_weight[0] if max_weight else 0
                    else:
                        prs[movement] = 0
            return prs
        except SQLAlchemyError as e:
            print(f"Error retrieving PRs: {e}")
            return {movement: 0 for movement in self.movements}

    def get_movement_history(self, movement):
        try:
            with self._session_scope() as session:
                movement_record = session.query(Movement).filter_by(name=movement).first()
                if not movement_record:
                    return pd.DataFrame()

                logs = session.query(WorkoutLog)\
                    .filter_by(movement_id=movement_record.id)\
                    .order_by(WorkoutLog.date)\
                    .all()

                data = [{
                    'date': pd.Timestamp(log.date),  # Convert to pandas Timestamp
                    'movement': movement,
                    'weight': log.weight,
                    'reps': log.reps,
                    'notes': log.notes,
                    'difficulty': log.difficulty_level,
                    'completed': log.completed_successfully
                } for log in logs]

                return pd.DataFrame(data)
        except SQLAlchemyError as e:
            print(f"Error retrieving movement history: {e}")
            return pd.DataFrame()

    def get_achievements(self):
        """Get all earned achievements."""
        return self.achievement_manager.get_earned_achievements()

    def get_movement_predictions(self, movement):
        """Get PR predictions and training insights for a movement."""
        try:
            with self._session_scope() as session:
                movement_record = session.query(Movement).filter_by(name=movement).first()
                if not movement_record:
                    return None

                history = self.get_movement_history(movement)
                if history.empty:
                    return None

                predictor = PRPredictor(history)
                predictions = predictor.predict_pr()
                insights = predictor.get_training_insights()

                return {
                    'predictions': predictions,
                    'insights': insights
                }
        except SQLAlchemyError as e:
            print(f"Error getting movement predictions: {e}")
            return None

    def get_workout_streak(self, user_id):
        """Calculate the current workout streak for a user."""
        try:
            with self._session_scope() as session:
                # Get all workout dates for the user
                workout_dates = session.query(func.date(WorkoutLog.date))\
                    .filter(WorkoutLog.user_id == user_id)\
                    .distinct()\
                    .order_by(func.date(WorkoutLog.date).desc())\
                    .all()

                if not workout_dates:
                    return 0

                # Convert to list of dates
                workout_dates = [date[0] for date in workout_dates]

                # Calculate current streak
                current_streak = 1  # Start with 1 for the most recent workout
                latest_date = workout_dates[0]

                for prev_date in workout_dates[1:]:
                    # Check if dates are consecutive
                    date_diff = (latest_date - prev_date).days
                    if date_diff == 1:
                        current_streak += 1
                        latest_date = prev_date
                    else:
                        break  # Streak is broken

                return current_streak

        except Exception as e:
            print(f"Error calculating workout streak: {str(e)}")
            return 0

    def get_training_load(self, user_id):
        """Get training load status for a user."""
        try:
            with self._session_scope() as session:
                # Get recent workout logs for load calculation
                recent_logs = session.query(WorkoutLog)\
                    .filter_by(user_id=user_id)\
                    .order_by(WorkoutLog.date.desc())\
                    .limit(14)\
                    .all()

                if not recent_logs:
                    return None

                # Calculate metrics
                current_load = self._calculate_training_load(recent_logs)
                recovery_score = self._calculate_recovery_score(recent_logs)
                readiness_score = min(100, int((recovery_score + 70) / 2))  # Simplified calculation

                # Determine status messages
                load_status = self._get_load_status(current_load)
                recovery_status = self._get_recovery_status(recovery_score)
                readiness_status = self._get_readiness_status(readiness_score)

                return {
                    'current_load': current_load,
                    'load_status': load_status,
                    'recovery_score': recovery_score,
                    'recovery_status': recovery_status,
                    'readiness_score': readiness_score,
                    'readiness_status': readiness_status
                }

        except Exception as e:
            print(f"Error getting training load: {str(e)}")
            return None

    def _calculate_training_load(self, logs):
        """Calculate training load from recent workout logs."""
        if not logs:
            return 0.0

        total_load = 0
        for log in logs:
            # Simple load calculation: weight * reps * difficulty multiplier
            difficulty_multiplier = {
                'BEGINNER': 1.0,
                'INTERMEDIATE': 1.2,
                'ADVANCED': 1.5,
                'ELITE': 2.0
            }.get(log.difficulty_level, 1.0)

            daily_load = log.weight * log.reps * difficulty_multiplier
            total_load += daily_load

        return total_load / len(logs)  # Average daily load

    def _calculate_recovery_score(self, logs):
        """Calculate recovery score based on recent workout intensity."""
        if not logs:
            return 100

        # Simple recovery calculation based on recent workout intensity
        recent_intensity = sum(log.weight * log.reps for log in logs[:3]) / 3
        base_recovery = 100 - min(recent_intensity / 100, 50)  # Cap the reduction at 50%
        return max(0, min(100, int(base_recovery)))

    def _get_load_status(self, load):
        """Get status message based on training load."""
        if load < 500:
            return "Low - You can increase intensity"
        elif load < 1000:
            return "Optimal - Good training balance"
        else:
            return "High - Consider recovery"

    def _get_recovery_status(self, score):
        """Get status message based on recovery score."""
        if score >= 80:
            return "Well Recovered"
        elif score >= 60:
            return "Moderately Recovered"
        else:
            return "Recovery Needed"

    def _get_readiness_status(self, score):
        """Get status message based on readiness score."""
        if score >= 80:
            return "Ready for High Intensity"
        elif score >= 60:
            return "Ready for Moderate Training"
        else:
            return "Light Training Recommended"

    def get_movement_status(self, user_id):
        """Get movement progress status for primary movements."""
        try:
            with self._session_scope() as session:
                movement_stats = []

                for movement_name in self.primary_movements:
                    # Get movement record
                    movement = session.query(Movement)\
                        .filter(func.lower(Movement.name) == func.lower(movement_name))\
                        .first()

                    if movement:
                        # Get personal best
                        max_weight = session.query(func.max(WorkoutLog.weight))\
                            .filter_by(
                                user_id=user_id,
                                movement_id=movement.id
                            ).scalar() or 0

                        # Calculate progress to next level
                        current_level = DifficultyLevel(movement.current_difficulty)
                        progress = self._calculate_level_progress(
                            session, user_id, movement.id, current_level
                        )

                        movement_stats.append({
                            'name': movement_name,
                            'current_level': current_level.value,
                            'personal_best': max_weight,
                            'progress_to_next': progress
                        })

                return movement_stats

        except Exception as e:
            print(f"Error getting movement status: {str(e)}")
            return None

    def _calculate_level_progress(self, session, user_id, movement_id, current_level):
        """Calculate progress percentage to next level."""
        try:
            # Get recent successful workouts
            recent_successful = session.query(WorkoutLog)\
                .filter_by(
                    user_id=user_id,
                    movement_id=movement_id,
                    completed_successfully=1
                )\
                .order_by(WorkoutLog.date.desc())\
                .limit(3)\
                .count()

            # Calculate progress percentage (each successful workout is worth 33.33%)
            progress = min(100, int((recent_successful / 3) * 100))
            return progress

        except Exception as e:
            print(f"Error calculating level progress: {str(e)}")
            return 0