"""AI-powered recovery recommendations system."""
import os
import anthropic
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import json

from utils.models import WorkoutLog, Movement
from utils.recovery_calculator import RecoveryCalculator

class RecoveryAdvisor:
    """Generates personalized recovery recommendations using AI."""

    def __init__(self, session: Session):
        """Initialize the recovery advisor with database session."""
        self.session = session
        self.recovery_calculator = RecoveryCalculator()
        # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
        self.client = anthropic.Anthropic(
            api_key=os.environ.get('ANTHROPIC_API_KEY')
        )

    def get_recovery_recommendations(
        self,
        user_id: int,
        current_date: Optional[datetime] = None
    ) -> Dict:
        """Generate personalized recovery recommendations."""
        if current_date is None:
            current_date = datetime.now()

        try:
            # Get recent workout data
            recent_workouts = self._get_recent_workouts(user_id, current_date)

            # Get current recovery and strain scores
            recovery_data = self.recovery_calculator.calculate_recovery_score(
                user_id, current_date
            )
            strain_data = self.recovery_calculator.calculate_strain_score(
                user_id, current_date
            )

            # Prepare workout summary for AI context
            workout_summary = self._prepare_workout_summary(recent_workouts)

            # Generate recommendations using Claude
            recommendations = self._generate_ai_recommendations(
                workout_summary,
                recovery_data,
                strain_data
            )

            if isinstance(recommendations, dict):
                return {
                    'recommendations': json.dumps(recommendations),
                    'recovery_score': recovery_data['recovery_score'],
                    'strain_score': strain_data['strain_score'],
                    'recent_workouts': len(recent_workouts),
                    'generated_at': datetime.now().isoformat()
                }
            else:
                # If recommendations is not a dict, use fallback
                return self._get_fallback_recommendations(
                    recovery_data['recovery_score'],
                    strain_data['strain_score']
                )

        except Exception as e:
            print(f"Error in get_recovery_recommendations: {str(e)}")
            return self._get_fallback_recommendations()

    def _get_recent_workouts(
        self,
        user_id: int,
        current_date: datetime,
        days: int = 7
    ) -> List[WorkoutLog]:
        """Get user's recent workouts."""
        start_date = current_date - timedelta(days=days)

        return self.session.query(WorkoutLog)\
            .join(Movement)\
            .filter(
                WorkoutLog.user_id == user_id,
                WorkoutLog.date >= start_date,
                WorkoutLog.date <= current_date
            )\
            .order_by(WorkoutLog.date.desc())\
            .all()

    def _prepare_workout_summary(self, workouts: List[WorkoutLog]) -> str:
        """Create a summary of recent workouts for AI context."""
        if not workouts:
            return "No recent workouts found."

        summary = []
        for workout in workouts:
            workout_date = workout.date.strftime("%Y-%m-%d")
            movement_name = workout.movement.name if workout.movement else "Unknown"
            summary.append(
                f"- {workout_date}: {movement_name} "
                f"({workout.weight}kg × {workout.reps} reps) "
                f"[{'Successful' if workout.completed_successfully else 'Failed'}] "
                f"Difficulty: {workout.difficulty_level}"
            )

        return "\n".join(summary)

    def _generate_ai_recommendations(
        self,
        workout_summary: str,
        recovery_data: Dict,
        strain_data: Dict
    ) -> Dict:
        """Generate personalized recommendations using Claude."""
        try:
            prompt = f"""Based on the following workout and recovery data, provide specific, actionable recovery recommendations:

Recent Workouts:
{workout_summary}

Recovery Score: {recovery_data['recovery_score']}/10
Current Strain: {strain_data['strain_score']}/10

Strain Components:
- Volume Load: {strain_data['components']['volume']}/10
- Relative Intensity: {strain_data['components']['intensity']}/10
- Training Frequency: {strain_data['components']['frequency']}/10

Please provide recommendations in the following areas:
1. Recovery Activities: Specific activities to aid recovery
2. Nutrition: Targeted nutrition advice based on training load
3. Rest: Sleep and rest recommendations
4. Next Training: Guidance for next training session
5. Warning Signs: What to watch out for

Format your response as a JSON object with these sections as keys."""

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1500,
                temperature=0.7
            )

            # Parse the response and return as a dictionary
            try:
                recommendations = response.content[0].text
                return json.loads(recommendations)  # Parse JSON string to dict
            except (json.JSONDecodeError, AttributeError, IndexError):
                return self._get_default_recommendations()

        except Exception as e:
            print(f"Error generating recommendations: {str(e)}")
            return self._get_default_recommendations()

    def _get_default_recommendations(self) -> Dict:
        """Get default recommendations when AI generation fails."""
        return {
            "Recovery Activities": "Focus on light mobility work and stretching.",
            "Nutrition": "Maintain balanced meals with adequate protein.",
            "Rest": "Aim for 7-9 hours of sleep.",
            "Next Training": "Consider intensity based on recovery score.",
            "Warning Signs": "Monitor for unusual fatigue or discomfort."
        }

    def _get_fallback_recommendations(
        self,
        recovery_score: float = 5.0,
        strain_score: float = 5.0
    ) -> Dict:
        """Get fallback response when the main process fails."""
        recommendations = self._get_default_recommendations()
        return {
            'recommendations': json.dumps(recommendations),
            'recovery_score': recovery_score,
            'strain_score': strain_score,
            'recent_workouts': 0,
            'generated_at': datetime.now().isoformat()
        }