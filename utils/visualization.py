import plotly.express as px
import plotly.graph_objects as go

def create_progress_chart(data, movement):
    fig = go.Figure()
    
    # Add PR line
    pr_data = data.loc[data.groupby('date')['weight'].idxmax()]
    fig.add_trace(
        go.Scatter(
            x=pr_data['date'],
            y=pr_data['weight'],
            mode='lines+markers',
            name='PR Progress',
            line=dict(color='#FF4B4B', width=2),
            marker=dict(size=8, symbol='diamond')
        )
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
                color='rgba(0, 0, 0, 0.5)',
                symbol='circle'
            )
        )
    )
    
    fig.update_layout(
        title=f"{movement} Progress Over Time",
        xaxis_title="Date",
        yaxis_title="Weight (kg)",
        template="plotly_white",
        hovermode='x unified',
        showlegend=True,
        height=500
    )
    
    return fig
