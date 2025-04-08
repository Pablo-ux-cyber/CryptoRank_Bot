import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

def generate_rankings_chart(csv_file='historical_data.csv', output_file='static/rankings_chart.png'):
    """
    Generate a chart visualizing app rankings over time
    
    Args:
        csv_file (str): Path to the CSV file containing historical data
        output_file (str): Path to save the output chart image
    
    Returns:
        bool: True if chart was successfully generated, False otherwise
    """
    try:
        # Read data from CSV file
        df = pd.read_csv(csv_file)
        
        # Convert date column to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Sort by date
        df = df.sort_values('date')
        
        # Create a new figure with a specific size
        plt.figure(figsize=(12, 8))
        
        # Set dark background style
        plt.style.use('dark_background')
        
        # Plot data for each category, handling missing values
        if 'iPhone - Free - Finance' in df.columns and not df['iPhone - Free - Finance'].isna().all():
            plt.plot(df['date'], df['iPhone - Free - Finance'], marker='o', linestyle='-', linewidth=2, label='Finance')
            
        if 'iPhone - Free - Apps' in df.columns and not df['iPhone - Free - Apps'].isna().all():
            plt.plot(df['date'], df['iPhone - Free - Apps'], marker='s', linestyle='-', linewidth=2, label='Apps')
            
        if 'iPhone - Free - Overall' in df.columns and not df['iPhone - Free - Overall'].isna().all():
            plt.plot(df['date'], df['iPhone - Free - Overall'], marker='^', linestyle='-', linewidth=2, label='Overall')
        
        # Set labels and title
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Ranking (lower is better)', fontsize=12)
        plt.title('Coinbase App Store Rankings - Last 30 Days', fontsize=16)
        
        # Format y-axis (invert so lower numbers are higher on chart, better ranking)
        plt.gca().invert_yaxis()
        
        # Add grid
        plt.grid(alpha=0.3)
        
        # Add legend
        plt.legend(fontsize=12)
        
        # Format x-axis dates
        plt.gcf().autofmt_xdate()
        
        # Add annotations showing latest position
        latest = df.iloc[-1]
        
        # Add annotations for the latest values if values exist
        if 'iPhone - Free - Finance' in df.columns and not pd.isna(latest['iPhone - Free - Finance']):
            plt.annotate(f"#{int(latest['iPhone - Free - Finance'])}", 
                         xy=(latest['date'], latest['iPhone - Free - Finance']),
                         xytext=(10, -15),
                         textcoords='offset points',
                         fontsize=10,
                         bbox=dict(boxstyle="round,pad=0.3", fc="blue", alpha=0.3))
        
        if 'iPhone - Free - Apps' in df.columns and not pd.isna(latest['iPhone - Free - Apps']):
            plt.annotate(f"#{int(latest['iPhone - Free - Apps'])}", 
                         xy=(latest['date'], latest['iPhone - Free - Apps']),
                         xytext=(10, -15),
                         textcoords='offset points',
                         fontsize=10,
                         bbox=dict(boxstyle="round,pad=0.3", fc="orange", alpha=0.3))
        
        if 'iPhone - Free - Overall' in df.columns and not pd.isna(latest['iPhone - Free - Overall']):
            plt.annotate(f"#{int(latest['iPhone - Free - Overall'])}", 
                         xy=(latest['date'], latest['iPhone - Free - Overall']),
                         xytext=(10, -15),
                         textcoords='offset points',
                         fontsize=10,
                         bbox=dict(boxstyle="round,pad=0.3", fc="green", alpha=0.3))
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Save figure
        plt.tight_layout()
        plt.savefig(output_file, dpi=100)
        plt.close()
        
        print(f"Chart generated and saved to {output_file}")
        return True
    
    except Exception as e:
        print(f"Error generating chart: {str(e)}")
        return False

def generate_summary_analysis(csv_file='historical_data.csv', output_file='data_analysis.txt'):
    """
    Generate a summary analysis of the historical data
    
    Args:
        csv_file (str): Path to the CSV file containing historical data
        output_file (str): Path to save the output analysis text
    
    Returns:
        bool: True if analysis was successfully generated, False otherwise
    """
    try:
        # Read data from CSV file
        df = pd.read_csv(csv_file)
        
        # Convert date column to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Sort by date
        df = df.sort_values('date')
        
        # Calculate basic statistics for each category
        categories = ['iPhone - Free - Finance', 'iPhone - Free - Apps', 'iPhone - Free - Overall']
        
        with open(output_file, 'w') as f:
            f.write(f"Coinbase App Rankings - Statistical Analysis\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Data period: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}\n")
            f.write(f"Total days of data: {len(df)}\n\n")
            
            for category in categories:
                # Check if the category exists and has non-NaN values
                if category in df.columns and not df[category].isna().all():
                    f.write(f"Category: {category}\n")
                    
                    # Only process and display data if we have valid values
                    current_value = df[category].iloc[-1]
                    if not pd.isna(current_value):
                        f.write(f"  Current ranking: #{int(current_value)}\n")
                    
                    min_value = df[category].min()
                    if not pd.isna(min_value):
                        min_date = df.loc[df[category].idxmin(), 'date'].strftime('%Y-%m-%d')
                        f.write(f"  Best ranking: #{int(min_value)} on {min_date}\n")
                    
                    max_value = df[category].max()
                    if not pd.isna(max_value):
                        max_date = df.loc[df[category].idxmax(), 'date'].strftime('%Y-%m-%d')
                        f.write(f"  Worst ranking: #{int(max_value)} on {max_date}\n")
                    
                    mean_value = df[category].mean()
                    if not pd.isna(mean_value):
                        f.write(f"  Average ranking: #{mean_value:.1f}\n")
                else:
                    f.write(f"Category: {category}\n")
                    f.write(f"  No data available for this category\n")
                
                # Only add trend and volatility analysis if we have data for this category
                if category in df.columns and not df[category].isna().all():
                    # Calculate trend (comparing first and last week averages) if enough data
                    if len(df) >= 14 and df[category].notna().sum() >= 14:  # Ensure we have at least 2 weeks of valid data
                        # Filter out NaN values for calculations
                        valid_data = df[df[category].notna()]
                        if len(valid_data) >= 14:
                            first_week = valid_data[category].iloc[:7].mean()
                            last_week = valid_data[category].iloc[-7:].mean()
                            
                            if not pd.isna(first_week) and not pd.isna(last_week) and first_week != 0:
                                change = first_week - last_week
                                change_pct = (change / first_week) * 100
                                
                                trend_desc = "improved" if change > 0 else "worsened"
                                f.write(f"  Trend (comparing first week vs last week): Ranking has {trend_desc} by {abs(change):.1f} positions ({abs(change_pct):.1f}%)\n")
                    
                    # Calculate volatility (standard deviation) only if we have data
                    std_value = df[category].std()
                    if not pd.isna(std_value):
                        f.write(f"  Volatility (standard deviation): {std_value:.2f} positions\n")
                
                f.write("\n")
            
            # Overall insights
            f.write("Overall Insights:\n")
            
            # Check which categories have enough valid data
            valid_categories = []
            for category in categories:
                if category in df.columns and not df[category].isna().all() and df[category].notna().sum() > 2:
                    valid_categories.append(category)
            
            # Only show correlation if we have at least 2 valid categories
            if len(valid_categories) >= 2:
                f.write("Correlation between categories:\n")
                # Create a correlation matrix only for valid categories
                corr_matrix = df[valid_categories].corr()
                
                for i, cat1 in enumerate(valid_categories):
                    for j, cat2 in enumerate(valid_categories):
                        if i < j:  # Only show each pair once
                            corr = corr_matrix.loc[cat1, cat2]
                            # Only display if correlation is valid
                            if not pd.isna(corr):
                                corr_desc = "Strong positive" if corr > 0.7 else "Moderate positive" if corr > 0.3 else "Weak positive" if corr > 0 else "Weak negative" if corr > -0.3 else "Moderate negative" if corr > -0.7 else "Strong negative"
                                f.write(f"  {cat1} vs {cat2}: {corr_desc} ({corr:.2f})\n")
            else:
                f.write("Insufficient data to calculate correlations between categories.\n")
            
            f.write("\n")
            
            # Check for significant changes or events, but only for categories with enough data
            for category in valid_categories:  # Only process valid categories
                if df[category].notna().sum() >= 3:  # Need at least 3 data points to analyze changes
                    # Calculate day-to-day changes
                    df[f'{category}_change'] = df[category].diff()
                    
                    # Find significant jumps (more than 20% change from previous position)
                    # Must have both current and previous values be valid
                    valid_rows = df[df[category].notna() & df[category].shift(1).notna()]
                    if not valid_rows.empty:
                        significant_changes = valid_rows[abs(valid_rows[f'{category}_change']) > valid_rows[category].shift(1) * 0.2].copy()
                        
                        if not significant_changes.empty:
                            f.write(f"Significant changes in {category}:\n")
                            for _, row in significant_changes.iterrows():
                                change = row[f'{category}_change']
                                if not pd.isna(change):
                                    direction = "improved" if change < 0 else "dropped"
                                    prev_val = row[category] - change
                                    f.write(f"  {row['date'].strftime('%Y-%m-%d')}: Ranking {direction} by {abs(change):.0f} positions (from #{prev_val:.0f} to #{row[category]:.0f})\n")
                            f.write("\n")
        
        print(f"Analysis generated and saved to {output_file}")
        return True
    
    except Exception as e:
        print(f"Error generating analysis: {str(e)}")
        return False

# Generate both chart and analysis when run directly
if __name__ == "__main__":
    generate_rankings_chart()
    generate_summary_analysis()