import pandas as pd
from datetime import datetime
from .models import Session, Movement, WorkoutLog, init_db

class DataManager:
    def __init__(self):
        self.movements = [
            "Strict Press", "Push Press", "Clean", "Jerk",
            "Clean and Jerk", "Snatch", "Overhead Squat",
            "Back Squat", "Front Squat"
        ]
        self._initialize_database()

    def _initialize_database(self):
        init_db()
        session = Session()

        # Add movements if they don't exist
        existing_movements = session.query(Movement).all()
        existing_names = {m.name for m in existing_movements}

        for movement_name in self.movements:
            if movement_name not in existing_names:
                movement = Movement(name=movement_name)
                session.add(movement)

        session.commit()
        session.close()

    def get_movements(self):
        return self.movements

    def log_movement(self, movement, weight, reps, date, notes=""):
        if movement not in self.movements:
            raise ValueError("Invalid movement")

        session = Session()
        movement_record = session.query(Movement).filter_by(name=movement).first()

        workout_log = WorkoutLog(
            date=date,
            movement_id=movement_record.id,
            weight=weight,
            reps=reps,
            notes=notes
        )

        session.add(workout_log)
        session.commit()
        session.close()

    def get_prs(self):
        session = Session()
        prs = {}

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

        session.close()
        return prs

    def get_movement_history(self, movement):
        session = Session()
        movement_record = session.query(Movement).filter_by(name=movement).first()

        if not movement_record:
            session.close()
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

        session.close()
        return pd.DataFrame(data)