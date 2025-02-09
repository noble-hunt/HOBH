import pandas as pd
from datetime import datetime
from .models import Session, Movement, WorkoutLog, init_db, DifficultyLevel
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func

class DataManager:
    def __init__(self):
        self.movements = [
            "Strict Press", "Push Press", "Clean", "Jerk",
            "Clean and Jerk", "Snatch", "Overhead Squat",
            "Back Squat", "Front Squat"
        ]
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

    def log_movement(self, movement, weight, reps, date, notes="", completed_successfully=1):
        if movement not in self.movements:
            raise ValueError("Invalid movement")

        try:
            with self._session_scope() as session:
                movement_record = session.query(Movement).filter_by(name=movement).first()
                if not movement_record:
                    raise ValueError(f"Movement '{movement}' not found in database")

                workout_log = WorkoutLog(
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