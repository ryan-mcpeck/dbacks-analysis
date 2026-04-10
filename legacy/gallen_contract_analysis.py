"""
Zac Gallen 2026 Contract Decision Analysis
Uses 2025 season data to assess re-signing value
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Load data
df = pd.read_csv('dbacks_team_statcast.csv')

# Filter for Zac Gallen
gallen = df[df['player_name'].str.contains('Gallen', case=False, na=False)].copy()

print("=" * 60)
print("ZAC GALLEN 2026 CONTRACT ANALYSIS")
print("=" * 60)
print(f"\nTotal Pitches in 2025: {len(gallen):,}")

# 1. VELOCITY TRENDS (Injury Risk Assessment)
print("\n📊 VELOCITY ANALYSIS (Injury Risk Indicator)")
print("-" * 60)

gallen['game_date'] = pd.to_datetime(gallen['game_date'])
velocity_by_month = gallen.groupby(gallen['game_date'].dt.to_period('M'))['release_speed'].agg(['mean', 'std', 'count'])
velocity_by_month['mean'] = velocity_by_month['mean'].round(1)
velocity_by_month['std'] = velocity_by_month['std'].round(1)

print("\nMonthly Velocity Trends:")
print(velocity_by_month)

# Season average vs late season
season_avg_velo = gallen['release_speed'].mean()
late_season = gallen[gallen['game_date'] >= '2025-08-01']
late_season_velo = late_season['release_speed'].mean()
velo_drop = season_avg_velo - late_season_velo

print(f"\nSeason Average Velocity: {season_avg_velo:.1f} mph")
print(f"Late Season Velocity (Aug-Sep): {late_season_velo:.1f} mph")
print(f"Velocity Drop: {velo_drop:+.1f} mph")

if abs(velo_drop) > 2:
    print("🚨 WARNING: Velocity drop >2mph - INJURY RISK")
elif abs(velo_drop) > 1:
    print("⚠️  CAUTION: Noticeable velocity decline")
else:
    print("✅ HEALTHY: Maintained velocity through season")

# 2. PITCH ARSENAL EFFECTIVENESS
print("\n⚾ PITCH ARSENAL BREAKDOWN")
print("-" * 60)

arsenal = gallen.groupby('pitch_type').agg({
    'release_speed': 'mean',
    'description': lambda x: (x == 'swinging_strike').mean() * 100,
    'player_name': 'count'
}).rename(columns={
    'release_speed': 'avg_velo',
    'description': 'whiff_rate_%',
    'player_name': 'pitch_count'
})

arsenal = arsenal[arsenal['pitch_count'] >= 10]  # Min 10 pitches
arsenal['avg_velo'] = arsenal['avg_velo'].round(1)
arsenal['whiff_rate_%'] = arsenal['whiff_rate_%'].round(1)
arsenal = arsenal.sort_values('pitch_count', ascending=False)

print(arsenal)

# Overall whiff rate
overall_whiff = (gallen['description'] == 'swinging_strike').mean() * 100
print(f"\nOverall Whiff Rate: {overall_whiff:.1f}%")
print("Benchmark: Elite starters >25%, Good starters >20%")

# 3. HIGH-LEVERAGE PERFORMANCE (2-Strike Counts)
print("\n🎯 HIGH-LEVERAGE PERFORMANCE (2-Strike Counts)")
print("-" * 60)

two_strike = gallen[gallen['strikes'] == 2]
if len(two_strike) >= 20:
    strike_rate_2strike = (two_strike['description'].isin(['called_strike', 'swinging_strike'])).mean() * 100
    whiff_rate_2strike = (two_strike['description'] == 'swinging_strike').mean() * 100
    
    print(f"2-Strike Pitch Count: {len(two_strike)}")
    print(f"Strike Rate in 2-Strike: {strike_rate_2strike:.1f}%")
    print(f"Whiff Rate in 2-Strike: {whiff_rate_2strike:.1f}%")
    
    if strike_rate_2strike > 40:
        print("✅ ELITE: Dominates in high-leverage situations")
    elif strike_rate_2strike > 30:
        print("✅ GOOD: Strong performance in pressure")
    else:
        print("⚠️  CONCERN: Struggles to put hitters away")
else:
    print("Insufficient data for 2-strike analysis")

# 4. WORKLOAD & DURABILITY
print("\n💪 WORKLOAD & DURABILITY")
print("-" * 60)

games_pitched = gallen['game_pk'].nunique()
total_pitches = len(gallen)
avg_pitches_per_game = total_pitches / games_pitched if games_pitched > 0 else 0

print(f"Games Pitched: {games_pitched}")
print(f"Total Pitches: {total_pitches:,}")
print(f"Avg Pitches/Game: {avg_pitches_per_game:.1f}")

if games_pitched >= 30:
    print("✅ DURABLE: Full season workload")
elif games_pitched >= 25:
    print("✅ GOOD: Solid availability")
else:
    print("⚠️  CONCERN: Limited games pitched")

# 5. CONSISTENCY ANALYSIS
print("\n📈 CONSISTENCY ANALYSIS")
print("-" * 60)

# Game-by-game variance
game_stats = gallen.groupby('game_pk').agg({
    'release_speed': 'mean',
    'description': lambda x: (x == 'swinging_strike').mean() * 100
}).rename(columns={'description': 'whiff_rate'})

velo_std = game_stats['release_speed'].std()
whiff_std = game_stats['whiff_rate'].std()

print(f"Game-to-Game Velocity Std Dev: {velo_std:.2f} mph")
print(f"Game-to-Game Whiff Rate Std Dev: {whiff_std:.2f}%")

if velo_std < 1.5:
    print("✅ CONSISTENT: Low velocity variance")
else:
    print("⚠️  INCONSISTENT: High velocity variance")

# 6. FINAL RECOMMENDATION
print("\n" + "=" * 60)
print("🎯 RE-SIGNING RECOMMENDATION")
print("=" * 60)

# Score the factors (0-10 scale)
health_score = 10 if abs(velo_drop) <= 1 else (8 if abs(velo_drop) <= 2 else 3)
effectiveness_score = 10 if overall_whiff > 25 else (7 if overall_whiff > 20 else 4)
durability_score = 10 if games_pitched >= 30 else (7 if games_pitched >= 25 else 4)
consistency_score = 10 if velo_std < 1.5 else (6 if velo_std < 2.0 else 3)

total_score = (health_score + effectiveness_score + durability_score + consistency_score) / 4

print(f"\nHealth/Injury Risk:  {health_score}/10")
print(f"Effectiveness:       {effectiveness_score}/10")
print(f"Durability:          {durability_score}/10")
print(f"Consistency:         {consistency_score}/10")
print(f"\nOVERALL SCORE:       {total_score:.1f}/10")

if total_score >= 8:
    recommendation = "✅ STRONG YES - Elite starter, offer competitive contract"
elif total_score >= 6:
    recommendation = "✅ YES - Solid starter, reasonable multi-year deal"
elif total_score >= 4:
    recommendation = "⚠️  CONDITIONAL - 1-2 year deal with incentives"
else:
    recommendation = "❌ NO - Significant concerns, explore alternatives"

print(f"\nRECOMMENDATION: {recommendation}")

# Contract value context
print("\n💰 MARKET CONTEXT")
print("-" * 60)
print("2026 Starting Pitcher Market (estimated):")
print("- Elite (8.5-10): $25-35M AAV, 5-7 years")
print("- Good (6.5-8.4): $15-25M AAV, 3-5 years")
print("- Average (5-6.4): $8-15M AAV, 2-3 years")
print("- Risk (4-4.9): $5-10M AAV, 1-2 years")

print("\n" + "=" * 60)
print("Analysis complete! Review metrics above for decision support.")
print("=" * 60)
