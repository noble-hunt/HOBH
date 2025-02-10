import os
import json
from openai import OpenAI

class WorkoutGenerator:
    def __init__(self):
        self.model = "gpt-3.5-turbo"  # Using GPT-3.5-turbo which is available on free tier
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def generate_workout(self, movements, intensity_focus=False):
        prompt = self._create_prompt(movements, intensity_focus)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Olympic weightlifting and CrossFit coach."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"}
            )

            # Parse the response content as JSON
            try:
                workout_data = json.loads(response.choices[0].message.content)
                return self._format_workout(workout_data, intensity_focus)
            except json.JSONDecodeError:
                return "Error: Unable to parse the generated workout. Please try again."
            except KeyError as e:
                return f"Error: Missing required field in workout data: {str(e)}"
            except Exception as e:
                return f"Error formatting workout: {str(e)}"

        except Exception as e:
            error_message = str(e)
            if "api_key" in error_message.lower():
                return "Error: Invalid OpenAI API key. Please check your API key."
            elif "quota" in error_message.lower():
                return "Error: API quota exceeded. Please check your usage limits."
            else:
                return f"Error generating workout: {error_message}"

    def _create_prompt(self, movements, intensity_focus):
        style = "HIIT/CrossFit style with high intensity intervals and conditioning" if intensity_focus else "traditional Olympic weightlifting style"

        return f"""
        Create a detailed {style} workout focusing on these movements: {', '.join(movements)}.
        Return the response in JSON format with this exact structure:
        {{
            "warm_up": ["exercise1", "exercise2", ...],
            "main_workout": [
                {{"movement": "movement_name", "sets": X, "reps": Y, "intensity": "Z%"}}
            ],
            "accessory_work": [
                {{"exercise": "name", "sets": X, "reps": Y}}
            ],
            "cool_down": ["exercise1", "exercise2", ...],
            "time_domains": {{"total_time": "estimated workout duration", "work_intervals": "work interval length", "rest_intervals": "rest interval length"}}
        }}

        Include:
        1. A proper warm-up sequence specific to the selected movements
        2. Main workout with appropriate sets, reps, and intensity percentages
        3. Complementary accessory work
        4. An appropriate cool-down routine
        5. Time domains for intervals if it's a HIIT workout

        Ensure all exercises are appropriate for {style} and follow proper progression principles.
        If it's a HIIT workout, include dynamic movements and metabolic conditioning.
        For the main_workout section, ensure each movement has numeric values for sets and reps, and intensity as a percentage string.
        """

    def _format_workout(self, workout_data, intensity_focus):
        """Format the workout data into HTML with proper error handling."""
        html = "<div class='workout-plan'>"

        try:
            # Warm-up
            if "warm_up" in workout_data and isinstance(workout_data["warm_up"], list):
                html += "<h3>🔥 Warm-up</h3><ul>"
                for exercise in workout_data["warm_up"]:
                    html += f"<li>{exercise}</li>"
                html += "</ul>"

            # Main workout
            workout_type = "HIIT/CrossFit WOD" if intensity_focus else "Main Workout"
            if "main_workout" in workout_data and isinstance(workout_data["main_workout"], list):
                html += f"<h3>💪 {workout_type}</h3><ul>"
                for exercise in workout_data["main_workout"]:
                    if all(k in exercise for k in ("movement", "sets", "reps", "intensity")):
                        html += f"<li>{exercise['movement']}: {exercise['sets']} sets × {exercise['reps']} reps @ {exercise['intensity']}</li>"
                html += "</ul>"

            # Time domains for HIIT workouts
            if intensity_focus and "time_domains" in workout_data:
                time_info = workout_data["time_domains"]
                if all(k in time_info for k in ("total_time", "work_intervals", "rest_intervals")):
                    html += f"""
                    <div class='time-domains'>
                        <h4>⏱️ Time Domains</h4>
                        <ul>
                            <li>Total Time: {time_info['total_time']}</li>
                            <li>Work Intervals: {time_info['work_intervals']}</li>
                            <li>Rest Intervals: {time_info['rest_intervals']}</li>
                        </ul>
                    </div>
                    """

            # Accessory work
            if "accessory_work" in workout_data and isinstance(workout_data["accessory_work"], list):
                html += "<h3>🏋️‍♂️ Accessory Work</h3><ul>"
                for exercise in workout_data["accessory_work"]:
                    if all(k in exercise for k in ("exercise", "sets", "reps")):
                        html += f"<li>{exercise['exercise']}: {exercise['sets']} sets × {exercise['reps']} reps</li>"
                html += "</ul>"

            # Cool-down
            if "cool_down" in workout_data and isinstance(workout_data["cool_down"], list):
                html += "<h3>🧘‍♂️ Cool-down</h3><ul>"
                for exercise in workout_data["cool_down"]:
                    html += f"<li>{exercise}</li>"
                html += "</ul>"

            html += "</div>"
            return html

        except Exception as e:
            return f"Error formatting workout: {str(e)}"