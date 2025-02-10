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
            'GARMIN': self._sync_garmin_data
        }

    def register_device(
        self,
        user_id: int,
        device_type: str,
        device_id: str,
        auth_token: str,
        refresh_token: Optional[str] = None
    ) -> WearableDevice:
        """Register a new wearable device for a user."""
        device = WearableDevice(
            user_id=user_id,
            device_type=device_type.upper(),
            device_id=device_id,
            auth_token=auth_token,
            refresh_token=refresh_token,
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
        # TODO: Implement WHOOP API integration
        return True

    def _sync_fitbit_data(self, device: WearableDevice) -> bool:
        """Sync data from Fitbit device."""
        # TODO: Implement Fitbit API integration
        return True

    def _sync_garmin_data(self, device: WearableDevice) -> bool:
        """Sync data from Garmin device."""
        # TODO: Implement Garmin API integration
        return True
