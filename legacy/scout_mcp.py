from fastmcp import FastMCP
import pandas as pd
import os

# Initialize the Scout Agent
mcp = FastMCP("Dbacks Scout")

# Load your existing professional dataset
csv_path = "dbacks_team_statcast.csv"
if not os.path.exists(csv_path):
    raise FileNotFoundError(f"Data file not found: {csv_path}")

df = pd.read_csv(csv_path)

@mcp.tool()
def get_pitcher_arsenal(pitcher_name: str) -> str:
    """Returns the velocity and whiff rate for a specific pitcher's arsenal."""
    pitcher_data = df[df['player_name'].str.contains(pitcher_name, case=False, na=False)]
    
    if pitcher_data.empty:
        return f"No data found for pitcher: {pitcher_name}"
    
    # Minimum 10 pitches per pitch type for meaningful stats
    stats = pitcher_data.groupby('pitch_type').filter(lambda x: len(x) >= 10).groupby('pitch_type').agg({
        'release_speed': 'mean',
        'description': lambda x: (x == 'swinging_strike').mean() * 100,
        'player_name': 'count'
    }).rename(columns={'description': 'whiff_rate_percent', 'player_name': 'pitch_count'})
    
    # Round velocity for readability
    stats['release_speed'] = stats['release_speed'].round(1)
    stats['whiff_rate_percent'] = stats['whiff_rate_percent'].round(1)
    
    return f"Arsenal for {pitcher_data['player_name'].iloc[0]}:\n\n{stats.to_string()}"

@mcp.tool()
def analyze_high_leverage() -> str:
    """Finds which pitchers are performing best in high-leverage (2-strike) counts."""
    two_strike_data = df[df['strikes'] == 2]
    
    # Filter pitchers with minimum 20 two-strike pitches for meaningful stats
    pitcher_counts = two_strike_data.groupby('player_name').size()
    qualified_pitchers = pitcher_counts[pitcher_counts >= 20].index
    two_strike_data = two_strike_data[two_strike_data['player_name'].isin(qualified_pitchers)]
    
    if two_strike_data.empty:
        return "No qualified pitchers found in two-strike situations."
    
    # Effectiveness metric: (Strikeouts + Called Strikes) / Total Pitches
    # Excludes fouls which don't end at-bats
    effectiveness = two_strike_data.groupby('player_name')['description'].apply(
        lambda x: (x.isin(['called_strike', 'swinging_strike'])).mean() * 100
    ).sort_values(ascending=False).head(5)
    
    effectiveness = effectiveness.round(1)
    
    return f"Top 5 Pitchers in 2-Strike Situations (Strike %):\n\n{effectiveness.to_string()}"

@mcp.tool()
def evaluate_pitcher_contract(pitcher_name: str) -> str:
    """Comprehensive contract evaluation for a pitcher including health, effectiveness, durability, and recommendation."""
    pitcher_data = df[df['player_name'].str.contains(pitcher_name, case=False, na=False)].copy()
    
    if pitcher_data.empty:
        return f"No data found for pitcher: {pitcher_name}"
    
    if len(pitcher_data) < 100:
        return f"Insufficient data for contract analysis: only {len(pitcher_data)} pitches"
    
    full_name = pitcher_data['player_name'].iloc[0]
    result = [f"CONTRACT EVALUATION: {full_name}", "=" * 60, ""]
    
    # 1. Health/Injury Risk (velocity trends)
    pitcher_data['game_date'] = pd.to_datetime(pitcher_data['game_date'])
    season_avg_velo = pitcher_data['release_speed'].mean()
    late_season = pitcher_data[pitcher_data['game_date'] >= pitcher_data['game_date'].max() - pd.Timedelta(days=30)]
    late_season_velo = late_season['release_speed'].mean() if not late_season.empty else season_avg_velo
    velo_drop = season_avg_velo - late_season_velo
    
    result.append("📊 HEALTH/INJURY RISK:")
    result.append(f"Season Avg Velocity: {season_avg_velo:.1f} mph")
    result.append(f"Late Season Velocity: {late_season_velo:.1f} mph")
    result.append(f"Velocity Change: {velo_drop:+.1f} mph")
    
    health_score = 10 if abs(velo_drop) <= 1 else (8 if abs(velo_drop) <= 2 else 3)
    if abs(velo_drop) > 2:
        result.append("🚨 WARNING: Velocity drop >2mph - INJURY RISK")
    elif abs(velo_drop) > 1:
        result.append("⚠️  CAUTION: Noticeable velocity decline")
    else:
        result.append("✅ HEALTHY: Maintained velocity")
    result.append("")
    
    # 2. Effectiveness (whiff rate)
    overall_whiff = (pitcher_data['description'] == 'swinging_strike').mean() * 100
    result.append("⚾ EFFECTIVENESS:")
    result.append(f"Whiff Rate: {overall_whiff:.1f}%")
    result.append(f"Benchmark: Elite >25%, Good >20%")
    
    effectiveness_score = 10 if overall_whiff > 25 else (7 if overall_whiff > 20 else 4)
    if overall_whiff > 25:
        result.append("✅ ELITE strikeout stuff")
    elif overall_whiff > 20:
        result.append("✅ GOOD swing-and-miss ability")
    else:
        result.append("⚠️  BELOW AVERAGE whiff rate")
    result.append("")
    
    # 3. Durability
    games_pitched = pitcher_data['game_pk'].nunique()
    total_pitches = len(pitcher_data)
    
    result.append("💪 DURABILITY:")
    result.append(f"Games: {games_pitched}, Pitches: {total_pitches:,}")
    
    durability_score = 10 if games_pitched >= 30 else (7 if games_pitched >= 25 else 4)
    if games_pitched >= 30:
        result.append("✅ DURABLE: Full season workload")
    elif games_pitched >= 25:
        result.append("✅ GOOD availability")
    else:
        result.append("⚠️  LIMITED games")
    result.append("")
    
    # 4. Overall Score & Recommendation
    total_score = (health_score + effectiveness_score + durability_score) / 3
    
    result.append("🎯 OVERALL ASSESSMENT:")
    result.append(f"Score: {total_score:.1f}/10")
    
    if total_score >= 8:
        recommendation = "✅ STRONG YES - Offer competitive multi-year contract"
        value = "$25-35M AAV, 5-7 years"
    elif total_score >= 6:
        recommendation = "✅ YES - Reasonable multi-year deal"
        value = "$15-25M AAV, 3-5 years"
    elif total_score >= 4:
        recommendation = "⚠️  CONDITIONAL - Short-term deal with incentives"
        value = "$8-15M AAV, 1-2 years"
    else:
        recommendation = "❌ NO - Significant concerns"
        value = "Explore alternatives"
    
    result.append(f"Recommendation: {recommendation}")
    result.append(f"Est. Market Value: {value}")
    
    return "\n".join(result)

if __name__ == "__main__":
    mcp.run()