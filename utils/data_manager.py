import pandas as pd
from datetime import datetime
from .models import Session, Movement, WorkoutLog, init_db, DifficultyLevel
from .achievement_manager import AchievementManager
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from .prediction import PRPredictor

class DataManager:
    def __init__(self):
        self.movements = [
            "Strict Press", "Push Press", "Clean", "Jerk",
            "Clean and Jerk", "Snatch", "Overhead Squat",
            "Back Squat", "Front Squat", "Deadlift", 
            "Bench Press", "Sumo Deadlift", "RDL"  # Added new movements
        ]
        self.achievement_manager = AchievementManager()
        self._initialize_database()

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

    def _initialize_database(self):
        init_db()
        with self._session_scope() as session:
            # Add movements if they don't exist
            existing_movements = session.query(Movement).all()
            existing_names = {m.name for m in existing_movements}

            for movement_name in self.movements:
                if movement_name not in existing_names:
                    movement = Movement(name=movement_name)
                    session.add(movement)

    def get_movements(self):
        return self.movements

    def log_movement(self, user_id, movement, weight, reps, date, notes="", completed_successfully=1):
        # Case-insensitive movement validation
        valid_movements = {m.lower(): m for m in self.movements}
        movement_lower = movement.lower()

        if movement_lower not in valid_movements:
            raise ValueError(f"Invalid movement: {movement}. Valid movements are: {', '.join(self.movements)}")

        # Use the correctly cased movement name
        movement_name = valid_movements[movement_lower]

        try:
            with self._session_scope() as session:
                movement_record = session.query(Movement).filter(
                    func.lower(Movement.name) == movement_lower
                ).first()

                if not movement_record:
                    raise ValueError(f"Movement '{movement}' not found in database")

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
                session.add(workout_log)

                # Update progression after logging
                self._update_movement_progression(session, movement_record)

                # Check for achievements
                self.achievement_manager.check_and_award_achievements(workout_log)

            return True
        except SQLAlchemyError as e:
            raise Exception(f"Database error while logging movement: {str(e)}")
        except ValueError as e:
            raise ValueError(f"Invalid input: {str(e)}")
        except Exception as e:
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
                    'date': log.date,
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

    def get_recent_logs(self, user_id, limit=5):
        """Get recent workout logs for a specific user."""
        try:
            with self._session_scope() as session:
                logs = session.query(WorkoutLog)\
                    .filter_by(user_id=user_id)\
                    .order_by(WorkoutLog.date.desc())\
                    .limit(limit)\
                    .all()
                return logs
        except SQLAlchemyError as e:
            print(f"Error retrieving recent logs: {e}")
            return []
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