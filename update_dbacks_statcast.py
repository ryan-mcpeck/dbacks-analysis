#!/usr/bin/env python3
"""
Script to update the Diamondbacks team statcast CSV file.
This script handles data corrections by using a full refresh approach
with a lookback window to capture late-arriving MLB data updates.

Features:
- Smart update frequency control (weekly recommended)
- Full refresh with lookback window to capture data corrections
- Automatic backup creation with timestamp
- Duplicate detection and removal
- Efficient data preservation for older games

Usage: python update_dbacks_statcast.py
"""

import sys
import os
import pandas as pd
from datetime import datetime, date, timedelta
import glob

# Add the pybaseball directory to the path
sys.path.insert(0, r'c:\Users\valak\GitHub Repos\pybaseball')

import pybaseball as pyb

def count_csv_rows(filepath):
    """Count the number of rows in a CSV file (excluding header)."""
    try:
        df = pd.read_csv(filepath)
        return len(df)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return 0

def get_last_game_date(filepath):
    """Get the most recent game date from the CSV file."""
    try:
        df = pd.read_csv(filepath)
        if 'game_date' in df.columns and not df.empty:
            # Convert to datetime and get the max date
            df['game_date'] = pd.to_datetime(df['game_date'])
            return df['game_date'].max().strftime('%Y-%m-%d')
        return None
    except Exception as e:
        print(f"Error reading last game date: {e}")
        return None

def should_update(last_update_date, min_days_between_updates=7):
    """Check if enough time has passed since last update."""
    if last_update_date is None:
        return True
    
    last_date = datetime.strptime(last_update_date, '%Y-%m-%d')
    days_since_update = (datetime.now() - last_date).days
    
    return days_since_update >= min_days_between_updates

def get_season_start_date():
    """Get the start date for the current season."""
    current_year = datetime.now().year
    return f"{current_year}-03-20"  # Spring training/early season

def verify_csv_file(filepath):
    """Verify that the CSV file is valid and readable."""
    try:
        df = pd.read_csv(filepath)
        
        # Basic checks
        if df.empty:
            return False, "File is empty"
        
        # Check for required columns
        required_columns = ['pitch_type', 'game_date', 'player_name', 'batter', 'pitcher']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing required columns: {missing_columns}"
        
        # Check data types and basic integrity
        if 'game_date' in df.columns:
            try:
                pd.to_datetime(df['game_date'])
            except:
                return False, "Invalid game_date format"
        
        # Check for reasonable data
        if len(df) < 100:  # Expect at least 100 pitches for any meaningful dataset
            return False, f"Suspiciously low row count: {len(df)}"
        
        return True, f"File verified successfully: {len(df):,} rows, {len(df.columns)} columns"
        
    except Exception as e:
        return False, f"Verification failed: {str(e)}"

def main():
    csv_file = r'c:\Users\valak\GitHub Repos\dbacks-analysis\dbacks_team_statcast.csv'
    
    print("=== Diamondbacks Statcast Data Update ===")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if file exists
    if not os.path.exists(csv_file):
        print("❌ CSV file not found. Run initial data fetch first.")
        return
    
    # Count existing rows and get last update date
    existing_rows = count_csv_rows(csv_file)
    last_game_date = get_last_game_date(csv_file)
    
    print(f"📊 Current CSV has {existing_rows:,} rows")
    print(f"📅 Last game date in data: {last_game_date}")
    
    # Check if update is needed (configurable)
    MIN_DAYS_BETWEEN_UPDATES = 7  # Weekly updates recommended
    
    if last_game_date and not should_update(last_game_date, MIN_DAYS_BETWEEN_UPDATES):
        days_since = (datetime.now() - datetime.strptime(last_game_date, '%Y-%m-%d')).days
        print(f"⏳ Last update was {days_since} days ago. Minimum interval is {MIN_DAYS_BETWEEN_UPDATES} days.")
        print("ℹ️  No update needed. Change MIN_DAYS_BETWEEN_UPDATES in script to override.")
        return
    
    # Always do a full refresh to capture data corrections
    # Use a lookback window to ensure we capture any late-arriving updates
    LOOKBACK_DAYS = 14  # Refetch data from last 2 weeks to catch corrections
    
    if last_game_date:
        # Start from 2 weeks before the last game to catch any data corrections
        lookback_date = datetime.strptime(last_game_date, '%Y-%m-%d') - timedelta(days=LOOKBACK_DAYS)
        start_date = max(lookback_date, datetime.strptime(get_season_start_date(), '%Y-%m-%d')).strftime('%Y-%m-%d')
        print(f"🔄 Full refresh with {LOOKBACK_DAYS}-day lookback: fetching from {start_date}")
        print("   (This ensures we capture any late-arriving data corrections)")
    else:
        # Fallback to season start
        start_date = get_season_start_date()
        print(f"🔄 Full season update: fetching data from {start_date}")
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"📡 Fetching complete dataset from {start_date} to {end_date}")
    
    try:
        # Enable caching for large requests
        pyb.cache.enable()
        
        # Fetch the complete updated dataset
        updated_data = pyb.statcast(start_dt=start_date, end_dt=end_date, team='AZ')
        
        if updated_data is None or updated_data.empty:
            print("ℹ️  No data available for the specified date range.")
            return
        
        print(f"📥 Retrieved {len(updated_data):,} rows of data")
        
        # For full refresh, we need to merge with data outside our refresh window
        print("🔄 Performing full refresh with data integrity preservation...")
        
        existing_data = pd.read_csv(csv_file)
        
        if start_date > get_season_start_date():
            # Keep data from before our refresh window
            existing_data['game_date'] = pd.to_datetime(existing_data['game_date'])
            cutoff_date = datetime.strptime(start_date, '%Y-%m-%d')
            
            # Keep old data that's outside our refresh window
            old_data = existing_data[existing_data['game_date'] < cutoff_date]
            print(f"📦 Preserving {len(old_data):,} rows from before {start_date}")
            
            # Combine old data with new refreshed data
            if not old_data.empty:
                # Convert back to string for consistency
                old_data['game_date'] = old_data['game_date'].dt.strftime('%Y-%m-%d')
                final_data = pd.concat([old_data, updated_data], ignore_index=True)
            else:
                final_data = updated_data
        else:
            # Complete season refresh
            final_data = updated_data
        
        # Sort by date and game order for consistency
        final_data['game_date'] = pd.to_datetime(final_data['game_date'])
        final_data = final_data.sort_values(['game_date', 'game_pk', 'at_bat_number', 'pitch_number'])
        final_data['game_date'] = final_data['game_date'].dt.strftime('%Y-%m-%d')
        
        # Remove any potential duplicates (shouldn't happen, but safety first)
        before_dedup = len(final_data)
        final_data = final_data.drop_duplicates(
            subset=['game_pk', 'at_bat_number', 'pitch_number'], 
            keep='last'
        )
        after_dedup = len(final_data)
        
        if before_dedup != after_dedup:
            print(f"🧹 Removed {before_dedup - after_dedup} duplicate rows")
        
        # Create backup with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = csv_file.replace('.csv', f'_backup_{timestamp}.csv')
        if os.path.exists(csv_file):
            print(f"💾 Creating backup: {os.path.basename(backup_file)}")
            os.rename(csv_file, backup_file)
        
        # Save updated data
        print(f"💿 Saving updated data...")
        final_data.to_csv(csv_file, index=False)
        
        # Verify the updated file
        print(f"🔍 Verifying updated file...")
        is_valid, verification_msg = verify_csv_file(csv_file)
        
        if not is_valid:
            print(f"❌ Verification failed: {verification_msg}")
            # Restore backup if verification fails
            if os.path.exists(backup_file):
                print(f"🔄 Restoring backup due to verification failure...")
                os.remove(csv_file)
                os.rename(backup_file, csv_file)
                print(f"✅ Backup restored successfully")
            return
        
        print(f"✅ Verification passed: {verification_msg}")
        
        # Report results
        new_rows = len(final_data)
        rows_added = new_rows - existing_rows
        print(f"📊 Updated CSV has {new_rows:,} rows")
        
        if rows_added > 0:
            print(f"📈 Added {rows_added:+,} new rows")
        elif rows_added < 0:
            print(f"📉 Data refreshed: {abs(rows_added):,} fewer rows (likely due to data corrections)")
        else:
            print(f"🔄 Data refreshed: same row count (data corrections applied)")
        
        # Show date range of updated data
        if 'game_date' in final_data.columns:
            min_date = final_data['game_date'].min()
            max_date = final_data['game_date'].max()
            print(f"📅 Data now covers: {min_date} to {max_date}")
        
        print("🎉 Update completed successfully!")
        print(f"ℹ️  Note: Used {LOOKBACK_DAYS}-day lookback to capture any late-arriving data corrections")
        
        # Remove the current backup since update was successful
        if os.path.exists(backup_file):
            print(f"🗑️  Removing current backup: {os.path.basename(backup_file)}")
            os.remove(backup_file)
        
        # Suggest next update
        next_update = datetime.now() + timedelta(days=MIN_DAYS_BETWEEN_UPDATES)
        print(f"💡 Next suggested update: {next_update.strftime('%Y-%m-%d')}")
        
        # Clean up old backups (keep only the 2 most recent, since we removed current one)
        try:
            backup_pattern = csv_file.replace('.csv', '_backup_*.csv')
            backup_files = glob.glob(backup_pattern)
            if len(backup_files) > 2:
                backup_files.sort()
                for old_backup in backup_files[:-2]:
                    os.remove(old_backup)
                    print(f"🗑️  Cleaned up old backup: {os.path.basename(old_backup)}")
        except Exception as e:
            print(f"⚠️  Could not clean up old backups: {e}")
        
    except Exception as e:
        print(f"❌ Error during update: {e}")
        # If there was an error and we created a backup, restore the most recent one
        # First check if current backup exists
        if 'backup_file' in locals() and os.path.exists(backup_file):
            print(f"🔄 Restoring current backup: {os.path.basename(backup_file)}")
            if os.path.exists(csv_file):
                os.remove(csv_file)
            os.rename(backup_file, csv_file)
        else:
            # Fall back to most recent timestamped backup
            backup_pattern = csv_file.replace('.csv', '_backup_*.csv')
            backup_files = glob.glob(backup_pattern)
            if backup_files and not os.path.exists(csv_file):
                # Restore the most recent backup
                latest_backup = max(backup_files, key=os.path.getctime)
                print(f"🔄 Restoring latest backup: {os.path.basename(latest_backup)}")
                os.rename(latest_backup, csv_file)

if __name__ == "__main__":
    main()
