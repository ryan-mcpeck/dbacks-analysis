import pandas as pd
from pybaseball import statcast

# Get data for all D-backs batters for the 2024 season
# Note: This can take a minute or two to download
print("Fetching data...")
dbacks_data = statcast('2024-03-28', '2024-07-11', team='AZ')
print("Data fetched successfully!")
print(dbacks_data.head())