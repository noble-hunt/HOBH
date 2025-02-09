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
    
    # Display PRs
    st.subheader("Personal Records")
    prs = data_manager.get_prs()
    
    col1, col2, col3 = st.columns(3)
    movements = data_manager.get_movements()
    
    for idx, movement in enumerate(movements):
        col = [col1, col2, col3][idx % 3]
        with col:
            st.metric(
                label=movement,
                value=f"{prs.get(movement, 0)} kg"
            )

def show_log_movement():
    st.header("Log Your Lift")
    
    movements = data_manager.get_movements()
    
    with st.form("log_movement"):
        movement = st.selectbox("Select Movement", movements)
        weight = st.number_input("Weight (kg)", min_value=0.0, step=0.5)
        reps = st.number_input("Reps", min_value=1, step=1)
        date = st.date_input("Date")
        notes = st.text_area("Notes (optional)")
        
        submitted = st.form_submit_button("Log Movement")
        
        if submitted:
            try:
                data_manager.log_movement(movement, weight, reps, date, notes)
                st.success("Movement logged successfully!")
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
        fig = create_progress_chart(history, movement)
        st.plotly_chart(fig)
    else:
        st.info("No data available for this movement yet.")

if __name__ == "__main__":
    main()
