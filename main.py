import time
import signal
import sys
import threading
import os
import csv
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, redirect, url_for, flash, request, send_file
from logger import logger
from scheduler import SensorTowerScheduler
from config import APP_ID, SCHEDULE_HOUR, SCHEDULE_MINUTE, TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "sensortower_bot_secret")
scheduler = None
last_scrape_data = None
last_scrape_time = None

def start_scheduler_thread():
    """Start the scheduler in a separate thread"""
    global scheduler
    scheduler = SensorTowerScheduler()
    success = scheduler.start()
    if not success:
        logger.error("Failed to start the scheduler")
    return success

def signal_handler(sig, frame):
    """Handle SIGINT (Ctrl+C) signal to gracefully shut down the application"""
    logger.info("Shutting down SensorTower bot...")
    if scheduler:
        scheduler.stop()
    sys.exit(0)

@app.route('/')
def index():
    """Render the home page"""
    global last_scrape_data, last_scrape_time
    
    # Check if scheduler is running
    status = "running" if scheduler and scheduler.running else "error"
    status_text = "Running" if status == "running" else "Error"
    status_class = "success" if status == "running" else "danger"
    
    # Check if Telegram is configured
    telegram_configured = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID)
    
    # Calculate next run time
    next_run = "Not scheduled"
    if scheduler and scheduler.running:
        # With our custom scheduler, we don't have a way to get next_run_time directly
        # So we'll show it as 24 hours from now
        next_run = (datetime.now() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    
    schedule_time = f"{SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d}"
    
    # Get categories from last scrape if available
    categories = []
    if last_scrape_data and "categories" in last_scrape_data:
        categories = last_scrape_data["categories"]
    
    return render_template('index.html', 
                          status=status,
                          status_text=status_text,
                          status_class=status_class,
                          app_id=APP_ID,
                          telegram_configured=telegram_configured,
                          next_run=next_run,
                          schedule_time=schedule_time,
                          last_scrape_time=last_scrape_time,
                          categories=categories)

@app.route('/test-telegram')
def test_telegram():
    """Test the Telegram connection"""
    if not scheduler:
        return jsonify({"status": "error", "message": "Scheduler not initialized"}), 500
        
    try:
        # Test the Telegram connection using the bot's test_connection method
        telegram_bot = scheduler.telegram_bot
        if telegram_bot.test_connection():
            # If test is successful, try to send a test message
            test_msg = (
                "🧪 Тестовое сообщение от SensorTower Bot\n\n"
                "Это сообщение отправлено для проверки работы бота.\n"
                f"Дата и время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            if telegram_bot.send_message(test_msg):
                return jsonify({
                    "status": "success", 
                    "message": "Telegram connection successful and test message sent!"
                })
            else:
                return jsonify({
                    "status": "warning", 
                    "message": "Connected to Telegram API, but failed to send test message. Check your channel ID."
                }), 200
        else:
            return jsonify({
                "status": "error", 
                "message": "Failed to connect to Telegram API. Check your bot token."
            }), 400
    except Exception as e:
        logger.error(f"Error testing Telegram connection: {str(e)}")
        return jsonify({"status": "error", "message": f"Error: {str(e)}"}), 500

@app.route('/trigger-scrape')
def trigger_scrape():
    """Manually trigger a scrape job"""
    global last_scrape_data, last_scrape_time
    
    if not scheduler:
        return jsonify({"status": "error", "message": "Scheduler not initialized"}), 500
    
    try:
        # Run the scraping job
        success = scheduler.run_scraping_job()
        
        # Update last scrape time regardless of success
        last_scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Update last_scrape_data if there is any (might be None)
        last_scrape_data = scheduler.scraper.last_scrape_data
        
        if success:
            # Normal success flow - data was scraped and sent to Telegram
            flash('Scraping job completed successfully!', 'success')
            return redirect(url_for('index'))
        else:
            # The job ran but no data was found or there was an issue
            # We still redirect to index but with a warning message
            flash('Scraping job completed, but no data was found. Check logs for details.', 'warning')
            return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error triggering manual scrape: {str(e)}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/logs')
def view_logs():
    """View the application logs"""
    from config import LOG_FILE
    
    # Read the last 100 lines of the log file
    log_content = []
    try:
        with open(LOG_FILE, 'r') as f:
            log_content = f.readlines()[-100:]
    except Exception as e:
        logger.error(f"Error reading log file: {str(e)}")
        log_content = [f"Error reading log file: {str(e)}"]
    
    return render_template('logs.html', logs=log_content)

@app.route('/history')
def view_history():
    """View historical data and analysis"""
    # Read historical data from CSV file
    historical_data = []
    analytics = {
        'finance': {'current': 0, 'best': 0, 'worst': 0, 'trend': 0, 'first_value': 0},
        'apps': {'current': 0, 'best': 0, 'worst': 0, 'trend': 0, 'first_value': 0},
        'overall': {'current': 0, 'best': 0, 'worst': 0, 'trend': 0, 'first_value': 0}
    }
    
    try:
        df = pd.read_csv('historical_data.csv')
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        
        # Get the first and last value for each category to calculate trend
        first_finance = df.iloc[0]['iPhone - Free - Finance']
        first_apps = df.iloc[0]['iPhone - Free - Apps']
        first_overall = df.iloc[0]['iPhone - Free - Overall']
        
        last_finance = df.iloc[-1]['iPhone - Free - Finance']
        last_apps = df.iloc[-1]['iPhone - Free - Apps']
        last_overall = df.iloc[-1]['iPhone - Free - Overall']
        
        # Calculate trend (positive means improvement, ranks going down)
        finance_trend = first_finance - last_finance
        apps_trend = first_apps - last_apps
        overall_trend = first_overall - last_overall
        
        # Fill analytics data
        analytics = {
            'finance': {
                'current': int(last_finance),
                'best': int(df['iPhone - Free - Finance'].min()),
                'worst': int(df['iPhone - Free - Finance'].max()),
                'trend': int(finance_trend),
                'first_value': int(first_finance)
            },
            'apps': {
                'current': int(last_apps),
                'best': int(df['iPhone - Free - Apps'].min()),
                'worst': int(df['iPhone - Free - Apps'].max()),
                'trend': int(apps_trend),
                'first_value': int(first_apps)
            },
            'overall': {
                'current': int(last_overall),
                'best': int(df['iPhone - Free - Overall'].min()),
                'worst': int(df['iPhone - Free - Overall'].max()),
                'trend': int(overall_trend),
                'first_value': int(first_overall)
            }
        }
        
        # Transform the data for template
        for _, row in df.iterrows():
            historical_data.append({
                'date': row['date'],
                'finance': row['iPhone - Free - Finance'],
                'apps': row['iPhone - Free - Apps'],
                'overall': row['iPhone - Free - Overall']
            })
            
    except Exception as e:
        logger.error(f"Error reading historical data: {str(e)}")
    
    # Try to read from data analysis file for more insights
    analysis_content = ""
    try:
        with open('data_analysis.txt', 'r') as f:
            analysis_content = f.read()
    except Exception as e:
        logger.error(f"Error reading analysis file: {str(e)}")
    
    return render_template('history_dynamic.html', 
                          historical_data=historical_data, 
                          analytics=analytics,
                          analysis_content=analysis_content)

@app.route('/download/history')
def download_history():
    """Download historical data as CSV"""
    try:
        return send_file('historical_data.csv',
                        mimetype='text/csv',
                        as_attachment=True,
                        download_name='coinbase_rankings_history.csv')
    except Exception as e:
        logger.error(f"Error downloading historical data: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"})

# Set up signal handler for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)

# Start the scheduler in a background thread when the app starts
scheduler_thread = threading.Thread(target=start_scheduler_thread)
scheduler_thread.daemon = True
scheduler_thread.start()

if __name__ == "__main__":
    # When running directly (not through gunicorn)
    app.run(host="0.0.0.0", port=5000, debug=True)
