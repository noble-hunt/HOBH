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
        if intensity_focus:
            return f"""
            Create a CrossFit-style workout using these movements as a base: {', '.join(movements)}.
            You can add complementary movements typical in CrossFit (burpees, box jumps, etc).

            Return the response in JSON format with this exact structure:
            {{
                "workout_type": "For Time" or "AMRAP" or "EMOM",
                "description": "Brief description of the workout format (e.g., '21-15-9 reps of')",
                "movements": [
                    {{
                        "name": "movement name",
                        "details": "weight/height/variation details or null"
                    }}
                ],
                "time_cap": "time cap in minutes",
                "scaling_options": [
                    {{
                        "level": "Beginner/Intermediate/Advanced",
                        "adjustments": "specific scaling suggestions"
                    }}
                ]
            }}

            The workout should follow CrossFit best practices:
            1. Clear rep schemes (like 21-15-9 or 5 rounds)
            2. Appropriate weights and standards
            3. Movement pairing that makes sense
            4. Reasonable time cap
            5. Include scaling options for different skill levels
            """
        else:
            return f"""
            Create a traditional Olympic weightlifting workout focusing on these movements: {', '.join(movements)}.
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
            2. Main workout with appropriate sets, reps, and intensity percentages
            3. Complementary accessory work
            4. An appropriate cool-down routine
            """

    def _format_workout(self, workout_data, intensity_focus):
        """Format the workout data into HTML with proper error handling."""
        try:
            if intensity_focus:
                # Format CrossFit-style workout
                html = "<div class='workout-plan crossfit-style'>"

                # Workout type and description
                html += f"<h3>🏋️‍♂️ {workout_data['workout_type']}</h3>"
                html += f"<p class='workout-description'>{workout_data['description']}</p>"

                # Movements
                html += "<div class='movements'>"
                for movement in workout_data['movements']:
                    html += f"<p>{movement['name']}"
                    if movement.get('details'):  # Use .get() to safely access 'details'
                        html += f" <span class='movement-details'>({movement['details']})</span>"
                    html += "</p>"
                html += "</div>"

                # Time cap
                html += f"<p class='time-cap'>⏱️ Time cap: {workout_data['time_cap']}</p>"

                # Scaling options
                html += "<div class='scaling-options'>"
                html += "<h4>🔄 Scaling Options</h4>"
                for option in workout_data['scaling_options']:
                    html += f"<div class='scale-level'><strong>{option['level']}:</strong><p>{option['adjustments']}</p></div>"
                html += "</div></div>"

            else:
                # Format traditional workout
                html = "<div class='workout-plan'>"

                # Warm-up
                if workout_data.get("warm_up") and isinstance(workout_data["warm_up"], list):
                    html += "<h3>🔥 Warm-up</h3><ul>"
                    for exercise in workout_data["warm_up"]:
                        html += f"<li>{exercise}</li>"
                    html += "</ul>"

                # Main workout
                if workout_data.get("main_workout") and isinstance(workout_data["main_workout"], list):
                    html += "<h3>💪 Main Workout</h3><ul>"
                    for exercise in workout_data["main_workout"]:
                        if all(k in exercise for k in ("movement", "sets", "reps", "intensity")):
                            html += f"<li>{exercise['movement']}: {exercise['sets']} sets × {exercise['reps']} reps @ {exercise['intensity']}</li>"
                    html += "</ul>"

                # Accessory work
                if workout_data.get("accessory_work") and isinstance(workout_data["accessory_work"], list):
                    html += "<h3>🏋️‍♂️ Accessory Work</h3><ul>"
                    for exercise in workout_data["accessory_work"]:
                        if all(k in exercise for k in ("exercise", "sets", "reps")):
                            html += f"<li>{exercise['exercise']}: {exercise['sets']} sets × {exercise['reps']} reps</li>"
                    html += "</ul>"

                # Cool-down
                if workout_data.get("cool_down") and isinstance(workout_data["cool_down"], list):
                    html += "<h3>🧘‍♂️ Cool-down</h3><ul>"
                    for exercise in workout_data["cool_down"]:
                        html += f"<li>{exercise}</li>"
                    html += "</ul>"

                html += "</div>"
            return html

        except Exception as e:
            return f"Error formatting workout: {str(e)}"