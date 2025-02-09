import streamlit as st
import pandas as pd
from utils.data_manager import DataManager
from utils.openai_helper import WorkoutGenerator
from utils.visualization import create_progress_chart, create_workout_summary, create_heatmap
from utils.social_manager import SocialManager
from utils.auth_manager import AuthManager
from utils.quote_generator import QuoteGenerator
from utils.avatar_manager import AvatarManager # Added import
import plotly.express as px
from pathlib import Path
from datetime import datetime
from utils.recovery_calculator import RecoveryCalculator  # Add this import

st.set_page_config(page_title="Olympic Weightlifting Tracker", layout="wide")

# Load custom CSS
with open('assets/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize managers
data_manager = DataManager()
social_manager = SocialManager()
auth_manager = AuthManager()
quote_generator = QuoteGenerator()
avatar_manager = AvatarManager() # Added initialization

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'daily_quote' not in st.session_state:
    st.session_state.daily_quote = None
if 'quote_date' not in st.session_state:
    st.session_state.quote_date = None

def login_user():
    st.header("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            user_id, error = auth_manager.authenticate_user(username, password)
            if user_id:
                st.session_state.user_id = user_id
                st.session_state.username = username
                st.success("Successfully logged in!")
                st.rerun()
            else:
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
                st.rerun()
            else:
                st.error(error)

def show_login_page():
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        login_user()

    with tab2:
        signup_user()

def main():
    # Show logout button in sidebar if user is logged in
    if st.session_state.user_id:
        st.sidebar.text(f"Welcome, {st.session_state.username}!")
        if st.sidebar.button("Logout"):
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()

    # Require login for all pages except login page
    if not st.session_state.user_id:
        show_login_page()
        return

    # Create container for logo with custom spacing
    logo_container = st.container()
    with logo_container:
        # Display logo instead of text title
        logo_path = "attached_assets/BlackBack.png"
        if Path(logo_path).exists():
            st.image(logo_path, use_container_width=False, width=250)
        else:
            st.title("🏋️‍♂️ Olympic Weightlifting Tracker")

        # Add minimal spacing after logo
        st.markdown('<div style="margin-bottom: 0.5rem;"></div>', unsafe_allow_html=True)

    # Sidebar for navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Home", "Log Movement", "Generate Workout", "Progress Tracker", "Social Hub", "Achievements", "Profile"]
    )

    if page == "Home":
        show_home()
    elif page == "Log Movement":
        show_log_movement()
    elif page == "Generate Workout":
        show_workout_generator()
    elif page == "Progress Tracker":
        show_progress_tracker()
    elif page == "Social Hub":
        show_social_hub()
    elif page == "Achievements":
        show_achievements()
    elif page == "Profile":
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
                    st.markdown(f"**Movement:** {workout.movement.name}")
                    st.markdown(f"Weight: {workout.weight}kg × {workout.reps} reps")
                    if workout.notes:
                        st.markdown(f"_{workout.notes}_")
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
    st.header("Welcome to Your Weightlifting Journey")

    # Daily Motivation Quote
    if (not st.session_state.daily_quote or 
        not st.session_state.quote_date or 
        st.session_state.quote_date.date() != datetime.now().date()):

        # Get user context for personalization
        user_context = {}
        if st.session_state.user_id:
            recent_logs = data_manager.get_recent_logs(st.session_state.user_id)
            if recent_logs:
                user_context = {
                    'target_movement': recent_logs[0].movement.name if recent_logs else None,
                    'current_streak': len(recent_logs)
                }

        st.session_state.daily_quote = quote_generator.generate_workout_quote(user_context)
        st.session_state.quote_date = datetime.now()

    # Display the quote
    st.markdown(
        f"""
        <div style="padding: 1rem; background-color: #f8f9fa; border-radius: 10px; 
                    margin: 0.5rem 0; text-align: center; border-left: 5px solid #DAA520;">
            <p style="font-size: 1.2rem; font-style: italic; color: #2C3E50; margin: 0;">
                "{st.session_state.daily_quote}"
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Add Recovery and Strain Score Section
    st.subheader("Training Load Status")

    # Initialize recovery calculator
    recovery_calc = RecoveryCalculator()

    # Create two columns for recovery and strain scores
    col1, col2 = st.columns(2)

    with col1:
        # Calculate and display recovery score
        recovery_data = recovery_calc.calculate_recovery_score(
            st.session_state.user_id,
            datetime.now()
        )

        # Create recovery score card
        st.markdown(
            f"""
            <div style="padding: 1rem; background-color: {_get_recovery_color(recovery_data['recovery_score'])}; 
                        border-radius: 10px; margin: 0.5rem 0;">
                <h3 style="margin: 0; color: white;">Recovery Score</h3>
                <h2 style="margin: 0.5rem 0; color: white;">{recovery_data['recovery_score']}/10</h2>
                <p style="margin: 0; color: white;">{recovery_data['message']}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        # Calculate and display strain score
        strain_data = recovery_calc.calculate_strain_score(
            st.session_state.user_id,
            datetime.now()
        )

        # Create strain score card
        st.markdown(
            f"""
            <div style="padding: 1rem; background-color: {_get_strain_color(strain_data['strain_score'])}; 
                        border-radius: 10px; margin: 0.5rem 0;">
                <h3 style="margin: 0; color: white;">Training Strain</h3>
                <h2 style="margin: 0.5rem 0; color: white;">{strain_data['strain_score']}/10</h2>
                <p style="margin: 0; color: white;">{strain_data['message']}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # If there's training data, show the strain components
        if strain_data['strain_score'] > 0:
            with st.expander("View Strain Components"):
                components = strain_data['components']
                st.markdown(f"""
                    - Volume Load: {components['volume']:.1f}/10
                    - Relative Intensity: {components['intensity']:.1f}/10
                    - Training Frequency: {components['frequency']:.1f}/10
                """)

    st.subheader("Movement Status")
    cols = st.columns(4)
    movements = data_manager.get_movements()
    prs = data_manager.get_prs()

    for idx, movement in enumerate(movements):
        col = cols[idx % 4]
        with col:
            difficulty = data_manager.get_movement_difficulty(movement)

            # Create colored box based on difficulty with more subtle gold colors
            difficulty_colors = {
                'BEGINNER': '#FFF8DC',  # Cornsilk
                'INTERMEDIATE': '#FFE4B5',  # Moccasin
                'ADVANCED': '#DEB887',  # Burlywood
                'ELITE': '#DAA520'  # Goldenrod
            }

            st.markdown(
                f"""
                <div class="movement-status-card" style="background-color: {difficulty_colors[difficulty.value]};">
                    <h5 style="margin: 0;">{movement}</h5>
                    <p style="margin: 5px 0;">PR: {prs.get(movement, 0)} kg</p>
                    <p style="margin: 0;">{difficulty.value}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

def show_log_movement():
    st.header("Log Your Lift")

    movements = data_manager.get_movements()

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
            help="This affects your difficulty progression"
        )

        notes = st.text_area("Notes (optional)")

        submitted = st.form_submit_button("Log Movement")

        if submitted:
            try:
                success_value = 1 if completed_successfully == "Successful" else 0
                data_manager.log_movement(movement, weight, reps, date, notes, success_value)

                # Show current difficulty level after logging
                current_difficulty = data_manager.get_movement_difficulty(movement)
                st.success(f"Movement logged successfully! Current difficulty: {current_difficulty.value}")
            except Exception as e:
                st.error(f"Error logging movement: {str(e)}")

def show_workout_generator():
    st.header("Workout Generator")

    movements = data_manager.get_movements()
    selected_movements = st.multiselect(
        "Select movements to focus on",
        movements
    )

    if st.button("Generate Workout"):
        if not selected_movements:
            st.warning("Please select at least one movement.")
            return

        workout_generator = WorkoutGenerator()
        workout = workout_generator.generate_workout(selected_movements)

        st.subheader("Your Custom Workout")
        st.markdown(workout, unsafe_allow_html=True)

def show_progress_tracker():
    st.header("Progress Tracker")

    # Movement selector and date range
    col1, col2 = st.columns([2, 1])

    with col1:
        movement = st.selectbox(
            "Select Movement",
            data_manager.get_movements()
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
            cutoff_date = pd.Timestamp.now() - pd.DateOffset(months=months[date_range])
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
        tab1, tab2, tab3, tab4 = st.tabs([
            "Progress Charts", 
            "Training Summary", 
            "Workout Patterns",
            "Training Insights"
        ])

        with tab1:
            # Create and display progress chart
            fig = create_progress_chart(history, movement)
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
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
            st.dataframe(
                history[['date', 'weight', 'reps', 'difficulty', 'Status', 'notes']]
                .sort_values('date', ascending=False)
                .head(5)
            )

        with tab3:
            # Display workout pattern heatmap
            st.subheader("Workout Patterns")
            heatmap = create_heatmap(history)
            st.plotly_chart(heatmap, use_container_width=True)

        with tab4:
            st.subheader("Training Insights")
            if prediction_data and prediction_data['insights']:
                st.write(prediction_data['insights'])
            else:
                st.info("Continue logging workouts to receive personalized training insights!")

    else:
        st.info("No data available for this movement yet.")

def show_achievements():
    st.header("🏆 Achievements & Badges")

    achievements = data_manager.get_achievements()

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
                        <h5 style="margin: 0;">🏅 {achievement['name']}</h5>
                        <p style="margin: 5px 0;">{achievement['description']}</p>
                        <p style="margin: 0;font-size: 0.8em;">
                            Earned: {achievement['date_earned'].strftime('%Y-%m-%d')}
                            {f"<br>Movement: {achievement['movement_name']}" if achievement['movement_name'] else ""}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.info("No achievements earned yet. Keep training to unlock achievements!")

        # Show available achievements
        st.subheader("Available Achievements")
        with st.expander("See what you can earn"):
            st.markdown("""
            - 🏋️ **Weight Master**: Lift 100kg or more in any movement
            - 📅 **Consistency King**: Log workouts for 7 consecutive days
            - 🎯 **Movement Expert**: Reach ADVANCED level in any movement
            - 👑 **Elite Status**: Reach ELITE level in any movement
            """)

def show_profile():
    st.header("🎯 Athlete Profile")

    if not st.session_state.user_id:
        st.warning("Please log in to customize your profile.")
        return

    # Create tabs for different profile sections
    tab1, tab2 = st.tabs(["Profile Info", "Avatar Customization"])

    with tab1:
        user = auth_manager.get_user(st.session_state.user_id)
        if user:
            st.subheader(f"Welcome, {user['display_name'] or user['username']}!")

            # Basic profile information
            new_display_name = st.text_input("Display Name", value=user['display_name'] or "")
            if st.button("Update Display Name"):
                # Add display name update logic here
                st.success("Display name updated successfully!")

    with tab2:
        st.subheader("Customize Your Avatar")

        # Get current avatar settings
        current_settings = avatar_manager.get_avatar_settings(st.session_state.user_id)
        available_options = avatar_manager.get_available_options()

        # Avatar customization form
        with st.form("avatar_customization"):
            selected_style = st.selectbox(
                "Avatar Style",
                options=available_options['styles'],
                index=0
            )

            selected_background = st.color_picker(
                "Background Color",
                value="#F0F2F6"
            )

            # Feature selection
            st.subheader("Features")
            features = {}
            for feature, options in available_options['features'].items():
                features[feature] = st.selectbox(
                    feature.replace('_', ' ').title(),
                    options=options,
                    index=0
                )

            if st.form_submit_button("Update Avatar"):
                success, message = avatar_manager.update_avatar(
                    st.session_state.user_id,
                    selected_style,
                    selected_background,
                    features
                )
                if success:
                    st.success("Avatar updated successfully!")
                    st.rerun()  # Updated from experimental_rerun to rerun
                else:
                    st.error(message)

        # Display current settings and avatar preview
        if current_settings:
            # Create columns for settings and preview
            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader("Current Settings")
                st.json(current_settings)

            with col2:
                st.subheader("Avatar Preview")
                try:
                    avatar_svg = avatar_manager.generate_avatar_svg(current_settings)
                    if avatar_svg:
                        st.image(avatar_svg, width=200)
                    else:
                        st.warning("Avatar preview not available")
                except Exception as e:
                    st.error(f"Error displaying avatar: {str(e)}")

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