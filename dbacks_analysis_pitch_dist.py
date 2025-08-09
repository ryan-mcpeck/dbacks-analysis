import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the data from the local CSV file.
print("Loading data from dbacks_team_statcast.csv...")
dbacks_data = pd.read_csv('dbacks_team_statcast.csv')
print("Data loaded successfully!")

# Identify plays where the Diamondbacks were the pitching team
is_dbacks_pitching = ((dbacks_data['home_team'] == 'AZ') & (dbacks_data['inning_topbot'] == 'Top')) | \
                     ((dbacks_data['away_team'] == 'AZ') & (dbacks_data['inning_topbot'] == 'Bot'))
dbacks_pitching_data = dbacks_data[is_dbacks_pitching].copy()

# Identify the starting pitchers (those who pitched in the 1st inning)
first_inning_pitchers = dbacks_pitching_data[dbacks_pitching_data['inning'] == 1]

# Count the number of starts for each pitcher (unique games started)
starts_count = first_inning_pitchers.groupby('player_name')['game_pk'].nunique().reset_index(name='starts')

# Filter for pitchers with at least 10 starts
main_starters = starts_count[starts_count['starts'] >= 10]
main_starters_list = main_starters['player_name'].unique()

# Filter the data to include only the main starting pitchers
starter_data = dbacks_pitching_data[dbacks_pitching_data['player_name'].isin(main_starters_list)]

# Calculate pitch counts for each starter
pitch_counts = starter_data.groupby(['player_name', 'pitch_name']).size().reset_index(name='count')

# Pivot the data to get pitch usage percentages
pitch_usage = pitch_counts.pivot(index='player_name', columns='pitch_name', values='count').fillna(0)

# Calculate total counts for each pitch type across all pitchers
total_pitch_counts = pitch_usage.sum()
# Sort columns (pitch types) by total usage
sorted_pitch_columns = total_pitch_counts.sort_values(ascending=False).index

# Reorder the columns based on sorted pitch types
pitch_usage = pitch_usage[sorted_pitch_columns]
pitch_percentages = pitch_usage.div(pitch_usage.sum(axis=1), axis=0) * 100

# --- Visualization ---
print("Generating pitch usage visualization...")

# Sort pitchers by number of starts (descending)
sorted_main_starters = main_starters.sort_values('starts', ascending=False)
# Create labels with pitcher names and starts
pitcher_labels = [f"{name} ({starts} starts)" for name, starts in zip(sorted_main_starters['player_name'], sorted_main_starters['starts'])]
pitch_percentages = pitch_percentages.loc[sorted_main_starters['player_name']]

# Create the stacked bar chart
ax = pitch_percentages.plot(
    kind='barh', 
    stacked=True, 
    figsize=(12, 8), 
    colormap='viridis'
)

# Update y-axis labels with the number of starts
ax.set_yticklabels(pitcher_labels)

# Set plot titles and labels
plt.title('Pitch Usage by Diamondbacks Starting Pitchers (2025)', fontsize=16, pad=20)
plt.xlabel('Pitch Percentage (%)', fontsize=12)
plt.ylabel('Pitcher', fontsize=12)

# Add gridlines
plt.grid(axis='x', linestyle='--', alpha=0.7)

# Move the legend outside the plot
plt.legend(title='Pitch Type', bbox_to_anchor=(1.02, 1), loc='upper left', frameon=True)

# Adjust layout to prevent label cutoff
plt.subplots_adjust(right=0.85)

plt.tight_layout()
plt.show()

print("Visualization complete.")