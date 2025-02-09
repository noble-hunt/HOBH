import streamlit as st
import pandas as pd
from utils.data_manager import DataManager
from utils.openai_helper import WorkoutGenerator
from utils.visualization import create_progress_chart, create_workout_summary, create_heatmap
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

if __name__ == "__main__":
    main()