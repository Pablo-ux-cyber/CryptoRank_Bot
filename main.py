import time
import signal
import sys
import threading
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, redirect, url_for, flash, request
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

@app.route('/trigger-scrape')
def trigger_scrape():
    """Manually trigger a scrape job"""
    global last_scrape_data, last_scrape_time
    
    if not scheduler:
        return jsonify({"status": "error", "message": "Scheduler not initialized"}), 500
    
    try:
        # Run the scraping job
        success = scheduler.run_scraping_job()
        
        if success:
            # Store the scraped data for display
            last_scrape_data = scheduler.scraper.last_scrape_data
            last_scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return redirect(url_for('index'))
        else:
            return jsonify({"status": "error", "message": "Scraping job failed"}), 500
    except Exception as e:
        logger.error(f"Error triggering manual scrape: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

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
