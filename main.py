import streamlit as st
import pandas as pd
from utils.data_manager import DataManager
from utils.openai_helper import WorkoutGenerator
from utils.visualization import create_progress_chart
from utils.social_manager import SocialManager
import plotly.express as px

st.set_page_config(page_title="Olympic Weightlifting Tracker", layout="wide")

# Load custom CSS
with open('assets/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize managers
data_manager = DataManager()
social_manager = SocialManager()

# Session state for user management
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

def main():
    st.title("🏋️‍♂️ Olympic Weightlifting Tracker")

    # User authentication placeholder
    if st.session_state.user_id is None:
        show_login()
    else:
        # Sidebar for navigation
        page = st.sidebar.selectbox(
            "Navigation",
            ["Home", "Log Movement", "Generate Workout", "Progress Tracker", "Social Hub"]
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

def show_login():
    st.header("Welcome! Please Log In or Sign Up")

    with st.form("login_form"):
        username = st.text_input("Username")
        action = st.form_submit_button("Login/Signup")

        if action and username:
            try:
                # Simple login/signup logic (for demo purposes)
                user_id = social_manager.create_profile(username)
                st.session_state.user_id = user_id
                st.success(f"Welcome, {username}!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

def show_social_hub():
    st.header("🤝 Social Hub")

    # Get user profile
    try:
        profile = social_manager.get_user_profile(st.session_state.user_id)

        # Profile section
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Following", profile["following_count"])
        with col2:
            st.metric("Followers", profile["followers_count"])
        with col3:
            st.metric("Shared Workouts", profile["shared_workouts_count"])

        st.markdown("---")

        # Tabs for different social features
        tab1, tab2, tab3 = st.tabs(["Feed", "Share Workout", "Find Athletes"])

        with tab1:
            st.subheader("Recent Activity")
            feed = social_manager.get_user_feed(st.session_state.user_id)

            for shared in feed:
                with st.container():
                    st.markdown(f"**{shared.user.username}** shared a workout:")
                    st.markdown(f"Movement: {shared.workout_log.movement.name}")
                    st.markdown(f"Weight: {shared.workout_log.weight}kg × {shared.workout_log.reps} reps")
                    if shared.caption:
                        st.markdown(f"_{shared.caption}_")
                    st.button(f"❤️ {shared.likes}", key=f"like_{shared.id}")
                    st.markdown("---")

        with tab2:
            st.subheader("Share Your Workout")
            recent_logs = data_manager.get_recent_logs(st.session_state.user_id, limit=5)

            if recent_logs:
                selected_log = st.selectbox(
                    "Select workout to share",
                    recent_logs,
                    format_func=lambda x: f"{x.movement.name} - {x.weight}kg × {x.reps} reps"
                )

                caption = st.text_area("Add a caption")

                if st.button("Share"):
                    try:
                        social_manager.share_workout(
                            st.session_state.user_id,
                            selected_log.id,
                            caption
                        )
                        st.success("Workout shared successfully!")
                    except Exception as e:
                        st.error(f"Error sharing workout: {str(e)}")
            else:
                st.info("Log some workouts first to share them!")

        with tab3:
            st.subheader("Find Athletes to Follow")
            search_term = st.text_input("Search by username")

            if search_term:
                # Implement user search functionality
                st.info("User search feature coming soon!")

    except Exception as e:
        st.error(f"Error loading social features: {str(e)}")

def show_home():
    st.header("Welcome to Your Weightlifting Journey")

    # Display PRs and Difficulty Levels
    st.subheader("Movement Status")

    # Create a more compact layout with 4 columns
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

    movement = st.selectbox(
        "Select Movement",
        data_manager.get_movements()
    )

    # Get movement history
    history = data_manager.get_movement_history(movement)

    if not history.empty:
        # Display current difficulty level
        current_difficulty = data_manager.get_movement_difficulty(movement)
        st.info(f"Current Difficulty Level: {current_difficulty.value}")

        # Create progress chart
        fig = create_progress_chart(history, movement)
        st.plotly_chart(fig)

        # Show recent sessions table
        st.subheader("Recent Sessions")
        history['Status'] = history['completed'].map({1: '✅ Success', 0: '❌ Failed'})
        st.dataframe(
            history[['date', 'weight', 'reps', 'difficulty', 'Status', 'notes']]
            .sort_values('date', ascending=False)
            .head(5)
        )
    else:
        st.info("No data available for this movement yet.")

if __name__ == "__main__":
    main()