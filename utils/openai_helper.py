import os
import json
from anthropic import Anthropic

class WorkoutGenerator:
    def __init__(self):
        # The newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
        self.model = "claude-3-5-sonnet-20241022"
        self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def generate_workout(self, movements):
        prompt = self._create_prompt(movements)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )

            # Parse the response content as JSON
            try:
                workout_data = json.loads(response.content)
                return self._format_workout(workout_data)
            except json.JSONDecodeError:
                return "Error: Unable to parse the generated workout. Please try again."

        except Exception as e:
            error_message = str(e)
            if "api_key" in error_message.lower():
                return "Error: Invalid Anthropic API key. Please check your API key."
            elif "quota" in error_message.lower():
                return "Error: API quota exceeded. Please check your usage limits."
            else:
                return f"Error generating workout: {error_message}"

    def _create_prompt(self, movements):
        return f"""
        You are an expert Olympic weightlifting coach. Create a detailed workout focusing on these movements: {', '.join(movements)}.

        The response should be valid JSON format with this exact structure:
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