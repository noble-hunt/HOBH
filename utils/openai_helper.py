import os
from openai import OpenAI
import json

class WorkoutGenerator:
    def __init__(self):
        self.model = "gpt-4"  # Using the stable GPT-4 model
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def generate_workout(self, movements):
        prompt = self._create_prompt(movements)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an experienced Olympic weightlifting coach. "
                        "Generate detailed workouts focusing on the specified movements."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            workout_data = json.loads(response.choices[0].message.content)
            return self._format_workout(workout_data)

        except Exception as e:
            error_message = str(e)
            if "model_not_found" in error_message:
                return "Error: Unable to access the GPT-4 model. Please make sure you have access to GPT-4 in your OpenAI account."
            elif "invalid_api_key" in error_message:
                return "Error: Invalid API key. Please check your OpenAI API key."
            elif "insufficient_quota" in error_message:
                return "Error: OpenAI API quota exceeded. Please check your usage limits."
            else:
                return f"Error generating workout: {error_message}"

    def _create_prompt(self, movements):
        return f"""
        Create a detailed Olympic weightlifting workout focusing on these movements: {', '.join(movements)}.

        Include:
        - Warm-up routine
        - Main workout with sets, reps, and intensity percentages
        - Accessory work
        - Cool-down

        Return the response in this JSON format:
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