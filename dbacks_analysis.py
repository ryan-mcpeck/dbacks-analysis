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
pitch_percentages = pitch_usage.div(pitch_usage.sum(axis=1), axis=0) * 100

# --- Visualization ---
print("Generating pitch usage visualization...")

# Create the stacked bar chart
ax = pitch_percentages.plot(
    kind='barh', 
    stacked=True, 
    figsize=(12, 8), 
    colormap='viridis'
)

# Set plot titles and labels
plt.title('Pitch Usage by Diamondbacks Starting Pitchers (2025)', fontsize=16)
plt.xlabel('Pitch Percentage (%)', fontsize=12)
plt.ylabel('Pitcher', fontsize=12)

# Move the legend outside the plot
plt.legend(title='Pitch Type', bbox_to_anchor=(1.02, 1), loc='upper left')

plt.tight_layout()
plt.show()

print("Visualization complete.")