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
        
        # Plot data for each category
        plt.plot(df['date'], df['iPhone - Free - Finance'], marker='o', linestyle='-', linewidth=2, label='Finance')
        plt.plot(df['date'], df['iPhone - Free - Apps'], marker='s', linestyle='-', linewidth=2, label='Apps')
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
        
        # Add annotations for the latest values
        plt.annotate(f"#{int(latest['iPhone - Free - Finance'])}", 
                     xy=(latest['date'], latest['iPhone - Free - Finance']),
                     xytext=(10, -15),
                     textcoords='offset points',
                     fontsize=10,
                     bbox=dict(boxstyle="round,pad=0.3", fc="blue", alpha=0.3))
        
        plt.annotate(f"#{int(latest['iPhone - Free - Apps'])}", 
                     xy=(latest['date'], latest['iPhone - Free - Apps']),
                     xytext=(10, -15),
                     textcoords='offset points',
                     fontsize=10,
                     bbox=dict(boxstyle="round,pad=0.3", fc="orange", alpha=0.3))
        
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
                f.write(f"Category: {category}\n")
                f.write(f"  Current ranking: #{int(df[category].iloc[-1])}\n")
                f.write(f"  Best ranking: #{int(df[category].min())} on {df.loc[df[category].idxmin(), 'date'].strftime('%Y-%m-%d')}\n")
                f.write(f"  Worst ranking: #{int(df[category].max())} on {df.loc[df[category].idxmax(), 'date'].strftime('%Y-%m-%d')}\n")
                f.write(f"  Average ranking: #{df[category].mean():.1f}\n")
                
                # Calculate trend (comparing first and last week averages)
                if len(df) >= 14:  # Ensure we have at least 2 weeks of data
                    first_week = df[category].iloc[:7].mean()
                    last_week = df[category].iloc[-7:].mean()
                    change = first_week - last_week
                    change_pct = (change / first_week) * 100
                    
                    trend_desc = "improved" if change > 0 else "worsened"
                    f.write(f"  Trend (comparing first week vs last week): Ranking has {trend_desc} by {abs(change):.1f} positions ({abs(change_pct):.1f}%)\n")
                
                # Calculate volatility (standard deviation)
                f.write(f"  Volatility (standard deviation): {df[category].std():.2f} positions\n\n")
            
            # Overall insights
            f.write("Overall Insights:\n")
            
            # Correlation between categories
            f.write("Correlation between categories:\n")
            corr_matrix = df[categories].corr()
            for i, cat1 in enumerate(categories):
                for j, cat2 in enumerate(categories):
                    if i < j:  # Only show each pair once
                        corr = corr_matrix.loc[cat1, cat2]
                        corr_desc = "Strong positive" if corr > 0.7 else "Moderate positive" if corr > 0.3 else "Weak positive" if corr > 0 else "Weak negative" if corr > -0.3 else "Moderate negative" if corr > -0.7 else "Strong negative"
                        f.write(f"  {cat1} vs {cat2}: {corr_desc} ({corr:.2f})\n")
            
            f.write("\n")
            
            # Check for significant changes or events
            for category in categories:
                # Calculate day-to-day changes
                df[f'{category}_change'] = df[category].diff()
                
                # Find significant jumps (more than 20% change from previous position)
                significant_changes = df[abs(df[f'{category}_change']) > df[category].shift(1) * 0.2].copy()
                
                if not significant_changes.empty:
                    f.write(f"Significant changes in {category}:\n")
                    for _, row in significant_changes.iterrows():
                        change = row[f'{category}_change']
                        direction = "improved" if change < 0 else "dropped"
                        f.write(f"  {row['date'].strftime('%Y-%m-%d')}: Ranking {direction} by {abs(change):.0f} positions (from #{row[category]-change:.0f} to #{row[category]:.0f})\n")
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