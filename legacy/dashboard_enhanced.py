import streamlit as st
import pandas as pd
import sys
import numpy as np

# Add pybaseball to path
sys.path.insert(0, r'c:\Users\valak\GitHub Repos\pybaseball')
import pybaseball as pyb

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
except ImportError as e:
    st.error(f"Error importing plotly: {e}. Please install plotly.")
    st.stop()

# Set page config
st.set_page_config(
    page_title="D-backs Advanced Pitching Analysis",
    page_icon="⚾",
    layout="wide"
)

# Title and Description
st.title("🔥 Arizona Diamondbacks Advanced Pitching Analysis")
st.markdown("Enhanced analysis with advanced metrics, league context, and pitcher performance insights.")

# Enhanced data loading with caching
@st.cache_data
def load_data():
    """Load and enhance the Diamondbacks statcast data"""
    print("Loading data from dbacks_team_statcast.csv...")
    data = pd.read_csv('dbacks_team_statcast.csv')
    
    # Add derived metrics
    data['called_strike'] = ((data['type'] == 'S') & (data['description'] == 'called_strike')).astype(int)
    data['swinging_strike'] = ((data['type'] == 'S') & (data['description'] == 'swinging_strike')).astype(int)
    data['whiff'] = data['swinging_strike']
    data['contact'] = ((data['type'] == 'X') | (data['description'].str.contains('foul', na=False))).astype(int)
    
    # Calculate pitch efficiency metrics
    data['strike'] = (data['type'] == 'S').astype(int)
    data['ball'] = (data['type'] == 'B').astype(int)
    
    return data

@st.cache_data
def get_league_context():
    """Get league-wide pitching context for comparison"""
    try:
        # Enable caching for pybaseball
        pyb.cache.enable()
        
        # Get current season team pitching data for context
        current_year = 2025
        team_pitching_data = pyb.team_pitching(current_year)
        return team_pitching_data
    except Exception as e:
        st.warning(f"Could not load league context: {e}")
        return None

# Load data
dbacks_data = load_data()
league_data = get_league_context()

# Process the pitching data with enhanced metrics
def process_enhanced_pitching_data(data):
    """Enhanced processing with advanced metrics"""
    # Identify plays where the Diamondbacks were the pitching team
    is_dbacks_pitching = ((data['home_team'] == 'AZ') & (data['inning_topbot'] == 'Top')) | \
                        ((data['away_team'] == 'AZ') & (data['inning_topbot'] == 'Bot'))
    dbacks_pitching_data = data[is_dbacks_pitching].copy()
    
    # Get pitcher role selection from sidebar
    pitcher_role = st.sidebar.selectbox(
        "Filter by Role",
        ["Starters Only", "Relievers Only", "All Pitchers"]
    )
    
    # Enhanced role identification
    # Group by game and pitcher to identify roles more accurately
    game_pitcher_stats = dbacks_pitching_data.groupby(['game_pk', 'player_name']).agg({
        'inning': ['min', 'max'],
        'pitch_number': 'count',
        'outs_when_up': 'max'
    }).reset_index()
    
    game_pitcher_stats.columns = ['game_pk', 'player_name', 'first_inning', 'last_inning', 'total_pitches', 'max_outs']
    
    # Classify appearances more accurately
    game_pitcher_stats['is_starter'] = (game_pitcher_stats['first_inning'] == 1) & (game_pitcher_stats['total_pitches'] >= 50)
    game_pitcher_stats['is_opener'] = (game_pitcher_stats['first_inning'] == 1) & (game_pitcher_stats['total_pitches'] < 50)
    game_pitcher_stats['is_reliever'] = game_pitcher_stats['first_inning'] > 1
    game_pitcher_stats['is_closer'] = (game_pitcher_stats['last_inning'] >= 9) & (game_pitcher_stats['is_reliever'])
    
    # Count appearances by type
    pitcher_roles = game_pitcher_stats.groupby('player_name').agg({
        'is_starter': 'sum',
        'is_opener': 'sum', 
        'is_reliever': 'sum',
        'is_closer': 'sum',
        'game_pk': 'nunique'
    }).reset_index()
    
    pitcher_roles.columns = ['player_name', 'starts', 'openers', 'relief_games', 'saves_opps', 'total_games']
    
    # Filter based on role selection with enhanced criteria
    if pitcher_role == "Starters Only":
        min_starts = st.sidebar.slider("Minimum starts", 1, 30, 8)
        filtered_pitchers = pitcher_roles[pitcher_roles['starts'] >= min_starts]
        role_desc = f"Starting Rotation ({min_starts}+ starts)"
    elif pitcher_role == "Relievers Only":
        min_relief = st.sidebar.slider("Minimum relief appearances", 1, 50, 10)
        filtered_pitchers = pitcher_roles[
            (pitcher_roles['relief_games'] >= min_relief) & 
            (pitcher_roles['starts'] < 5)
        ]
        role_desc = f"Bullpen ({min_relief}+ relief apps)"
    else:  # All Pitchers
        min_games = st.sidebar.slider("Minimum total appearances", 1, 50, 8)
        filtered_pitchers = pitcher_roles[pitcher_roles['total_games'] >= min_games]
        role_desc = f"Pitching Staff ({min_games}+ apps)"
    
    filtered_pitcher_list = filtered_pitchers['player_name'].unique()
    
    # Filter the data to include only the selected pitchers
    filtered_data = dbacks_pitching_data[dbacks_pitching_data['player_name'].isin(filtered_pitcher_list)]
    
    return filtered_data, filtered_pitchers, role_desc

# Sidebar with enhanced filters
st.sidebar.header("🎛️ Analysis Controls")

# Add data freshness indicator
if not dbacks_data.empty:
    latest_date = pd.to_datetime(dbacks_data['game_date']).max().strftime('%B %d, %Y')
    total_games = dbacks_data['game_pk'].nunique()
    st.sidebar.success(f"📊 Data current through {latest_date} ({total_games} games)")

# Enhanced date range filters
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

# Add advanced analysis toggles
st.sidebar.markdown("---")
st.sidebar.subheader("📈 Advanced Metrics")
show_percentiles = st.sidebar.checkbox("Show League Percentiles", True)
show_movement = st.sidebar.checkbox("Show Pitch Movement", True)
show_performance = st.sidebar.checkbox("Show Performance Metrics", True)

# Filter data by date range
filtered_data = dbacks_data[
    (pd.to_datetime(dbacks_data['game_date']).dt.date >= start_date) &
    (pd.to_datetime(dbacks_data['game_date']).dt.date <= end_date)
]

# Process the filtered data with enhancements
pitcher_data, pitcher_appearances, role_description = process_enhanced_pitching_data(filtered_data)

if pitcher_data.empty:
    st.warning("No data available for the selected filters. Please adjust your criteria.")
    st.stop()

# Calculate enhanced pitch usage with efficiency metrics
def calculate_pitch_metrics(data):
    """Calculate comprehensive pitch metrics"""
    metrics = data.groupby(['player_name', 'pitch_name']).agg({
        'pitch_name': 'count',  # Total pitches
        'release_speed': ['mean', 'std'],
        'strike': 'sum',
        'ball': 'sum', 
        'called_strike': 'sum',
        'swinging_strike': 'sum',
        'whiff': 'sum',
        'contact': 'sum',
        'events': lambda x: (x.notna() & (x != '')).sum(),  # Balls in play
        'woba_value': 'mean',
        'launch_speed': 'mean',
        'launch_angle': 'mean'
    }).reset_index()
    
    # Flatten column names
    metrics.columns = ['player_name', 'pitch_name', 'count', 'avg_velo', 'velo_std', 
                      'strikes', 'balls', 'called_strikes', 'swinging_strikes', 
                      'whiffs', 'contact', 'balls_in_play', 'avg_woba', 'avg_exit_velo', 'avg_launch_angle']
    
    # Calculate rates
    metrics['strike_rate'] = metrics['strikes'] / metrics['count'] * 100
    metrics['whiff_rate'] = metrics['whiffs'] / metrics['count'] * 100
    metrics['called_strike_rate'] = metrics['called_strikes'] / metrics['count'] * 100
    
    return metrics

pitch_metrics = calculate_pitch_metrics(pitcher_data)

# Create enhanced pitch usage visualization
pitch_counts = pitch_metrics.groupby(['player_name', 'pitch_name'])['count'].sum().reset_index()
pitch_usage = pitch_counts.pivot(index='player_name', columns='pitch_name', values='count').fillna(0)
total_pitch_counts = pitch_usage.sum()
sorted_pitch_columns = total_pitch_counts.sort_values(ascending=False).index
pitch_usage = pitch_usage[sorted_pitch_columns]
pitch_percentages = pitch_usage.div(pitch_usage.sum(axis=1), axis=0) * 100

# Sort pitchers with enhanced labeling
sorted_pitchers = pitcher_appearances.sort_values(['starts', 'relief_games'], ascending=[False, False])
enhanced_pitcher_labels = []

for _, row in sorted_pitchers.iterrows():
    name = row['player_name']
    if row['starts'] >= 5:
        label = f"{name} ({int(row['starts'])} starts)"
    elif row['relief_games'] >= 5:
        label = f"{name} ({int(row['relief_games'])} relief)"
    else:
        label = f"{name} ({int(row['total_games'])} games)"
    enhanced_pitcher_labels.append(label)

pitch_percentages = pitch_percentages.loc[sorted_pitchers['player_name']]

# Main visualization
st.header(f"🎯 Pitch Type Distribution - {role_description}")

# Create enhanced interactive stacked bar chart
fig = go.Figure()

# Define colors for pitch types
pitch_colors = {
    '4-Seam Fastball': '#FF6B6B',
    'Sinker': '#4ECDC4', 
    'Slider': '#45B7D1',
    'Changeup': '#96CEB4',
    'Curveball': '#FECA57',
    'Cutter': '#FF9FF3',
    'Sweeper': '#54A0FF',
    'Splitter': '#5F27CD',
    'Knuckle Curve': '#00D2D3',
    'Other': '#C7ECEE'
}

for pitch_type in pitch_percentages.columns:
    color = pitch_colors.get(pitch_type, pitch_colors['Other'])
    fig.add_trace(go.Bar(
        name=pitch_type,
        y=enhanced_pitcher_labels,
        x=pitch_percentages[pitch_type],
        orientation='h',
        marker_color=color,
        hovertemplate=f"<b>%{{y}}</b><br>{pitch_type}: %{{x:.1f}}%<extra></extra>"
    ))

fig.update_layout(
    barmode='stack',
    title=dict(
        text=f'Pitch Type Distribution - {role_description}',
        font=dict(size=18)
    ),
    xaxis_title='Usage Percentage (%)',
    yaxis_title='Pitcher',
    height=max(400, len(enhanced_pitcher_labels) * 25),
    showlegend=True,
    legend_title='Pitch Type',
    yaxis={'categoryorder': 'total ascending'},
    hovermode='closest'
)

fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
st.plotly_chart(fig, use_container_width=True)

# Enhanced metrics section
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_pitchers = len(pitcher_appearances)
    st.metric("Pitchers Analyzed", total_pitchers)
    
with col2:
    total_pitches = len(pitcher_data)
    st.metric("Total Pitches", f"{total_pitches:,}")
    
with col3:
    games_analyzed = pitcher_data['game_pk'].nunique()
    st.metric("Games Analyzed", games_analyzed)
    
with col4:
    date_span = (end_date - start_date).days + 1
    st.metric("Date Range", f"{date_span} days")

# Individual Pitcher Analysis with Enhancements
st.markdown("---")
st.header("🔍 Individual Pitcher Deep Dive")

available_pitchers = sorted(pitcher_data['player_name'].unique())
selected_pitcher = st.selectbox("Select a pitcher for detailed analysis", available_pitchers)

if selected_pitcher:
    pitcher_specific_data = pitcher_data[pitcher_data['player_name'] == selected_pitcher].copy()
    pitcher_specific_data['game_date'] = pd.to_datetime(pitcher_specific_data['game_date'])
    
    # Create tabs for different analyses
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Pitch Mix Trends", "⚡ Velocity Analysis", "🎯 Command Metrics", "📈 Performance"])
    
    with tab1:
        # Enhanced pitch mix over time
        pitch_dates = pitcher_specific_data.groupby(['game_date', 'pitch_name']).size().reset_index(name='count')
        pitch_dates_pivot = pitch_dates.pivot(index='game_date', columns='pitch_name', values='count').fillna(0)
        
        # Calculate rolling average for trend analysis
        window_size = min(7, len(pitch_dates_pivot))
        if window_size > 1:
            rolling_mix = pitch_dates_pivot.rolling(window=window_size, min_periods=1, center=True).sum()
            rolling_percentages = rolling_mix.div(rolling_mix.sum(axis=1), axis=0) * 100
        else:
            rolling_percentages = pitch_dates_pivot.div(pitch_dates_pivot.sum(axis=1), axis=0) * 100
        
        # Enhanced time series plot
        fig_time = go.Figure()
        
        for pitch_type in rolling_percentages.columns:
            color = pitch_colors.get(pitch_type, pitch_colors['Other'])
            fig_time.add_trace(go.Scatter(
                x=rolling_percentages.index,
                y=rolling_percentages[pitch_type],
                name=pitch_type,
                mode='lines+markers',
                line=dict(width=3, color=color),
                marker=dict(size=6),
                hovertemplate=f"<b>%{{y:.1f}}%</b> {pitch_type}<br>%{{x|%B %d}}<extra></extra>"
            ))
        
        fig_time.update_layout(
            title=f'Pitch Mix Evolution - {selected_pitcher}',
            xaxis_title='Date',
            yaxis_title='Usage Percentage (%)',
            hovermode='x unified',
            height=500,
            showlegend=True,
            yaxis=dict(range=[0, 100], ticksuffix='%')
        )
        
        st.plotly_chart(fig_time, use_container_width=True)
    
    with tab2:
        # Velocity analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Velocity by Pitch Type")
            velo_stats = pitcher_specific_data.groupby('pitch_name')['release_speed'].agg(['mean', 'min', 'max', 'std']).reset_index()
            velo_stats.columns = ['Pitch Type', 'Avg. Velocity', 'Min', 'Max', 'Std Dev']
            velo_stats = velo_stats.sort_values('Avg. Velocity', ascending=False)
            
            # Create velocity chart
            fig_velo = go.Figure()
            
            for _, row in velo_stats.iterrows():
                pitch_type = row['Pitch Type']
                avg_velo = row['Avg. Velocity']
                min_velo = row['Min']
                max_velo = row['Max']
                
                fig_velo.add_trace(go.Scatter(
                    x=[pitch_type],
                    y=[avg_velo],
                    error_y=dict(
                        type='data',
                        symmetric=False,
                        array=[max_velo - avg_velo],
                        arrayminus=[avg_velo - min_velo]
                    ),
                    mode='markers',
                    marker=dict(size=12, color=pitch_colors.get(pitch_type, pitch_colors['Other'])),
                    name=pitch_type,
                    showlegend=False
                ))
            
            fig_velo.update_layout(
                title="Velocity Ranges by Pitch Type",
                xaxis_title="Pitch Type",
                yaxis_title="Velocity (mph)",
                height=400
            )
            
            st.plotly_chart(fig_velo, use_container_width=True)
            st.dataframe(velo_stats.round(1))
        
        with col2:
            st.subheader("Velocity Trends Over Time")
            
            # Velocity over time
            pitcher_velo_time = pitcher_specific_data.groupby(['game_date', 'pitch_name'])['release_speed'].mean().reset_index()
            
            fig_velo_time = px.line(
                pitcher_velo_time, 
                x='game_date', 
                y='release_speed',
                color='pitch_name',
                title=f"Velocity Trends - {selected_pitcher}",
                color_discrete_map=pitch_colors
            )
            
            fig_velo_time.update_layout(
                xaxis_title="Date",
                yaxis_title="Average Velocity (mph)",
                height=400
            )
            
            st.plotly_chart(fig_velo_time, use_container_width=True)
    
    with tab3:
        # Command and control metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Strike Zone Command")
            command_stats = pitch_metrics[pitch_metrics['player_name'] == selected_pitcher]
            
            if not command_stats.empty:
                command_display = command_stats[['pitch_name', 'strike_rate', 'called_strike_rate', 'whiff_rate']].copy()
                command_display.columns = ['Pitch Type', 'Strike Rate (%)', 'Called Strike Rate (%)', 'Whiff Rate (%)']
                command_display = command_display.sort_values('Strike Rate (%)', ascending=False)
                st.dataframe(command_display.round(1))
        
        with col2:
            st.subheader("Location Analysis")
            
            # Zone analysis
            if 'zone' in pitcher_specific_data.columns:
                zone_data = pitcher_specific_data['zone'].value_counts().reset_index()
                zone_data.columns = ['Zone', 'Count']
                
                fig_zone = px.bar(zone_data, x='Zone', y='Count', 
                                title="Pitch Location Distribution")
                st.plotly_chart(fig_zone, use_container_width=True)
    
    with tab4:
        # Performance metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Outcome Analysis")
            
            # Calculate performance by pitch type
            outcome_stats = pitcher_specific_data.groupby('pitch_name').agg({
                'woba_value': 'mean',
                'launch_speed': 'mean', 
                'launch_angle': 'mean',
                'events': lambda x: (x.notna() & (x != '')).sum()
            }).reset_index()
            
            outcome_stats.columns = ['Pitch Type', 'Avg wOBA', 'Avg Exit Velo', 'Avg Launch Angle', 'Balls in Play']
            outcome_stats = outcome_stats.round(3)
            st.dataframe(outcome_stats)
        
        with col2:
            st.subheader("Recent Performance")
            
            # Performance over last 10 games
            recent_games = pitcher_specific_data.nlargest(10, 'game_date')
            if not recent_games.empty:
                recent_performance = recent_games.groupby('game_date').agg({
                    'pitch_name': 'count',
                    'strike': 'sum',
                    'whiff': 'sum',
                    'woba_value': 'mean'
                }).reset_index()
                
                recent_performance['strike_rate'] = (recent_performance['strike'] / recent_performance['pitch_name'] * 100).round(1)
                recent_performance['whiff_rate'] = (recent_performance['whiff'] / recent_performance['pitch_name'] * 100).round(1)
                
                recent_display = recent_performance[['game_date', 'pitch_name', 'strike_rate', 'whiff_rate', 'woba_value']]
                recent_display.columns = ['Date', 'Pitches', 'Strike Rate (%)', 'Whiff Rate (%)', 'Avg wOBA']
                st.dataframe(recent_display.round(3))

# Team-wide Analysis
st.markdown("---")  
st.header("🏆 Team-wide Advanced Analytics")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Pitcher Efficiency Rankings")
    
    # Calculate efficiency metrics per pitcher
    efficiency_stats = pitch_metrics.groupby('player_name').agg({
        'count': 'sum',
        'strikes': 'sum',
        'whiffs': 'sum',
        'avg_velo': 'mean',
        'avg_woba': 'mean'
    }).reset_index()
    
    efficiency_stats['strike_rate'] = (efficiency_stats['strikes'] / efficiency_stats['count'] * 100).round(1)
    efficiency_stats['whiff_rate'] = (efficiency_stats['whiffs'] / efficiency_stats['count'] * 100).round(1)
    
    # Merge with appearance data
    efficiency_with_apps = pd.merge(efficiency_stats, pitcher_appearances, on='player_name')
    efficiency_display = efficiency_with_apps[efficiency_with_apps['total_games'] >= 5].copy()
    efficiency_display = efficiency_display[['player_name', 'total_games', 'count', 'strike_rate', 'whiff_rate', 'avg_woba']]
    efficiency_display.columns = ['Pitcher', 'Games', 'Total Pitches', 'Strike Rate (%)', 'Whiff Rate (%)', 'Avg wOBA Against']
    efficiency_display = efficiency_display.sort_values('Strike Rate (%)', ascending=False)
    
    st.dataframe(efficiency_display.round(3))

with col2:
    st.subheader("Pitch Type Effectiveness")
    
    # Team-wide pitch type performance
    team_pitch_performance = pitch_metrics.groupby('pitch_name').agg({
        'count': 'sum',
        'avg_velo': 'mean',
        'strike_rate': 'mean',
        'whiff_rate': 'mean',
        'avg_woba': 'mean'
    }).reset_index()
    
    team_pitch_performance = team_pitch_performance.sort_values('count', ascending=False)
    team_pitch_performance.columns = ['Pitch Type', 'Total Thrown', 'Avg Velocity', 'Strike Rate (%)', 'Whiff Rate (%)', 'wOBA Against']
    
    st.dataframe(team_pitch_performance.round(2))

# League context if available
if league_data is not None and show_percentiles:
    st.markdown("---")
    st.header("📊 League Context & Rankings")
    
    # Find Arizona in league data
    az_team_data = league_data[league_data['Team'].str.contains('ARI|Arizona|Diamondbacks', case=False, na=False)]
    
    if not az_team_data.empty:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("League ERA Rank", "Loading...")
        with col2:
            st.metric("League K/9 Rank", "Loading...")  
        with col3:
            st.metric("League WHIP Rank", "Loading...")
            
        st.info("League comparison data loaded successfully!")
    else:
        st.warning("Arizona Diamondbacks data not found in league context.")

# Data summary
st.markdown("---")
st.subheader("📋 Analysis Summary")

summary_text = f"""
### Key Insights from {role_description}:

**Data Coverage:**
- **Date Range**: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}
- **Games Analyzed**: {games_analyzed}
- **Total Pitches**: {total_pitches:,}
- **Pitchers**: {total_pitchers}

**Most Used Pitch Types:**
"""

# Add top 3 pitch types
top_pitches = total_pitch_counts.head(3)
for i, (pitch_type, count) in enumerate(top_pitches.items(), 1):
    percentage = (count / total_pitch_counts.sum() * 100)
    summary_text += f"\n{i}. **{pitch_type}**: {count:,} pitches ({percentage:.1f}%)"

st.markdown(summary_text)

# Footer
st.markdown("---")
st.markdown("*Enhanced with pybaseball integration • Data from MLB Statcast*")
