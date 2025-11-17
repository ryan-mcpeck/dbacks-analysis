import streamlit as st
import pandas as pd

try:
    import plotly.graph_objects as go
except ImportError as e:
    st.error(f"Error importing plotly: {e}. Attempting to resolve...")
    import sys
    st.write("Python path:", sys.path)
    st.write("Installed packages:")
    import pkg_resources
    st.write([f"{pkg.key} {pkg.version}" for pkg in pkg_resources.working_set])
    raise

# Set page config
st.set_page_config(
    page_title="D-backs Pitching Analysis",
    page_icon="⚾",
    layout="wide"
)

# Title and Description
st.title("Arizona Diamondbacks Pitching Analysis")
st.markdown("Analysis of pitch types and patterns across the D-backs pitching staff.")

# Load the data
@st.cache_data
def load_data():
    print("Loading data from dbacks_team_statcast.csv...")
    return pd.read_csv('dbacks_team_statcast.csv')

dbacks_data = load_data()

# Process the data
def process_pitching_data(data):
    # Identify plays where the Diamondbacks were the pitching team
    is_dbacks_pitching = ((data['home_team'] == 'AZ') & (data['inning_topbot'] == 'Top')) | \
                        ((data['away_team'] == 'AZ') & (data['inning_topbot'] == 'Bot'))
    dbacks_pitching_data = data[is_dbacks_pitching].copy()
    
    # Get pitcher role selection from sidebar
    pitcher_role = st.sidebar.selectbox(
        "Filter by Role",
        ["Starters Only", "Relievers Only", "All Pitchers"]
    )
    
    # Identify starting and relief appearances
    first_inning_appearances = dbacks_pitching_data[dbacks_pitching_data['inning'] == 1].groupby(['game_pk', 'player_name']).first()
    relief_appearances = dbacks_pitching_data[dbacks_pitching_data['inning'] > 1].groupby(['game_pk', 'player_name']).first()
    
    # Count starts and relief appearances for each pitcher
    starts_count = first_inning_appearances.reset_index().groupby('player_name')['game_pk'].nunique().reset_index(name='starts')
    relief_count = relief_appearances.reset_index().groupby('player_name')['game_pk'].nunique().reset_index(name='relief_games')
    
    # Merge the counts
    pitcher_appearances = pd.merge(starts_count, relief_count, on='player_name', how='outer').fillna(0)
    pitcher_appearances['total_games'] = pitcher_appearances['starts'] + pitcher_appearances['relief_games']
    
    # Filter based on role selection
    if pitcher_role == "Starters Only":
        min_starts = st.sidebar.slider("Minimum starts", 1, 30, 10)
        filtered_pitchers = pitcher_appearances[pitcher_appearances['starts'] >= min_starts]
    elif pitcher_role == "Relievers Only":
        min_relief = st.sidebar.slider("Minimum relief appearances", 1, 50, 10)
        filtered_pitchers = pitcher_appearances[
            (pitcher_appearances['relief_games'] >= min_relief) & 
            (pitcher_appearances['starts'] < 5)  # To exclude frequent starters
        ]
    else:  # All Pitchers
        min_games = st.sidebar.slider("Minimum total appearances", 1, 50, 10)
        filtered_pitchers = pitcher_appearances[pitcher_appearances['total_games'] >= min_games]
    
    filtered_pitcher_list = filtered_pitchers['player_name'].unique()
    
    # Filter the data to include only the selected pitchers
    filtered_data = dbacks_pitching_data[dbacks_pitching_data['player_name'].isin(filtered_pitcher_list)]
    
    return filtered_data, filtered_pitchers

# Sidebar
st.sidebar.header("Filters")

# Add date range filters
min_date = pd.to_datetime(dbacks_data['game_date']).min()
max_date = pd.to_datetime(dbacks_data['game_date']).max()

start_date = st.sidebar.date_input(
    "Start Date",
    value=min_date,
    min_value=min_date,
    max_value=max_date
)

end_date = st.sidebar.date_input(
    "End Date",
    value=max_date,
    min_value=min_date,
    max_value=max_date
)

# Filter data by date range
filtered_data = dbacks_data[
    (pd.to_datetime(dbacks_data['game_date']).dt.date >= start_date) &
    (pd.to_datetime(dbacks_data['game_date']).dt.date <= end_date)
]

# Process the filtered data
pitcher_data, pitcher_appearances = process_pitching_data(filtered_data)

# Calculate pitch usage
pitch_counts = pitcher_data.groupby(['player_name', 'pitch_name']).size().reset_index(name='count')
pitch_usage = pitch_counts.pivot(index='player_name', columns='pitch_name', values='count').fillna(0)
total_pitch_counts = pitch_usage.sum()
sorted_pitch_columns = total_pitch_counts.sort_values(ascending=False).index
pitch_usage = pitch_usage[sorted_pitch_columns]
pitch_percentages = pitch_usage.div(pitch_usage.sum(axis=1), axis=0) * 100

# Sort pitchers and create labels based on role
pitcher_role = st.session_state.get('pitcher_role', "Starters Only")
if pitcher_role == "Starters Only":
    sorted_pitchers = pitcher_appearances.sort_values('starts', ascending=False)
    pitcher_labels = [f"{name} ({int(starts)} starts)" for name, starts in 
                     zip(sorted_pitchers['player_name'], sorted_pitchers['starts'])]
elif pitcher_role == "Relievers Only":
    sorted_pitchers = pitcher_appearances.sort_values('relief_games', ascending=False)
    pitcher_labels = [f"{name} ({int(relief)} games)" for name, relief in 
                     zip(sorted_pitchers['player_name'], sorted_pitchers['relief_games'])]
else:
    sorted_pitchers = pitcher_appearances.sort_values('total_games', ascending=False)
    pitcher_labels = [f"{name} ({int(total)} games)" for name, total in 
                     zip(sorted_pitchers['player_name'], sorted_pitchers['total_games'])]

pitch_percentages = pitch_percentages.loc[sorted_pitchers['player_name']]

# Create interactive stacked bar chart using plotly
fig = go.Figure()

for pitch_type in pitch_percentages.columns:
    fig.add_trace(go.Bar(
        name=pitch_type,
        y=pitcher_labels,
        x=pitch_percentages[pitch_type],
        orientation='h'
    ))

role_title = {
    "Starters Only": "Starting Rotation",
    "Relievers Only": "Bullpen",
    "All Pitchers": "Pitching Staff"
}

fig.update_layout(
    barmode='stack',
    title=f'Pitch Type Distribution - {role_title[pitcher_role]} (2025)',
    xaxis_title='Usage Percentage (%)',
    yaxis_title='Pitcher (Appearances)',
    height=600,
    showlegend=True,
    legend_title='Pitch Type',
    yaxis={'categoryorder': 'total ascending'}
)

# Add gridlines
fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')

# Display the plot
st.plotly_chart(fig, use_container_width=True)

# Date Range Summary
st.markdown("---")
games_in_range = filtered_data['game_pk'].nunique()
date_range = (end_date - start_date).days + 1
st.markdown(f"""
    ### Selected Time Period
    - **Date Range**: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}
    - **Days**: {date_range}
    - **Games**: {games_in_range}
""")

# Pitcher-specific analysis
st.markdown("---")
st.header("Individual Pitcher Analysis")

# Get list of pitchers
available_pitchers = sorted(pitcher_data['player_name'].unique())
selected_pitcher = st.selectbox("Select a pitcher", available_pitchers)

# Filter data for selected pitcher
pitcher_specific_data = pitcher_data[pitcher_data['player_name'] == selected_pitcher].copy()
pitcher_specific_data['game_date'] = pd.to_datetime(pitcher_specific_data['game_date'])

# Calculate pitch mix over time
pitch_dates = pitcher_specific_data.groupby(['game_date', 'pitch_name']).size().reset_index(name='count')
pitch_dates_pivot = pitch_dates.pivot(index='game_date', columns='pitch_name', values='count').fillna(0)

# Calculate 7-day rolling average for smoother lines
rolling_mix = pitch_dates_pivot.rolling(window=7, min_periods=1, center=True).sum()
rolling_percentages = rolling_mix.div(rolling_mix.sum(axis=1), axis=0) * 100

# Create enhanced time series plot
fig_time = go.Figure()

for pitch_type in rolling_percentages.columns:
    fig_time.add_trace(go.Scatter(
        x=rolling_percentages.index,
        y=rolling_percentages[pitch_type],
        name=pitch_type,
        mode='lines',
        line=dict(width=3, shape='spline'),  # Thicker lines with smooth curves
        hovertemplate=f"<b>%{{y:.1f}}%</b> {pitch_type}<br>%{{x|%B %d}}<extra></extra>"
    ))

fig_time.update_layout(
    title=dict(
        text=f'Pitch Mix Trends - {selected_pitcher}',
        font=dict(size=20, color='white')
    ),
    xaxis_title=dict(text='Date', font=dict(color='white')),
    yaxis_title=dict(text='Usage Percentage (%)', font=dict(color='white')),
    hovermode='x unified',
    height=500,  # Slightly taller
    showlegend=True,
    legend_title=dict(text='Pitch Type', font=dict(color='white')),
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=1.02,
        font=dict(color='white'),
        bgcolor='rgba(0,0,0,0)'
    ),
    margin=dict(r=150),  # More room for legend
    paper_bgcolor='rgb(17, 17, 17)',  # Dark background for the entire plot
    plot_bgcolor='rgb(17, 17, 17)',   # Dark background for the plotting area
    yaxis=dict(
        gridcolor='rgba(255, 255, 255, 0.1)',
        range=[0, 100],
        ticksuffix='%',
        zerolinecolor='rgba(255, 255, 255, 0.2)',
        zerolinewidth=1,
        tickfont=dict(color='white'),
        tickcolor='white'
    ),
    xaxis=dict(
        gridcolor='rgba(255, 255, 255, 0.1)',
        tickformat='%B %d',
        zerolinecolor='rgba(255, 255, 255, 0.2)',
        zerolinewidth=1,
        tickfont=dict(color='white'),
        tickcolor='white'
    )
)

st.plotly_chart(fig_time, use_container_width=True)

# Additional statistics for the selected pitcher
col1, col2 = st.columns(2)

with col1:
    st.subheader("Pitch Velocities")
    avg_velo = pitcher_specific_data.groupby('pitch_name')['release_speed'].agg(['mean', 'min', 'max']).reset_index()
    avg_velo.columns = ['Pitch Type', 'Avg. Velocity', 'Min. Velocity', 'Max. Velocity']
    avg_velo = avg_velo.sort_values('Avg. Velocity', ascending=False)
    st.dataframe(avg_velo.round(1))

with col2:
    st.subheader("Pitch Usage Summary")
    pitch_summary = pitcher_specific_data.groupby('pitch_name').size().reset_index(name='Count')
    pitch_summary['Percentage'] = pitch_summary['Count'] / pitch_summary['Count'].sum() * 100
    pitch_summary = pitch_summary.sort_values('Count', ascending=False)
    st.dataframe(pitch_summary.round(1))

# Overall Statistics Section
st.markdown("---")
st.header("Team-wide Pitch Analysis")

# Calculate and display statistics
col1, col2 = st.columns(2)

with col1:
    st.subheader("Pitch Velocities by Type")
    avg_velo = pitcher_data.groupby(['player_name', 'pitch_name'])['release_speed'].mean().reset_index()
    avg_velo = avg_velo.sort_values(['player_name', 'release_speed'], ascending=[True, False])
    avg_velo.columns = ['Pitcher', 'Pitch Type', 'Avg. Velocity (mph)']
    st.dataframe(avg_velo.round(1))

with col2:
    st.subheader("Total Pitches Thrown")
    total_pitches = pitch_counts.groupby('player_name')['count'].sum().reset_index()
    total_pitches = total_pitches.sort_values('count', ascending=False)
    total_pitches.columns = ['Pitcher', 'Total Pitches']
    st.dataframe(total_pitches)
