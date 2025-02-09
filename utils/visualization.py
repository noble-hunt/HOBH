import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def create_progress_chart(data, movement):
    fig = make_subplots(rows=2, cols=1, 
                       subplot_titles=(f"{movement} Weight Progress", "Training Volume"),
                       vertical_spacing=0.2)

    # Add PR line
    pr_data = data.loc[data.groupby('date')['weight'].idxmax()]
    fig.add_trace(
        go.Scatter(
            x=pr_data['date'],
            y=pr_data['weight'],
            mode='lines+markers',
            name='PR Progress',
            line=dict(color='#FF4B4B', width=2),
            marker=dict(size=8, symbol='diamond'),
            hovertemplate="Date: %{x}<br>Weight: %{y}kg<br>PR!<extra></extra>"
        ),
        row=1, col=1
    )

    # Add all lifts as scatter points
    fig.add_trace(
        go.Scatter(
            x=data['date'],
            y=data['weight'],
            mode='markers',
            name='All Lifts',
            marker=dict(
                size=6,
                color=data['completed'].map({1: 'rgba(0, 255, 0, 0.5)', 0: 'rgba(255, 0, 0, 0.5)'}),
                symbol='circle'
            ),
            hovertemplate="Date: %{x}<br>Weight: %{y}kg<br>Reps: %{text}<extra></extra>",
            text=data['reps']
        ),
        row=1, col=1
    )

    # Add trend line
    fig.add_trace(
        go.Scatter(
            x=data['date'],
            y=data['weight'].rolling(window=5).mean(),
            mode='lines',
            name='Trend (5-day MA)',
            line=dict(color='rgba(0, 0, 0, 0.5)', dash='dash'),
            hovertemplate="Date: %{x}<br>Avg Weight: %{y:.1f}kg<extra></extra>"
        ),
        row=1, col=1
    )

    # Calculate and plot volume (weight × reps)
    data['volume'] = data['weight'] * data['reps']
    fig.add_trace(
        go.Bar(
            x=data['date'],
            y=data['volume'],
            name='Volume (kg × reps)',
            marker_color='#FFB6C1',
            hovertemplate="Date: %{x}<br>Volume: %{y:.0f}<extra></extra>"
        ),
        row=2, col=1
    )

    # Update layout
    fig.update_layout(
        height=800,
        showlegend=True,
        template="plotly_white",
        hovermode='x unified',
        xaxis=dict(title="Date", rangeslider=dict(visible=True)),
        xaxis2=dict(title="Date"),
        yaxis=dict(title="Weight (kg)"),
        yaxis2=dict(title="Volume")
    )

    return fig

def create_workout_summary(data):
    # Calculate summary statistics
    total_workouts = len(data)
    successful_workouts = len(data[data['completed'] == 1])
    success_rate = (successful_workouts / total_workouts * 100) if total_workouts > 0 else 0

    max_weight = data['weight'].max()
    avg_weight = data['weight'].mean()
    total_volume = (data['weight'] * data['reps']).sum()

    return {
        'total_workouts': total_workouts,
        'success_rate': success_rate,
        'max_weight': max_weight,
        'avg_weight': avg_weight,
        'total_volume': total_volume
    }

def create_heatmap(data):
    # Create a heatmap of workout frequency by day
    data['weekday'] = pd.to_datetime(data['date']).dt.day_name()
    data['hour'] = pd.to_datetime(data['date']).dt.hour

    workout_frequency = pd.crosstab(data['weekday'], data['hour'])

    fig = go.Figure(data=go.Heatmap(
        z=workout_frequency.values,
        x=workout_frequency.columns,
        y=workout_frequency.index,
        colorscale='Viridis',
        hoverongaps=False,
        hovertemplate="Day: %{y}<br>Hour: %{x}:00<br>Workouts: %{z}<extra></extra>"
    ))

    fig.update_layout(
        title="Workout Frequency Heatmap",
        xaxis_title="Hour of Day",
        yaxis_title="Day of Week",
        height=400
    )

    return fig