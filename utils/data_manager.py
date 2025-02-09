import pandas as pd
import os
from datetime import datetime

class DataManager:
    def __init__(self):
        self.movements = [
            "Strict Press", "Push Press", "Clean", "Jerk",
            "Clean and Jerk", "Snatch", "Overhead Squat",
            "Back Squat", "Front Squat"
        ]
        self.data_file = "data/workouts.csv"
        self._initialize_data_file()

    def _initialize_data_file(self):
        if not os.path.exists("data"):
            os.makedirs("data")
            
        if not os.path.exists(self.data_file):
            df = pd.DataFrame(columns=[
                'date', 'movement', 'weight', 'reps', 'notes'
            ])
            df.to_csv(self.data_file, index=False)

    def get_movements(self):
        return self.movements

    def log_movement(self, movement, weight, reps, date, notes=""):
        if movement not in self.movements:
            raise ValueError("Invalid movement")
            
        new_entry = pd.DataFrame([{
            'date': date,
            'movement': movement,
            'weight': weight,
            'reps': reps,
            'notes': notes
        }])
        
        df = pd.read_csv(self.data_file)
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_csv(self.data_file, index=False)

    def get_prs(self):
        df = pd.read_csv(self.data_file)
        prs = {}
        
        for movement in self.movements:
            movement_data = df[df['movement'] == movement]
            if not movement_data.empty:
                prs[movement] = movement_data['weight'].max()
            else:
                prs[movement] = 0
                
        return prs

    def get_movement_history(self, movement):
        df = pd.read_csv(self.data_file)
        movement_data = df[df['movement'] == movement].copy()
        movement_data['date'] = pd.to_datetime(movement_data['date'])
        return movement_data.sort_values('date')
