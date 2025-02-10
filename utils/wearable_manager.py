"""Wearable device integration and data management."""
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
import requests

from utils.models import (
    WearableDevice,
    WearableData,
    WearableMetricType,
    UserProfile
)

class WearableManager:
    """Manages wearable device integration and data synchronization."""

    def __init__(self, session: Session):
        self.session = session
        self.supported_devices = {
            'WHOOP': self._sync_whoop_data,
            'FITBIT': self._sync_fitbit_data,
            'GARMIN': self._sync_garmin_data,
            'APPLE_WATCH': self._sync_apple_watch_data,
            'OURA': self._sync_oura_data
        }

    def register_device(
        self,
        user_id: int,
        device_type: str,
        device_id: str,
        auth_token: str,
        refresh_token: Optional[str] = None,
        team_id: Optional[str] = None,
        key_id: Optional[str] = None,
        private_key: Optional[str] = None
    ) -> WearableDevice:
        """Register a new wearable device for a user."""
        device = WearableDevice(
            user_id=user_id,
            device_type=device_type.upper(),
            device_id=device_id,
            auth_token=auth_token,
            refresh_token=refresh_token,
            team_id=team_id,
            key_id=key_id,
            private_key=private_key,
            last_sync=datetime.utcnow()
        )
        self.session.add(device)
        self.session.commit()
        return device

    def sync_device_data(self, device_id: int) -> Tuple[bool, str]:
        """Synchronize data from a specific device."""
        try:
            device = self.session.query(WearableDevice).get(device_id)
            if not device:
                return False, "Device not found"

            if not device.is_active:
                return False, "Device is inactive"

            # Get sync function for device type
            sync_func = self.supported_devices.get(device.device_type.upper())
            if not sync_func:
                return False, f"Unsupported device type: {device.device_type}"

            # Sync data
            success = sync_func(device)
            if success:
                device.last_sync = datetime.utcnow()
                self.session.commit()
                return True, "Data synchronized successfully"
            return False, "Failed to sync data"

        except Exception as e:
            return False, f"Error syncing data: {str(e)}"

    def get_recent_metrics(
        self,
        user_id: int,
        metric_type: WearableMetricType,
        days: int = 7
    ) -> List[Dict]:
        """Get recent metrics for a specific user and metric type."""
        start_date = datetime.utcnow() - timedelta(days=days)

        metrics = self.session.query(WearableData)\
            .join(WearableDevice)\
            .filter(
                WearableDevice.user_id == user_id,
                WearableData.metric_type == metric_type.value,
                WearableData.timestamp >= start_date
            )\
            .order_by(WearableData.timestamp.desc())\
            .all()

        return [
            {
                'timestamp': metric.timestamp,
                'value': metric.metric_value,
                'unit': metric.metric_unit,
                'confidence': metric.confidence
            }
            for metric in metrics
        ]

    def get_daily_summary(self, user_id: int) -> Dict:
        """Get daily summary of all metrics for a user."""
        today = datetime.utcnow().date()

        metrics = {}
        for metric_type in WearableMetricType:
            latest = self.session.query(WearableData)\
                .join(WearableDevice)\
                .filter(
                    WearableDevice.user_id == user_id,
                    WearableData.metric_type == metric_type.value,
                    func.date(WearableData.timestamp) == today
                )\
                .order_by(WearableData.timestamp.desc())\
                .first()

            if latest:
                metrics[metric_type.value.lower()] = {
                    'value': latest.metric_value,
                    'unit': latest.metric_unit,
                    'last_updated': latest.timestamp
                }

        return metrics

    def _sync_whoop_data(self, device: WearableDevice) -> bool:
        """Sync data from WHOOP device."""
        try:
            base_url = "https://api.whoop.com/v2"
            headers = {'Authorization': f'Bearer {device.auth_token}'}

            # Get recovery data
            recovery_response = requests.get(f"{base_url}/users/recovery", headers=headers)
            if recovery_response.status_code == 200:
                recovery_data = recovery_response.json()
                self._save_metric(
                    device.id,
                    WearableMetricType.RECOVERY_SCORE,
                    recovery_data['score'],
                    'score',
                    0.95
                )

            # Get strain data
            strain_response = requests.get(f"{base_url}/users/strain", headers=headers)
            if strain_response.status_code == 200:
                strain_data = strain_response.json()
                self._save_metric(
                    device.id,
                    WearableMetricType.DAY_STRAIN,
                    strain_data['score'],
                    'score',
                    0.95
                )

            return True
        except:
            return False

    def _sync_fitbit_data(self, device: WearableDevice) -> bool:
        """Sync data from Fitbit device."""
        try:
            base_url = "https://api.fitbit.com/1/user/-"
            headers = {'Authorization': f'Bearer {device.auth_token}'}
            today = datetime.utcnow().strftime('%Y-%m-%d')

            # Get activity data
            activity_response = requests.get(
                f"{base_url}/activities/date/{today}.json",
                headers=headers
            )
            if activity_response.status_code == 200:
                activity_data = activity_response.json()
                self._save_metric(
                    device.id,
                    WearableMetricType.STEPS,
                    activity_data['summary']['steps'],
                    'steps',
                    1.0
                )
                self._save_metric(
                    device.id,
                    WearableMetricType.ACTIVE_ZONE_MINUTES,
                    activity_data['summary'].get('activeZoneMinutes', 0),
                    'minutes',
                    1.0
                )

            return True
        except:
            return False

    def _sync_apple_watch_data(self, device: WearableDevice) -> bool:
        """Sync data from Apple Watch using HealthKit API."""
        try:
            # Apple Watch integration requires a native iOS app
            # This is a placeholder for future implementation
            return False
        except:
            return False

    def _sync_oura_data(self, device: WearableDevice) -> bool:
        """Sync data from Oura Ring."""
        try:
            base_url = "https://api.ouraring.com/v2"
            headers = {'Authorization': f'Bearer {device.auth_token}'}

            # Get sleep data
            sleep_response = requests.get(f"{base_url}/usercollection/daily_sleep", headers=headers)
            if sleep_response.status_code == 200:
                sleep_data = sleep_response.json()
                if sleep_data['data']:
                    latest_sleep = sleep_data['data'][0]
                    self._save_metric(
                        device.id,
                        WearableMetricType.SLEEP,
                        latest_sleep['duration'],
                        'seconds',
                        0.9
                    )
                    self._save_metric(
                        device.id,
                        WearableMetricType.HRV,
                        latest_sleep['hrv']['average'],
                        'ms',
                        0.9
                    )

            return True
        except:
            return False

    def _save_metric(
        self,
        device_id: int,
        metric_type: WearableMetricType,
        value: float,
        unit: str,
        confidence: float = 1.0
    ) -> None:
        """Save a new metric measurement to the database."""
        metric = WearableData(
            device_id=device_id,
            timestamp=datetime.utcnow(),
            metric_type=metric_type.value,
            metric_value=value,
            metric_unit=unit,
            confidence=confidence
        )
        self.session.add(metric)
        self.session.commit()

    def _validate_garmin_token(self, device: WearableDevice) -> bool:
        """Validate if the current Garmin auth token is still valid."""
        try:
            response = requests.get(
                "https://connect.garmin.com/modern/proxy/userprofile-service/socialProfile",
                headers={'Authorization': f'Bearer {device.auth_token}'}
            )
            return response.status_code == 200
        except:
            return False

    def _refresh_garmin_token(self, device: WearableDevice) -> bool:
        """Refresh Garmin auth token using refresh token."""
        try:
            response = requests.post(
                "https://connect.garmin.com/oauth-service/token",
                data={
                    'refresh_token': device.refresh_token,
                    'grant_type': 'refresh_token'
                }
            )

            if response.status_code == 200:
                token_data = response.json()
                device.auth_token = token_data['access_token']
                if token_data.get('refresh_token'):
                    device.refresh_token = token_data['refresh_token']
                self.session.commit()
                return True
            return False
        except:
            return False
    def _sync_garmin_data(self, device: WearableDevice) -> bool:
        """Sync data from Garmin device."""
        # Implement Garmin Connect API integration
        try:
            # Garmin Connect API endpoints
            base_url = "https://connect.garmin.com/modern"
            endpoints = {
                'heart_rate': "/proxy/wellness-service/wellness/dailyHeartRate",
                'steps': "/proxy/activitylist-service/wellness/dailySteps",
                'sleep': "/proxy/wellness-service/wellness/dailySleepData"
            }

            # Check if we need to refresh token
            if not self._validate_garmin_token(device):
                if not self._refresh_garmin_token(device):
                    return False

            # Headers for Garmin API requests
            headers = {
                'Authorization': f'Bearer {device.auth_token}',
                'Content-Type': 'application/json'
            }

            # Get today's data
            today = datetime.utcnow().date()

            # Sync heart rate data
            hr_response = requests.get(
                f"{base_url}{endpoints['heart_rate']}/{today}",
                headers=headers
            )
            if hr_response.status_code == 200:
                hr_data = hr_response.json()
                self._save_metric(
                    device.id,
                    WearableMetricType.HEART_RATE,
                    hr_data['value'],
                    'bpm',
                    hr_data.get('confidence', 0.9)
                )

            # Sync steps data
            steps_response = requests.get(
                f"{base_url}{endpoints['steps']}/{today}",
                headers=headers
            )
            if steps_response.status_code == 200:
                steps_data = steps_response.json()
                self._save_metric(
                    device.id,
                    WearableMetricType.STEPS,
                    steps_data['steps'],
                    'steps',
                    1.0
                )

            # Sync sleep data
            sleep_response = requests.get(
                f"{base_url}{endpoints['sleep']}/{today}",
                headers=headers
            )
            if sleep_response.status_code == 200:
                sleep_data = sleep_response.json()
                self._save_metric(
                    device.id,
                    WearableMetricType.SLEEP,
                    sleep_data['sleepMinutes'],
                    'minutes',
                    sleep_data.get('confidence', 0.8)
                )

            return True

        except requests.exceptions.RequestException as e:
            print(f"Error syncing Garmin data: {str(e)}")
            return False