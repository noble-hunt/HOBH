import streamlit as st
import pandas as pd
from utils.data_manager import DataManager
from utils.openai_helper import WorkoutGenerator
from utils.visualization import create_progress_chart
import plotly.express as px

st.set_page_config(page_title="Olympic Weightlifting Tracker", layout="wide")

# Load custom CSS
with open('assets/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize data manager
data_manager = DataManager()

def main():
    st.title("🏋️‍♂️ Olympic Weightlifting Tracker")

    # Sidebar for navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Home", "Log Movement", "Generate Workout", "Progress Tracker"]
    )

    if page == "Home":
        show_home()
    elif page == "Log Movement":
        show_log_movement()
    elif page == "Generate Workout":
        show_workout_generator()
    elif page == "Progress Tracker":
        show_progress_tracker()

def show_home():
    st.header("Welcome to Your Weightlifting Journey")

    # Display PRs and Difficulty Levels
    st.subheader("Movement Status")

    col1, col2, col3 = st.columns(3)
    movements = data_manager.get_movements()
    prs = data_manager.get_prs()

    for idx, movement in enumerate(movements):
        col = [col1, col2, col3][idx % 3]
        with col:
            difficulty = data_manager.get_movement_difficulty(movement)

            # Create colored box based on difficulty
            difficulty_colors = {
                'BEGINNER': 'lightblue',
                'INTERMEDIATE': 'lightgreen',
                'ADVANCED': 'orange',
                'ELITE': 'red'
            }

            st.markdown(
                f"""
                <div style="padding: 1rem; border-radius: 5px; background-color: {difficulty_colors[difficulty.value]};">
                    <h4>{movement}</h4>
                    <p>PR: {prs.get(movement, 0)} kg</p>
                    <p>Level: {difficulty.value}</p>
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