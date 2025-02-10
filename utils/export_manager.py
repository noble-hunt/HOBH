"""Health data export and sharing functionality."""
import json
import csv
from datetime import datetime
from io import StringIO
from typing import Dict, List, Optional
import pandas as pd
from sqlalchemy.orm import Session
from utils.models import (
    WorkoutLog,
    WearableData,
    UserProfile,
    WearableDevice
)

class HealthDataExporter:
    """Manages health data export and sharing functionality."""

    def __init__(self, session: Session):
        self.session = session

    def export_workout_data(
        self,
        user_id: int,
        format: str = 'csv',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """Export workout data in specified format."""
        query = self.session.query(WorkoutLog).filter(
            WorkoutLog.user_id == user_id
        )

        if start_date:
            query = query.filter(WorkoutLog.date >= start_date)
        if end_date:
            query = query.filter(WorkoutLog.date <= end_date)

        workouts = query.all()
        
        if format.lower() == 'csv':
            return self._generate_csv(workouts)
        elif format.lower() == 'json':
            return self._generate_json(workouts)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def export_wearable_data(
        self,
        user_id: int,
        format: str = 'csv',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        metrics: Optional[List[str]] = None
    ) -> Dict:
        """Export wearable device data in specified format."""
        # Get user's devices
        devices = self.session.query(WearableDevice).filter(
            WearableDevice.user_id == user_id
        ).all()
        
        device_ids = [device.id for device in devices]
        
        # Query wearable data
        query = self.session.query(WearableData).filter(
            WearableData.device_id.in_(device_ids)
        )

        if start_date:
            query = query.filter(WearableData.timestamp >= start_date)
        if end_date:
            query = query.filter(WearableData.timestamp <= end_date)
        if metrics:
            query = query.filter(WearableData.metric_type.in_(metrics))

        data = query.all()
        
        if format.lower() == 'csv':
            return self._generate_wearable_csv(data)
        elif format.lower() == 'json':
            return self._generate_wearable_json(data)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_csv(self, workouts: List[WorkoutLog]) -> Dict:
        """Generate CSV format for workout data."""
        output = StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            'Date', 'Movement', 'Weight (kg)', 'Reps',
            'Difficulty', 'Completed', 'Notes'
        ])
        
        # Write workout data
        for workout in workouts:
            writer.writerow([
                workout.date,
                workout.movement.name if workout.movement else '',
                workout.weight,
                workout.reps,
                workout.difficulty,
                'Yes' if workout.completed else 'No',
                workout.notes or ''
            ])
        
        return {
            'content': output.getvalue(),
            'filename': f'workout_data_{datetime.now().strftime("%Y%m%d")}.csv',
            'mimetype': 'text/csv'
        }

    def _generate_json(self, workouts: List[WorkoutLog]) -> Dict:
        """Generate JSON format for workout data."""
        data = []
        for workout in workouts:
            data.append({
                'date': workout.date.isoformat(),
                'movement': workout.movement.name if workout.movement else None,
                'weight': workout.weight,
                'reps': workout.reps,
                'difficulty': workout.difficulty,
                'completed': workout.completed,
                'notes': workout.notes
            })
        
        return {
            'content': json.dumps(data, indent=2),
            'filename': f'workout_data_{datetime.now().strftime("%Y%m%d")}.json',
            'mimetype': 'application/json'
        }

    def _generate_wearable_csv(self, data: List[WearableData]) -> Dict:
        """Generate CSV format for wearable data."""
        output = StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            'Timestamp', 'Device Type', 'Metric Type',
            'Value', 'Unit', 'Confidence'
        ])
        
        # Write wearable data
        for record in data:
            writer.writerow([
                record.timestamp,
                record.device.device_type if record.device else '',
                record.metric_type,
                record.metric_value,
                record.metric_unit,
                record.confidence
            ])
        
        return {
            'content': output.getvalue(),
            'filename': f'wearable_data_{datetime.now().strftime("%Y%m%d")}.csv',
            'mimetype': 'text/csv'
        }

    def _generate_wearable_json(self, data: List[WearableData]) -> Dict:
        """Generate JSON format for wearable data."""
        export_data = []
        for record in data:
            export_data.append({
                'timestamp': record.timestamp.isoformat(),
                'device_type': record.device.device_type if record.device else None,
                'metric_type': record.metric_type,
                'value': record.metric_value,
                'unit': record.metric_unit,
                'confidence': record.confidence
            })
        
        return {
            'content': json.dumps(export_data, indent=2),
            'filename': f'wearable_data_{datetime.now().strftime("%Y%m%d")}.json',
            'mimetype': 'application/json'
        }
