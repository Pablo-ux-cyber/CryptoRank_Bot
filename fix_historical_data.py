import pandas as pd
import sys
import argparse
from datetime import datetime

def fix_historical_data(date_str=None, finance=None, apps=None, overall=None, interactive=True):
    """
    Fix the historical data CSV file based on user-provided corrections
    
    This script allows editing specific dates in the historical data
    with correct ranking values.
    
    Args:
        date_str (str): The date to correct in YYYY-MM-DD format
        finance (int): Correct ranking for iPhone - Free - Finance
        apps (int): Correct ranking for iPhone - Free - Apps
        overall (int): Correct ranking for iPhone - Free - Overall
        interactive (bool): Whether to run in interactive mode
    """
    try:
        # Load the historical data
        df = pd.read_csv('historical_data.csv')
        
        if interactive:
            # Print the current data
            print("Current historical data:")
            print(df)
            
            # Ask for the date to correct
            date_str = input("\nEnter the date to correct (YYYY-MM-DD) or 'q' to quit: ")
            if date_str.lower() == 'q':
                print("No changes made")
                return
        
        # Validate the date format
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            date_str = date.strftime('%Y-%m-%d')  # Normalize the format
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            return
        
        # Check if the date exists in the data
        if date_str not in df['date'].values:
            print(f"Date {date_str} not found in the data")
            return
        
        # Get the current values for the date
        current_row = df[df['date'] == date_str].iloc[0]
        print(f"\nCurrent values for {date_str}:")
        print(f"iPhone - Free - Finance: #{current_row['iPhone - Free - Finance']}")
        print(f"iPhone - Free - Apps: #{current_row['iPhone - Free - Apps']}")
        print(f"iPhone - Free - Overall: #{current_row['iPhone - Free - Overall']}")
        
        if interactive:
            # Get the corrected values
            try:
                finance_input = input("\nEnter the correct value for iPhone - Free - Finance (or press Enter to keep current): ")
                if finance_input.strip() == '':
                    finance = current_row['iPhone - Free - Finance']
                else:
                    finance = int(finance_input)
                    
                apps_input = input("Enter the correct value for iPhone - Free - Apps (or press Enter to keep current): ")
                if apps_input.strip() == '':
                    apps = current_row['iPhone - Free - Apps']
                else:
                    apps = int(apps_input)
                    
                overall_input = input("Enter the correct value for iPhone - Free - Overall (or press Enter to keep current): ")
                if overall_input.strip() == '':
                    overall = current_row['iPhone - Free - Overall']
                else:
                    overall = int(overall_input)
            except ValueError:
                print("Error: All values must be integers")
                return
        else:
            # Use provided values or keep current
            finance = finance if finance is not None else current_row['iPhone - Free - Finance']
            apps = apps if apps is not None else current_row['iPhone - Free - Apps']
            overall = overall if overall is not None else current_row['iPhone - Free - Overall']
        
        # Update the values in the dataframe
        df.loc[df['date'] == date_str, 'iPhone - Free - Finance'] = finance
        df.loc[df['date'] == date_str, 'iPhone - Free - Apps'] = apps
        df.loc[df['date'] == date_str, 'iPhone - Free - Overall'] = overall
        
        # Save the updated data
        df.to_csv('historical_data.csv', index=False)
        
        print("\nData updated successfully")
        print(f"Updated values for {date_str}:")
        print(f"iPhone - Free - Finance: #{finance}")
        print(f"iPhone - Free - Apps: #{apps}")
        print(f"iPhone - Free - Overall: #{overall}")
        
        # Also update the config.py file to include this as a known good rank
        update_config_known_ranks(date_str, finance, apps, overall)
        
    except Exception as e:
        print(f"Error: {e}")
        return

def update_config_known_ranks(date_str, finance, apps, overall):
    """Update the KNOWN_GOOD_RANKS dictionary in config.py"""
    import re
    
    try:
        with open('config.py', 'r') as f:
            config_content = f.read()
            
        # Check if this date is already in the KNOWN_GOOD_RANKS
        date_pattern = f"'{date_str}'"
        if date_pattern in config_content:
            # Update existing entry
            pattern = r"'{}'\s*:\s*\{{[^}}]*\}}".format(date_str)
            replacement = f"'{date_str}': {{\n        'iPhone - Free - Finance': {finance},\n        'iPhone - Free - Apps': {apps},\n        'iPhone - Free - Overall': {overall}\n    }}"
            config_content = re.sub(pattern, replacement, config_content)
        else:
            # Add new entry
            pattern = r"KNOWN_GOOD_RANKS\s*=\s*\{[^\}]*"
            replacement = f"KNOWN_GOOD_RANKS = {{\n    # Format: 'date': {{'category': rank}}\n    '{date_str}': {{\n        'iPhone - Free - Finance': {finance},\n        'iPhone - Free - Apps': {apps},\n        'iPhone - Free - Overall': {overall}\n    }},"
            config_content = re.sub(pattern, replacement, config_content)
            
        with open('config.py', 'w') as f:
            f.write(config_content)
            
        print(f"Updated config.py with known good ranks for {date_str}")
    except Exception as e:
        print(f"Warning: Could not update config.py: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fix historical SensorTower data')
    parser.add_argument('--date', type=str, help='Date to fix (YYYY-MM-DD format)')
    parser.add_argument('--finance', type=int, help='Correct ranking for iPhone - Free - Finance')
    parser.add_argument('--apps', type=int, help='Correct ranking for iPhone - Free - Apps')
    parser.add_argument('--overall', type=int, help='Correct ranking for iPhone - Free - Overall')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    
    args = parser.parse_args()
    
    # If no arguments provided, run in interactive mode
    if not any([args.date, args.finance, args.apps, args.overall]) and not args.interactive:
        fix_historical_data(interactive=True)
    else:
        fix_historical_data(args.date, args.finance, args.apps, args.overall, args.interactive)