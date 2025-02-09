import pandas as pd
from datetime import datetime
from .models import Session, Movement, WorkoutLog, init_db
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError

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

    def log_movement(self, movement, weight, reps, date, notes=""):
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
                    notes=notes
                )
                session.add(workout_log)
            return True
        except SQLAlchemyError as e:
            raise Exception(f"Database error while logging movement: {str(e)}")
        except ValueError as e:
            raise ValueError(f"Invalid input: {str(e)}")
        except Exception as e:
            raise Exception(f"Error logging movement: {str(e)}")

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
                    'notes': log.notes
                } for log in logs]

                return pd.DataFrame(data)
        except SQLAlchemyError as e:
            print(f"Error retrieving movement history: {e}")
            return pd.DataFrame()