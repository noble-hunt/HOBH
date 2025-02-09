import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import warnings
warnings.filterwarnings('ignore')

class PRPredictor:
    def __init__(self, data):
        self.data = data
        self.min_data_points = 5  # Minimum data points needed for prediction
        self.prediction_days = 30  # Predict PR for next 30 days

    def prepare_data(self):
        """Prepare data for prediction analysis."""
        if len(self.data) < self.min_data_points:
            return None, None

        # Convert dates to numeric (days since first workout)
        first_date = self.data['date'].min()
        days_since_start = (self.data['date'] - first_date).dt.days

        # Get PR progression
        pr_data = self.data.loc[self.data.groupby('date')['weight'].idxmax()]
        pr_days = (pr_data['date'] - first_date).dt.days

        return days_since_start.values.reshape(-1, 1), self.data['weight'].values

    def predict_pr(self):
        """Predict future PR based on training patterns."""
        X, y = self.prepare_data()
        
        if X is None or len(X) < self.min_data_points:
            return {
                'prediction': None,
                'confidence': 0,
                'message': "Not enough data for prediction. Need at least 5 workouts."
            }

        # Fit linear regression model
        model = LinearRegression()
        model.fit(X, y)

        # Calculate R² score for confidence
        confidence = r2_score(y, model.predict(X))

        # Predict for future date
        last_day = X.max()
        future_day = last_day + self.prediction_days
        predicted_weight = model.predict([[future_day]])[0]

        # Calculate average rate of improvement (kg per day)
        rate_of_improvement = model.coef_[0]
        
        # Get current PR
        current_pr = self.data['weight'].max()

        # Calculate realistic prediction (limit maximum improvement)
        max_realistic_improvement = 0.15  # Maximum 15% improvement in 30 days
        max_predicted = current_pr * (1 + max_realistic_improvement)
        predicted_weight = min(predicted_weight, max_predicted)

        # Round prediction to nearest 0.5kg
        predicted_weight = round(predicted_weight * 2) / 2

        # Generate message based on prediction
        if predicted_weight <= current_pr:
            message = "Maintain current training pattern to preserve your PR."
            prediction = current_pr
        else:
            improvement = predicted_weight - current_pr
            message = f"Based on your training pattern, you could achieve a new PR of {predicted_weight}kg "
            message += f"(+{improvement:.1f}kg) within the next 30 days."

        return {
            'current_pr': current_pr,
            'prediction': predicted_weight,
            'confidence': confidence,
            'improvement_rate': rate_of_improvement,
            'message': message
        }

    def get_training_insights(self):
        """Generate training insights based on data patterns."""
        if len(self.data) < self.min_data_points:
            return "Not enough data for insights. Continue logging your workouts!"

        # Analyze training frequency
        avg_days_between = self.analyze_training_frequency()
        
        # Analyze success rate
        success_rate = (self.data['completed'] == 1).mean()
        
        # Analyze volume trends
        volume_trend = self.analyze_volume_trend()

        insights = []
        
        # Frequency insights
        if avg_days_between > 5:
            insights.append("Consider increasing training frequency for better progress.")
        elif avg_days_between < 2:
            insights.append("Ensure adequate rest between training sessions.")

        # Success rate insights
        if success_rate < 0.7:
            insights.append("High failure rate detected. Consider adjusting weights or volume.")
        elif success_rate > 0.9:
            insights.append("High success rate - you might be ready for more challenging weights.")

        # Volume insights
        if volume_trend == 'increasing':
            insights.append("Good progression in training volume!")
        elif volume_trend == 'decreasing':
            insights.append("Training volume is decreasing. Monitor fatigue and recovery.")

        return "\n".join(insights) if insights else "Keep up the consistent training!"

    def analyze_training_frequency(self):
        """Analyze average days between training sessions."""
        dates = sorted(self.data['date'].unique())
        if len(dates) < 2:
            return 0
        
        intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
        return sum(intervals) / len(intervals)

    def analyze_volume_trend(self):
        """Analyze if training volume is increasing or decreasing."""
        if len(self.data) < self.min_data_points:
            return 'neutral'
            
        self.data['volume'] = self.data['weight'] * self.data['reps']
        recent_volume = self.data.sort_values('date').tail(self.min_data_points)['volume']
        
        slope = np.polyfit(range(len(recent_volume)), recent_volume, 1)[0]
        
        if slope > 0:
            return 'increasing'
        elif slope < 0:
            return 'decreasing'
        return 'neutral'
