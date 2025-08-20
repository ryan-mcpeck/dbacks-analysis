# Key improvements to add to your original dashboard.py

# 1. Enhanced Data Processing - Add these calculated fields
def enhance_statcast_data(data):
    """Add derived metrics to statcast data"""
    data['called_strike'] = ((data['type'] == 'S') & (data['description'] == 'called_strike')).astype(int)
    data['swinging_strike'] = ((data['type'] == 'S') & (data['description'] == 'swinging_strike')).astype(int)
    data['whiff'] = data['swinging_strike']
    data['strike'] = (data['type'] == 'S').astype(int)
    data['ball'] = (data['type'] == 'B').astype(int)
    return data

# 2. Better Role Classification
def classify_pitcher_roles(data):
    """More accurate pitcher role identification"""
    game_pitcher_stats = data.groupby(['game_pk', 'player_name']).agg({
        'inning': ['min', 'max'],
        'pitch_number': 'count',
    }).reset_index()
    
    game_pitcher_stats.columns = ['game_pk', 'player_name', 'first_inning', 'last_inning', 'total_pitches']
    game_pitcher_stats['is_starter'] = (game_pitcher_stats['first_inning'] == 1) & (game_pitcher_stats['total_pitches'] >= 50)
    game_pitcher_stats['is_reliever'] = game_pitcher_stats['first_inning'] > 1
    
    return game_pitcher_stats

# 3. Performance Metrics Calculation
def calculate_advanced_metrics(data):
    """Calculate pitch-level performance metrics"""
    return data.groupby(['player_name', 'pitch_name']).agg({
        'pitch_name': 'count',
        'release_speed': 'mean',
        'strike': 'sum',
        'whiff': 'sum',
        'woba_value': 'mean',
        'launch_speed': 'mean'
    }).reset_index()

# 4. Enhanced Visualizations
pitch_colors = {
    '4-Seam Fastball': '#FF6B6B',
    'Sinker': '#4ECDC4', 
    'Slider': '#45B7D1',
    'Changeup': '#96CEB4',
    'Curveball': '#FECA57',
    'Cutter': '#FF9FF3'
}

# 5. Tabbed Analysis Structure
tab1, tab2, tab3 = st.tabs(["Pitch Mix", "Velocity", "Performance"])

# 6. Add These Metrics to Your Sidebar
st.sidebar.subheader("Advanced Options")
show_advanced = st.sidebar.checkbox("Show Advanced Metrics", True)
show_trends = st.sidebar.checkbox("Show Trend Analysis", True)

# 7. Team-wide Performance Summary
def team_performance_summary(data):
    """Generate team-wide performance insights"""
    total_pitches = len(data)
    avg_velo = data['release_speed'].mean()
    strike_rate = (data['strike'].sum() / total_pitches * 100)
    
    return {
        'total_pitches': total_pitches,
        'avg_velocity': avg_velo,
        'strike_rate': strike_rate
    }
