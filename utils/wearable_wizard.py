"""Wizard for guiding users through wearable device connection process."""
from dataclasses import dataclass
from typing import Dict, List, Optional
import streamlit as st
from enum import Enum

class WearableType(str, Enum):
    """Supported wearable device types."""
    APPLE_WATCH = "APPLE_WATCH"
    FITBIT = "FITBIT"
    WHOOP = "WHOOP"
    OURA = "OURA"
    GARMIN = "GARMIN"

@dataclass
class DeviceInfo:
    """Information about a wearable device type."""
    name: str
    description: str
    setup_steps: List[str]
    features: List[str]
    icon: str
    status: str = "pending"  # pending, connecting, connected, error

class WearableWizard:
    """Guide users through wearable device connection process."""

    def __init__(self):
        self.devices: Dict[WearableType, DeviceInfo] = {
            WearableType.APPLE_WATCH: DeviceInfo(
                name="Apple Watch",
                description="Track your workouts with deep Apple Health integration",
                setup_steps=[
                    "Install our companion iOS app (coming soon)",
                    "Enable Health data sharing",
                    "Select metrics to sync"
                ],
                features=[
                    "Real-time heart rate monitoring",
                    "Workout detection",
                    "Stand hours tracking",
                    "Activity rings integration"
                ],
                icon="⌚"
            ),
            WearableType.FITBIT: DeviceInfo(
                name="Fitbit",
                description="Connect your Fitbit device for comprehensive activity tracking",
                setup_steps=[
                    "Sign in to your Fitbit account",
                    "Authorize data access",
                    "Select data to sync"
                ],
                features=[
                    "Steps and distance",
                    "Heart rate zones",
                    "Sleep tracking",
                    "Activity minutes"
                ],
                icon="📈"
            ),
            WearableType.WHOOP: DeviceInfo(
                name="WHOOP",
                description="Get detailed recovery and strain insights",
                setup_steps=[
                    "Log in to WHOOP",
                    "Grant API access",
                    "Configure sync settings"
                ],
                features=[
                    "Recovery scoring",
                    "Strain tracking",
                    "Sleep performance",
                    "Respiratory rate"
                ],
                icon="🔄"
            ),
            WearableType.OURA: DeviceInfo(
                name="Oura Ring",
                description="Track your readiness and recovery with Oura",
                setup_steps=[
                    "Connect to Oura account",
                    "Allow data access",
                    "Choose metrics to import"
                ],
                features=[
                    "Sleep quality analysis",
                    "Readiness score",
                    "Body temperature",
                    "HRV tracking"
                ],
                icon="💍"
            ),
            WearableType.GARMIN: DeviceInfo(
                name="Garmin",
                description="Sync your Garmin device data",
                setup_steps=[
                    "Sign in to Garmin Connect",
                    "Authorize application",
                    "Select sync preferences"
                ],
                features=[
                    "Activity tracking",
                    "Heart rate monitoring",
                    "Sleep analysis",
                    "Stress tracking"
                ],
                icon="⌚"
            )
        }

    def render_device_selection(self) -> Optional[WearableType]:
        """Render the device selection step."""
        st.subheader("Select Your Device")
        
        cols = st.columns(len(self.devices))
        selected_device = None
        
        for idx, (device_type, info) in enumerate(self.devices.items()):
            with cols[idx]:
                st.markdown(
                    f"""
                    <div style='text-align: center; padding: 1rem; 
                             border: 1px solid #ddd; border-radius: 10px;
                             background-color: white; height: 200px;'>
                        <h1 style='font-size: 2rem; margin-bottom: 0.5rem;'>{info.icon}</h1>
                        <h3 style='margin: 0.5rem 0;'>{info.name}</h3>
                        <p style='font-size: 0.8rem; color: #666;'>{info.description}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if st.button(f"Connect {info.name}", key=f"connect_{device_type}"):
                    selected_device = device_type
                    
        return selected_device

    def render_device_setup(self, device_type: WearableType) -> bool:
        """Render the device setup steps."""
        device = self.devices[device_type]
        
        st.subheader(f"Connect Your {device.name}")
        
        # Create two columns for setup steps and features
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown("### Setup Steps")
            for idx, step in enumerate(device.setup_steps, 1):
                st.markdown(f"{idx}. {step}")
                
            # Add visual progress indicator
            if device_type in [WearableType.FITBIT, WearableType.WHOOP, 
                             WearableType.OURA, WearableType.GARMIN]:
                st.info("⏳ Waiting for API approval...")
            elif device_type == WearableType.APPLE_WATCH:
                st.warning("🔜 iOS app coming soon!")
                
        with col2:
            st.markdown("### Features")
            for feature in device.features:
                st.markdown(f"✓ {feature}")
                
        # Store device preference
        if st.button("Save Preferences"):
            if "wearable_preferences" not in st.session_state:
                st.session_state.wearable_preferences = {}
            st.session_state.wearable_preferences[device_type] = True
            st.success(f"Your {device.name} preferences have been saved!")
            return True
            
        return False

    def render_wizard(self):
        """Render the complete wearable connection wizard."""
        st.title("Connect Your Wearable Device")
        
        # Initialize wizard state
        if "wizard_step" not in st.session_state:
            st.session_state.wizard_step = "select_device"
            st.session_state.selected_device = None
            
        # Device selection step
        if st.session_state.wizard_step == "select_device":
            selected = self.render_device_selection()
            if selected:
                st.session_state.selected_device = selected
                st.session_state.wizard_step = "device_setup"
                st.experimental_rerun()
                
        # Device setup step
        elif st.session_state.wizard_step == "device_setup":
            if self.render_device_setup(st.session_state.selected_device):
                st.session_state.wizard_step = "select_device"
                st.session_state.selected_device = None
                st.experimental_rerun()
            
            # Add back button
            if st.button("← Back to Device Selection"):
                st.session_state.wizard_step = "select_device"
                st.session_state.selected_device = None
                st.experimental_rerun()
