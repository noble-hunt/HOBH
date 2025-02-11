import streamlit as st
import pandas as pd
from utils.data_manager import DataManager
from utils.openai_helper import WorkoutGenerator
from utils.visualization import create_progress_chart, create_workout_summary, create_heatmap, create_3d_movement_progress
from utils.social_manager import SocialManager
from utils.auth_manager import AuthManager
from utils.quote_generator import QuoteGenerator
from utils.avatar_manager import AvatarManager
import plotly.express as px
from pathlib import Path
from datetime import datetime
from utils.recovery_calculator import RecoveryCalculator
from utils.movement_analyzer import MovementAnalyzer
from utils.wearable_manager import WearableManager, WearableMetricType
import os
import requests
from urllib.parse import urlencode
from utils.wearable_wizard import WearableWizard
from utils.gamification import GamificationManager
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from utils.models import WearableDevice, WorkoutLog, UserProfile # Added import for UserProfile
from utils.export_manager import HealthDataExporter
from utils.recovery_advisor import RecoveryAdvisor # Added import for RecoveryAdvisor
import json # Added import for JSON handling
import zipfile
from io import BytesIO

st.set_page_config(page_title="Olympic Weightlifting Tracker", layout="wide")

# Load custom CSS
with open('assets/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize managers
data_manager = DataManager()
social_manager = SocialManager()
auth_manager = AuthManager()
quote_generator = QuoteGenerator()

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'daily_quote' not in st.session_state:
    st.session_state.daily_quote = None
if 'quote_date' not in st.session_state:
    st.session_state.quote_date = None
if 'show_nav' not in st.session_state:
    st.session_state.show_nav = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"

def toggle_nav():
    """Toggle navigation menu visibility"""
    st.session_state.show_nav = not st.session_state.show_nav

def navigate_to(page):
    """Navigate to a specific page"""
    if page == "Logout":
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.current_page = "Home"
    else:
        st.session_state.current_page = page
    st.session_state.show_nav = False

def login_user():
    st.header("Login")

    # Add debug logging
    print("Debug: Starting login process")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            print(f"Debug: Form submitted for user: {username}")
            user_id, error = auth_manager.authenticate_user(username, password)

            if user_id:
                print(f"Debug: Authentication successful for user_id: {user_id}")
                # Update session state
                st.session_state['user_id'] = user_id
                st.session_state['username'] = username
                # Use st.rerun() to ensure state changes are applied immediately
                st.success("Successfully logged in!")
                st.rerun()
            else:
                print(f"Debug: Authentication failed - {error}")
                st.error(error)

def signup_user():
    st.header("Sign Up")
    with st.form("signup_form"):
        username = st.text_input("Username")
        display_name = st.text_input("Display Name (optional)")
        password = st.text_input("Password", type="password")
        password_confirm = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Sign Up")

        if submitted:
            if password != password_confirm:
                st.error("Passwords do not match!")
                return

            if len(password) < 6:
                st.error("Password must be at least 6 characters long!")
                return

            user_id, error = auth_manager.create_user(username, password, display_name)
            if user_id:
                st.session_state.user_id = user_id
                st.session_state.username = username
                st.success("Account created successfully!")
            else:
                st.error(error)

def show_login_page():
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        login_user()

    with tab2:
        signup_user()

def main():
    if not st.session_state.user_id:
        show_login_page()
        return

    # Navigation button with Streamlit native components
    st.button("☰", key="nav_toggle", on_click=toggle_nav, help="Toggle navigation menu")

    # Navigation menu using Streamlit's native sidebar
    if st.session_state.show_nav:
        with st.sidebar:
            st.button("🏠 Home", on_click=navigate_to, args=("Home",), use_container_width=True)
            st.button("📝 Log Movement", on_click=navigate_to, args=("Log Movement",), use_container_width=True)
            st.button("🎯 Generate Workout", on_click=navigate_to, args=("Generate Workout",), use_container_width=True)
            st.button("📊 Progress Tracker", on_click=navigate_to, args=("Progress Tracker",), use_container_width=True)
            st.button("🤝 Social Hub", on_click=navigate_to, args=("Social Hub",), use_container_width=True)
            st.button("🏆 Achievements", on_click=navigate_to, args=("Achievements",), use_container_width=True)
            st.button("👤 Profile", on_click=navigate_to, args=("Profile",), use_container_width=True)
            st.button("🚪 Logout", on_click=navigate_to, args=("Logout",), use_container_width=True)

    # Handle page display based on current_page
    if st.session_state.current_page == "Home":
        show_home()
    elif st.session_state.current_page == "Log Movement":
        show_log_movement()
    elif st.session_state.current_page == "Generate Workout":
        show_workout_generator()
    elif st.session_state.current_page == "Progress Tracker":
        show_progress_tracker()
    elif st.session_state.current_page == "Social Hub":
        show_social_hub()
    elif st.session_state.current_page == "Achievements":
        show_achievements()
    elif st.session_state.current_page == "Profile":
        show_profile()


def show_social_hub():
    st.header("🤝 Social Hub")

    # Tabs for different social features
    tab1, tab2 = st.tabs(["Recent Activity", "Share Workout"])

    with tab1:
        st.subheader("Recent Activity")
        st.info("See what others are achieving in their weightlifting journey!")

        try:
            # Show recent activities without user filtering
            workouts = data_manager.get_recent_logs(st.session_state.user_id, limit=10)

            for workout in workouts:
                with st.container():
                    st.markdown(f"**Movement:** {workout['movement']['name']}")
                    st.markdown(f"Weight: {workout['weight']}kg × {workout['reps']} reps")
                    if workout['notes']:
                        st.markdown(f"_{workout['notes']}_")
                    st.markdown("---")

        except Exception as e:
            st.error(f"Error loading recent activities: {str(e)}")

    with tab2:
        st.subheader("Share Your Achievement")
        movement = st.selectbox("Select Movement", data_manager.get_movements())
        weight = st.number_input("Weight (kg)", min_value=0.0, step=0.5)
        reps = st.number_input("Reps", min_value=1, step=1)
        notes = st.text_area("Add a note")

        if st.button("Share"):
            try:
                # Add user_id parameter and fix the parameter order
                data_manager.log_movement(
                    user_id=st.session_state.user_id,
                    movement=movement,
                    weight=weight,
                    reps=reps,
                    date=datetime.now().date(),
                    notes=notes
                )
                st.success("Workout shared successfully!")
            except Exception as e:
                st.error(f"Error sharing workout: {str(e)}")

def show_home():
    """Display the home page with animated welcome screen"""

    # Welcome Container with animated logo
    welcome_container = st.container()
    with welcome_container:
        st.markdown('<div class="welcome-container">', unsafe_allow_html=True)

        # Animated logo
        if Path("attached_assets/yHOBH.png").exists():
            st.markdown(
                f'<div class="welcome-logo">',
                unsafe_allow_html=True
            )
            st.image("attached_assets/yHOBH.png", use_container_width=False, width=250)
            st.markdown('</div>', unsafe_allow_html=True)

        # Welcome message
        st.markdown(
            f'<h1 class="welcome-header">Welcome to Your Fitness Journey</h1>',
            unsafe_allow_html=True
        )

        # Get user's fitness data
        try:
            recent_logs = data_manager.get_recent_logs(st.session_state.user_id)
            total_workouts = len(recent_logs)
            unique_movements = len(set(log['movement']['name'] for log in recent_logs if log.get('movement')))

            # Create metrics grid
            cols = st.columns(4)

            metrics = [
                {"label": "Total Workouts", "value": total_workouts, "icon": "🏋️‍♂️"},
                {"label": "Movements Mastered", "value": unique_movements, "icon": "🎯"},
                {"label": "Active Streak", "value": data_manager.get_workout_streak(st.session_state.user_id), "icon": "🔥"},
                {"label": "PR's Set", "value": len(data_manager.get_prs()), "icon": "🏆"}
            ]

            for idx, metric in enumerate(metrics):
                with cols[idx]:
                    st.markdown(
                        f"""
                        <div class="journey-metric">
                            <h3>{metric['icon']}</h3>
                            <h2>{metric['value']}</h2>
                            <p>{metric['label']}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            # Recent Achievements
            st.markdown('<h2 class="welcome-header">Recent Achievements</h2>', unsafe_allow_html=True)
            achievements = data_manager.get_achievements()[:3]  # Get last 3 achievements

            if achievements:
                for achievement in achievements:
                    st.markdown(
                        f"""
                        <div class="achievement-card">
                            <h4>🏅 {achievement['name']}</h4>
                            <p>{achievement['description']}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.info("Complete your first workout to start earning achievements!")

        except Exception as e:
            st.error(f"Error loading fitness data: {str(e)}")

        st.markdown('</div>', unsafe_allow_html=True)

        # Daily Motivation Quote
        if (not st.session_state.daily_quote or 
            not st.session_state.quote_date or 
            st.session_state.quote_date.date() != datetime.now().date()):

            user_context = {}
            if st.session_state.user_id:
                try:
                    recent_logs = data_manager.get_recent_logs(st.session_state.user_id)
                    if recent_logs and len(recent_logs) > 0 and recent_logs[0].get('movement'):
                        user_context = {
                            'target_movement': recent_logs[0]['movement']['name'],
                            'current_streak': len(recent_logs)
                        }
                except Exception as e:
                    st.error(f"Error loading recent activity: {str(e)}")
                    user_context = {}

            st.session_state.daily_quote = quote_generator.generate_workout_quote(user_context)
            st.session_state.quote_date = datetime.now()

        # Display the quote with animation
        st.markdown(
            f"""
            <div class="quote-container" style="animation: fadeIn 1s ease-out 2s both;">
                <p class="quote-text">"{st.session_state.daily_quote}"</p>
            </div>
            """,
            unsafe_allow_html=True
        )

def show_log_movement():
    st.header("Log Your Lift")

    tab1, tab2 = st.tabs(["Log Movement", "Form Analysis"])

    with tab1:
        movements = data_manager.get_all_movements()

        with st.form("log_movement"):
            movement = st.selectbox("Select Movement", movements)
            weight = st.number_input("Weight (kg)", min_value=0.0, step=0.5)
            reps = st.number_input("Reps", min_value=1, step=1)
            date = st.date_input("Date")

            # Add success/failure toggle
            completed_successfully = st.radio(
                "How was the session?",
                ["Successful", "Failed"],
                index=0,
                help="This affects your difficulty progression and XP rewards"
            )

            notes = st.text_area("Notes (optional)")

            submitted = st.form_submit_button("Log Movement")

            if submitted:
                try:
                    success_value = 1 if completed_successfully == "Successful" else 0
                    success = data_manager.log_movement(
                        user_id=st.session_state.user_id,
                        movement=movement,
                        weight=weight,
                        reps=reps,
                        date=date,
                        notes=notes,
                        completed_successfully=success_value
                    )

                    if success:
                        # Get the latest workout log for the user
                        try:
                            # Create database engine and session
                            engine = create_engine(os.environ['DATABASE_URL'])
                            with Session(engine) as session:
                                # Get the actual WorkoutLog object from the database
                                workout_log = session.query(WorkoutLog)\
                                    .filter_by(user_id=st.session_state.user_id)\
                                    .order_by(WorkoutLog.date.desc())\
                                    .first()

                                if workout_log:
                                    # Process gamification with the actual WorkoutLog object
                                    gamification_mgr = GamificationManager(session)
                                    progress = gamification_mgr.process_workout(workout_log)

                                    # Show XP gained with animation
                                    st.balloons()
                                    st.success(f"Movement logged successfully! +{progress.xp_gained} XP")

                                    # Show level up notification if applicable
                                    if progress.new_level:
                                        st.success(f"🎉 Level Up! You reached level {progress.new_level.level}: {progress.new_level.title}")
                                        for reward in progress.new_level.rewards:
                                            st.info(f"🎁 Reward Unlocked: {reward}")

                                    # Show achievement notifications
                                    if progress.achievements_earned:
                                        for achievement in progress.achievements_earned:
                                            st.success(f"🏆 Achievement Unlocked: {achievement}")

                                    # Show current difficulty level after logging
                                    current_difficulty = data_manager.get_movement_difficulty(movement)
                                    st.info(f"Current Difficulty: {current_difficulty.value}")
                                else:
                                    st.error("Error retrieving the logged workout.")
                        except Exception as e:
                            st.error(f"Error processing workout achievements: {str(e)}")

                except Exception as e:
                    st.error(f"Error logging movement: {str(e)}")

    with tab2:
        st.subheader("Movement Form Analysis")
        col1, col2 = st.columns([3, 1])

        with col1:
            # Movement selection for analysis
            selected_movement = st.selectbox(
                "Select movement to analyze",
                ["Clean", "Snatch"],  # Only show movements with defined criteria
                key="analysis_movement"
            )

            # Initialize movement analyzer
            analyzer = MovementAnalyzer()

            # Input source selection
            input_source = st.radio(
                "Select input source",
                ["Camera", "Upload Video"],
                horizontal=True
            )

            # Video upload section
            video_file = None
            if input_source == "Upload Video":
                video_file = st.file_uploader(
                    "Upload your movement video",
                    type=["mp4", "mov", "avi"],
                    help="Upload a video of your movement for analysis. Supported formats: MP4, MOV, AVI"
                )

            # Add help text
            st.markdown("""
            ### How to use:
            1. Select your movement type
            2. Choose input source (camera or video upload)
            3. If using camera: Position yourself so your full body is visible
            4. If uploading video: Select a clear video of your movement
            5. Press 'Start Analysis' to begin
            6. Follow the real-time feedback and suggestions

            The analyzer will provide:
            - Real-time form feedback
            - Joint angle measurements
            - Movement phase detection
            - Form score and suggestions
            """)

        with col2:
            # Start analysis button with clear visual prominence
            start_button_disabled = input_source == "Upload Video" and video_file is None

            if st.button(
                "Start Analysis",
                key="start_analysis",
                use_container_width=True,  # Updated from use_column_width
                disabled=start_button_disabled
            ):
                try:
                    if input_source == "Upload Video" and video_file is not None:
                        video_bytes = video_file.read()
                        analyzer.start_analysis(
                            selected_movement,
                            input_source="video",
                            video_file=video_bytes
                        )
                    else:
                        analyzer.start_analysis(
                            selected_movement,
                            input_source="camera"
                        )
                except Exception as e:
                    st.error(f"Error starting analysis: {str(e)}")
                    if input_source == "Camera":
                        st.info("Please ensure your camera is connected and accessible.")
                    else:
                        st.info("Please ensure your video file is valid and try again.")

def show_workout_generator():
    st.header("Workout Generator")

    movements = data_manager.get_all_movements()
    selected_movements = st.multiselect(
        "Select movements to focus on",
        movements
    )

    # Add intensity focus toggle
    intensity_focus = st.toggle(
        "HIIT/CrossFit Style",
        help="Enable to generate a high-intensity interval training workout with CrossFit elements"
    )

    if st.button("Generate Workout"):
        if not selected_movements:
            st.warning("Please select at least one movement.")
            return

        workout_generator = WorkoutGenerator()
        workout = workout_generator.generate_workout(
            selected_movements,
            intensity_focus=intensity_focus
        )

        st.subheader("Your Custom Workout")
        st.markdown(workout, unsafe_allow_html=True)

def show_progress_tracker():
    st.header("Progress Tracker")

    # Movement selector and date range
    col1, col2 = st.columns([2, 1])

    with col1:
        movement = st.selectbox(
            "Select Movement",
            data_manager.get_all_movements()
        )

    with col2:
        date_range = st.radio(
            "Time Range",
            ["1 Month", "3 Months", "6 Months", "1 Year", "All Time"],
            horizontal=True
        )

    # Get movement history
    history = data_manager.get_movement_history(movement)

    if not history.empty:
        # Filter data based on date range
        if date_range != "All Time":
            months = {
                "1 Month": 1,
                "3 Months": 3,
                "6 Months": 6,
                "1 Year": 12
            }
            # Convert cutoff_date to pandas Timestamp
            cutoff_date = pd.Timestamp.now() - pd.DateOffset(months=months[date_range])
            # Ensure history['date'] is in datetime format
            history['date'] = pd.to_datetime(history['date'])
            history = history[history['date'] >= cutoff_date]

        # Get predictions and insights
        prediction_data = data_manager.get_movement_predictions(movement)

        # Create columns for current stats and predictions
        col1, col2 = st.columns(2)

        with col1:
            # Display current difficulty level
            current_difficulty = data_manager.get_movement_difficulty(movement)
            st.info(f"Current Difficulty Level: {current_difficulty.value}")

        with col2:
            if prediction_data and prediction_data['predictions']:
                pred = prediction_data['predictions']
                if pred['prediction'] and pred['prediction'] > pred['current_pr']:
                    st.success(pred['message'])
                else:
                    st.info(pred['message'])

        # Create tabs for different visualizations
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Progress Charts", 
            "3D Visualization",
            "Training Summary", 
            "Workout Patterns",
            "Training Insights"
        ])

        with tab1:
            # Create and display progress chart
            fig = create_progress_chart(history, movement)
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            # 3D Movement Progress
            st.subheader("3D Progress Visualization")
            fig_3d = create_3d_movement_progress(history, movement)
            st.plotly_chart(fig_3d, use_container_width=True)

            # Add explanation of the visualization
            st.markdown("""
            This 3D visualization shows your progress across three dimensions:
            - Date (X-axis)
            - Weight (Y-axis)
            - Volume (Z-axis)

            The color intensity represents the relative intensity of each workout.
            You can rotate and zoom the visualization to explore your progress from different angles.
            """)

        with tab3:
            # Display workout summary statistics
            summary = create_workout_summary(history)

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Workouts", summary['total_workouts'])
            with col2:
                st.metric("Success Rate", f"{summary['success_rate']:.1f}%")
            with col3:
                st.metric("Max Weight", f"{summary['max_weight']}kg")
            with col4:
                st.metric("Total Volume", f"{summary['total_volume']:.0f}")

            # Show recent sessions table
            st.subheader("Recent Sessions")
            history['Status'] = history['completed'].map({1: '✅ Success', 0: '❌ Failed'})
            display_df = history[['date', 'weight', 'reps', 'difficulty', 'Status', 'notes']].copy()
            display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')  # Format dates for display
            st.dataframe(
                display_df.sort_values('date', ascending=False).head(5)
            )

        with tab4:
            # Display workout pattern heatmap
            st.subheader("Workout Patterns")
            heatmap = create_heatmap(history)
            st.plotly_chart(heatmap, use_container_width=True)

            st.markdown("""
            The heatmap shows your workout intensity patterns throughout the week:
            - Darker colors indicate higher intensity workouts
            - Lighter colors indicate lower intensity workouts
            - White spaces indicate no workouts during those times
            """)

        with tab5:
            st.subheader("Training Insights")
            if prediction_data and prediction_data['insights']:
                st.write(prediction_data['insights'])
            else:
                st.info("Continue logging workouts to receive personalized training insights!")

    else:
        st.info("No data available for this movement yet.")

def show_achievements():
    st.header("🏆 Achievements & Progress")

    # Initialize gamification manager for progress tracking
    engine = create_engine(os.environ['DATABASE_URL'])
    with Session(engine) as session:
        gamification_mgr = GamificationManager(session)
        progress = gamification_mgr.get_user_progress(st.session_state.user_id)

        # Create level progress display
        col1, col2 = st.columns([2, 1])
        with col1:
            current_level = progress['current_level']
            st.markdown(f"""
                <div style='padding: 1rem; background-color: #f0f2f6; border-radius: 10px;'>
                    <h3 style='margin: 0;'>{current_level.title}</h3>
                    <p style='margin: 0;'>Level {current_level.level}</p>
                    <div style='margin: 10px 0;'>
                        <div style='
                            background-color: #e1e4e8;
                            border-radius: 5px;
                            height: 20px;
                        '>
                            <div style='
                                width: {progress['progress_to_next']}%;
                                background-color: #4CAF50;
                                height: 100%;
                                border-radius: 5px;
                                transition: width 0.5s ease-in-out;
                            '></div>
                        </div>
                    </div>
                    <p style='margin: 0;'>Total XP: {progress['total_xp']:,}</p>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            if progress['next_level']:
                st.markdown(f"""
                    <div style='padding: 1rem; background-color: #f0f2f6; border-radius: 10px;'>
                        <h4 style='margin: 0;'>Next Level</h4>
                        <p style='margin: 0;'>{progress['next_level'].title}</p>
                        <p style='margin: 0;'>{progress['progress_to_next']}% Complete</p>
                    </div>
                """, unsafe_allow_html=True)

    # Get achievements
    achievements = data_manager.get_achievements()
    st.subheader("🎖️ Earned Achievements")

    if achievements:
        # Create a grid layout for achievements
        cols = st.columns(3)

        for idx, achievement in enumerate(achievements):
            col = cols[idx % 3]
            with col:
                # Create achievement card
                st.markdown(
                    f"""
                    <div class="movement-status-card" style="background-color: #FFD700;">
                        <h5 style="margin:0;">🏅 {achievement['name']}</h5>
                        <p style="margin: 5px 0;">{achievement['description']}</p>
                        <p style="margin: 0;font-size: 0.8em;">
                            Earned: {achievement['date_earned'].strftime('%Y-%m-%d')}
                            {f"<br>Movement: {achievement['movementname']}" if achievement['movement_name'] else ""}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.info("No achievements earned yet. Keep training to unlock achievements!")

    # Show available achievements
    st.subheader("🎯 Available Achievements")
    st.markdown("""
        Keep training to unlock these achievements:
        - 🏋️ **Weight Master**: Lift 100kg or more in any movement
        - 📅 **Consistency King**: Log workouts for 7 consecutive days
        - 🎯 **Movement Expert**: Reach ADVANCED level in any movement
        - 👑 **Elite Status**: Reach ELITE level in any movement
    """)

def show_profile():
    st.header("👤 Profile Settings")

    # Create database engine and session
    engine = create_engine(os.environ['DATABASE_URL'])
    with Session(engine) as session:
        try:
            # Initialize recovery advisor
            recovery_advisor = RecoveryAdvisor(session)

            # Get personalized recommendations
            recommendations = recovery_advisor.get_recovery_recommendations(
                st.session_state.user_id
            )

            if 'error' in recommendations:
                st.warning(recommendations['fallback_message'])
            else:
                # Parse the recommendations JSON string
                rec_data = json.loads(recommendations['recommendations'])

                # Create expandable sections for each recommendation type
                with st.expander("🎯 Recovery Activities", expanded=True):
                    st.write(rec_data['Recovery Activities'])

                with st.expander("🥗 Nutrition Recommendations"):
                    st.write(rec_data['Nutrition'])

                with st.expander("😴 Rest & Sleep"):
                    st.write(rec_data['Rest'])

                with st.expander("📋 Next Training Session"):
                    st.write(rec_data['Next Training'])

                with st.expander("⚠️ Warning Signs"):
                    st.write(rec_data['Warning Signs'])

                # Add timestamp
                st.caption(
                    f"Last updated: {datetime.fromisoformat(recommendations['generated_at']).strftime('%Y-%m-%d %H:%M')}"
                )

            st.markdown("---")  # Add separator before next section

            # Profile Information Section
            st.subheader("Profile Information")
            try:
                # Initialize managers with session
                avatar_manager = AvatarManager(session)

                # Get user profile info
                user_profile = session.query(UserProfile).filter_by(id=st.session_state.user_id).first()
                if user_profile:
                    # Display basic info
                    st.write(f"Username: {user_profile.username}")
                    if user_profile.bio:
                        st.write(f"Bio: {user_profile.bio}")

                    # Profile Stats
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Workouts", len(user_profile.workout_logs))
                        st.metric("Active Days", user_profile.active_days or 0)
                    with col2:
                        st.metric("Average Recovery", f"{user_profile.avg_recovery or 0:.1f}")
                        st.metric("Current Streak", f"{user_profile.current_streak or 0} days")

                    # Avatar Customization
                    st.subheader("🎨 Avatar Customization")

                    # Get current avatar settings
                    current_settings = avatar_manager.get_avatar_settings(st.session_state.user_id)

                    # Get available options
                    options = avatar_manager.get_available_options()

                    # Create customization form
                    with st.form("avatar_customization"):
                        # Style selection
                        selected_style = st.selectbox(
                            "Avatar Style",
                            options['styles'],
                            index=options['styles'].index(current_settings['style']) if current_settings else 0
                        )

                        # Background color
                        background_color = st.color_picker(
                            "Background Color",
                            current_settings['background'] if current_settings else '#F0F2F6'
                        )

                        # Features customization
                        st.subheader("Features")
                        features = {}

                        col1, col2 = st.columns(2)
                        with col1:
                            features['skin_color'] = st.selectbox(
                                "Skin Color",
                                options['features']['skin_color'],
                                index=options['features']['skin_color'].index(
                                    current_settings['features'].get('skin_color', 'light')
                                ) if current_settings and 'features' in current_settings else 0
                            )

                            features['hair_color'] = st.selectbox(
                                "Hair Color",
                                options['features']['hair_color']
                            )

                            features['hair_style'] = st.selectbox(
                                "Hair Style",
                                options['features']['hair_style']
                            )

                        with col2:
                            features['facial_hair'] = st.selectbox(
                                "Facial Hair",
                                options['features']['facial_hair']
                            )

                            features['accessories'] = st.selectbox(
                                "Accessories",
                                options['features']['accessories']
                            )

                        # Submit button
                        submitted = st.form_submit_button("Update Avatar")

                        if submitted:
                            success, message = avatar_manager.update_avatar(
                                st.session_state.user_id,
                                selected_style,
                                background_color,
                                features
                            )
                            if success:
                                st.success(message)
                            else:
                                st.error(message)

            except Exception as e:
                                st.error(f"Error loading profile information: {str(e)}")

            # Wearable Device Integration
            st.subheader("🔌 Connected Devices")
            try:
                # Initialize wearable manager with session
                wearable_manager = WearableManager(session)

                # Get connected devices
                connected_devices = wearable_manager.get_connected_devices(st.session_state.user_id)

                if connected_devices:
                    for device in connected_devices:
                        with st.expander(f"{device.name} ({device.type})"):
                            st.write(f"Status: {device.status}")
                            st.write(f"Last Sync: {device.last_sync}")

                            # Add disconnect button
                            if st.button(f"Disconnect {device.name}", key=f"disconnect_{device.id}"):
                                try:
                                    wearable_manager.disconnect_device(device.id)
                                    st.success(f"Successfully disconnected {device.name}")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error disconnecting device: {str(e)}")
                else:
                    st.info("No devices connected")

                    # Add device connection wizard
                    if st.button("Connect a Device"):
                        try:
                            wizard = WearableWizard(session)
                            wizard.start_connection_flow()
                        except Exception as e:
                            st.error(f"Error starting device connection: {str(e)}")

            except Exception as e:
                st.error(f"Error loading connected devices: {str(e)}")

            # Data Export Section
            st.subheader("📊 Export Data")
            try:
                # Initialize export manager with session
                export_manager = HealthDataExporter(session)

                # Select data to export
                export_options = st.multiselect(
                    "Select data to export",
                    ["Workouts", "Recovery Scores", "Device Metrics", "Achievements"],
                    key="export_data"
                )

                if export_options:
                    if st.button("Export Selected Data"):
                        try:
                            exported_data = export_manager.export_health_data(
                                user_id=st.session_state.user_id,
                                data_types=export_options
                            )
                            st.download_button(
                                "Download Export",
                                exported_data,
                                exported_data,
                                file_name="health_data_export.json",
                                mime="application/json"
                            )
                        except Exception as e:
                            st.error(f"Error exporting data: {str(e)}")

            except Exception as e:
                st.error(f"Error initializing data export: {str(e)}")

        except Exception as e:
            st.error(f"Error loading profile settings: {str(e)}")

def _get_recovery_color(score):
    """Get background color for recovery score card."""
    if score <= 3:
        return "#dc3545"  # Red
    elif score <= 6:
        return "#ffc107"  # Yellow
    elif score <= 8:
        return "#28a745"  # Green
    else:
        return "#20c997"  # Teal

def _get_strain_color(score):
    """Get background color for strain score card."""
    if score <= 3:
        return "#20c997"  # Teal
    elif score <= 6:
        return "#28a745"  # Green
    elif score <= 8:
        return "#ffc107"  # Yellow
    else:
        return "#dc3545"  # Red

if __name__ == "__main__":
    main()