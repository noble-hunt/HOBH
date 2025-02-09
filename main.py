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

def main():
    st.title("🏋️‍♂️ Olympic Weightlifting Tracker")

    # Sidebar for navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Home", "Log Movement", "Generate Workout", "Progress Tracker", "Social Hub", "Achievements"]
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

def show_social_hub():
    st.header("🤝 Social Hub")

    # Tabs for different social features
    tab1, tab2 = st.tabs(["Recent Activity", "Share Workout"])

    with tab1:
        st.subheader("Recent Activity")
        st.info("See what others are achieving in their weightlifting journey!")

        try:
            # Show recent activities without user filtering
            workouts = data_manager.get_recent_logs(limit=10)

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
                data_manager.log_movement(movement, weight, reps, pd.Timestamp.now().date(), notes)
                st.success("Workout shared successfully!")
            except Exception as e:
                st.error(f"Error sharing workout: {str(e)}")

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

if __name__ == "__main__":
    main()