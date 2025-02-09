import os
from openai import OpenAI
from datetime import datetime

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
class QuoteGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    def generate_workout_quote(self, user_data=None):
        """Generate a personalized workout motivation quote."""
        try:
            context = self._build_context(user_data)
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a motivational fitness coach specializing in Olympic weightlifting. "
                            "Generate a short, powerful, and personalized motivational quote. "
                            "The quote should be inspiring and specific to weightlifting. "
                            "Keep it under 100 characters for impact."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Generate a motivational quote for an Olympic weightlifter. Context: {context}"
                    }
                ],
                max_tokens=100,
                temperature=0.7
            )
            return response.choices[0].message.content.strip('"')
        except Exception as e:
            return "Every lift is a step toward greatness. Keep pushing! 💪"

    def _build_context(self, user_data):
        """Build context for personalization based on user data."""
        if not user_data:
            return "General weightlifting motivation"
            
        context = []
        if 'recent_achievement' in user_data:
            context.append(f"Recently achieved: {user_data['recent_achievement']}")
        if 'target_movement' in user_data:
            context.append(f"Working on: {user_data['target_movement']}")
        if 'current_streak' in user_data:
            context.append(f"Current training streak: {user_data['current_streak']} days")
            
        return " | ".join(context) if context else "General weightlifting motivation"
