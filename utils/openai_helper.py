import os
import json
from openai import OpenAI

class WorkoutGenerator:
    def __init__(self):
        self.model = "gpt-4"  # Using standard GPT-4 model
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def generate_workout(self, movements):
        prompt = self._create_prompt(movements)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Olympic weightlifting coach."
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
                return self._format_workout(workout_data)
            except json.JSONDecodeError:
                return "Error: Unable to parse the generated workout. Please try again."

        except Exception as e:
            error_message = str(e)
            if "api_key" in error_message.lower():
                return "Error: Invalid OpenAI API key. Please check your API key."
            elif "quota" in error_message.lower():
                return "Error: API quota exceeded. Please check your usage limits."
            else:
                return f"Error generating workout: {error_message}"

    def _create_prompt(self, movements):
        return f"""
        Create a detailed workout focusing on these movements: {', '.join(movements)}.
        Return the response in JSON format with this exact structure:
        {{
            "warm_up": ["exercise1", "exercise2", ...],
            "main_workout": [
                {{"movement": "movement_name", "sets": X, "reps": Y, "intensity": "Z%"}}
            ],
            "accessory_work": [
                {{"exercise": "name", "sets": X, "reps": Y}}
            ],
            "cool_down": ["exercise1", "exercise2", ...]
        }}

        Include:
        1. A proper warm-up sequence specific to the selected movements
        2. Main workout with appropriate sets, reps, and intensity percentages based on standard Olympic weightlifting progression
        3. Complementary accessory work
        4. An appropriate cool-down routine

        Ensure all exercises are appropriate for Olympic weightlifting and follow proper progression principles.
        """

    def _format_workout(self, workout_data):
        html = "<div class='workout-plan'>"

        # Warm-up
        html += "<h3>🔥 Warm-up</h3><ul>"
        for exercise in workout_data["warm_up"]:
            html += f"<li>{exercise}</li>"
        html += "</ul>"

        # Main workout
        html += "<h3>💪 Main Workout</h3><ul>"
        for exercise in workout_data["main_workout"]:
            html += f"<li>{exercise['movement']}: {exercise['sets']} sets × {exercise['reps']} reps @ {exercise['intensity']}</li>"
        html += "</ul>"

        # Accessory work
        html += "<h3>🏋️‍♂️ Accessory Work</h3><ul>"
        for exercise in workout_data["accessory_work"]:
            html += f"<li>{exercise['exercise']}: {exercise['sets']} sets × {exercise['reps']} reps</li>"
        html += "</ul>"

        # Cool-down
        html += "<h3>🧘‍♂️ Cool-down</h3><ul>"
        for exercise in workout_data["cool_down"]:
            html += f"<li>{exercise}</li>"
        html += "</ul>"

        html += "</div>"
        return html