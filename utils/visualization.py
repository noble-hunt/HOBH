import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def create_progress_chart(data, movement):
    fig = make_subplots(rows=2, cols=1, 
                       subplot_titles=(f"{movement} Weight Progress", "Training Volume"),
                       vertical_spacing=0.2)

    # Add PR line with milestone markers
    pr_data = data.loc[data.groupby('date')['weight'].idxmax()]
    milestone_data = _calculate_pr_milestones(pr_data)

    # Add PR line
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

    # Add milestone markers
    if not milestone_data.empty:
        fig.add_trace(
            go.Scatter(
                x=milestone_data['date'],
                y=milestone_data['weight'],
                mode='markers',
                name='Milestones',
                marker=dict(
                    size=15,
                    symbol='star',
                    color='#FFD700',
                    line=dict(color='#B8860B', width=2)
                ),
                hovertemplate="Milestone!<br>Date: %{x}<br>Weight: %{y}kg<br>%{text}<extra></extra>",
                text=milestone_data['milestone_text']
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
    # Create a heatmap of workout frequency and intensity by day
    data['weekday'] = pd.to_datetime(data['date']).dt.day_name()
    data['hour'] = pd.to_datetime(data['date']).dt.hour

    # Calculate average intensity (weight relative to max weight) for each time slot
    data['intensity'] = data['weight'] / data['weight'].max() * 100

    # Create pivot table for intensity heatmap
    intensity_matrix = pd.pivot_table(
        data,
        values='intensity',
        index='weekday',
        columns='hour',
        aggfunc='mean'
    )

    # Create the heatmap
    fig = go.Figure(data=go.Heatmap(
        z=intensity_matrix.values,
        x=intensity_matrix.columns,
        y=intensity_matrix.index,
        colorscale='Viridis',
        hoverongaps=False,
        hovertemplate="Day: %{y}<br>Hour: %{x}:00<br>Intensity: %{z:.1f}%<extra></extra>"
    ))

    fig.update_layout(
        title="Workout Intensity Heatmap",
        xaxis_title="Hour of Day",
        yaxis_title="Day of Week",
        height=400
    )

    return fig

def create_3d_movement_progress(data, movement):
    """Create a 3D visualization of movement progress."""
    # Calculate relative intensity
    data['relative_intensity'] = data['weight'] / data['weight'].max() * 100

    # Create 3D scatter plot
    fig = go.Figure(data=[
        go.Scatter3d(
            x=data['date'],
            y=data['weight'],
            z=data['volume'],
            mode='markers',
            marker=dict(
                size=8,
                color=data['relative_intensity'],
                colorscale='Viridis',
                opacity=0.8,
                colorbar=dict(title="Relative Intensity (%)")
            ),
            hovertemplate=(
                "Date: %{x}<br>" +
                "Weight: %{y}kg<br>" +
                "Volume: %{z}<br>" +
                "Intensity: %{marker.color:.1f}%<extra></extra>"
            )
        )
    ])

    # Update layout
    fig.update_layout(
        title=f"3D Progress Visualization - {movement}",
        scene=dict(
            xaxis_title="Date",
            yaxis_title="Weight (kg)",
            zaxis_title="Volume (kg × reps)",
            camera=dict(
                up=dict(x=0, y=0, z=1),
                center=dict(x=0, y=0, z=0),
                eye=dict(x=1.5, y=1.5, z=1.5)
            )
        ),
        height=700
    )

    return fig

def _calculate_pr_milestones(pr_data):
    """Calculate milestone achievements in PR progression."""
    if pr_data.empty:
        return pd.DataFrame()

    milestones = []
    last_pr = 0
    milestone_thresholds = [5, 10, 20, 50]  # kg increments for milestones

    for _, row in pr_data.iterrows():
        for threshold in milestone_thresholds:
            if last_pr < threshold and row['weight'] >= threshold:
                milestones.append({
                    'date': row['date'],
                    'weight': row['weight'],
                    'milestone_text': f"{threshold}kg milestone!"
                })
        last_pr = row['weight']

    return pd.DataFrame(milestones)