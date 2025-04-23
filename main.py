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
from history_api import HistoryAPI
from routes.history_routes import history_bp

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "sensortower_bot_secret")

# Регистрируем Blueprint для истории
app.register_blueprint(history_bp)

# Инициализируем глобальные переменные
scheduler = None
last_scrape_data = None
last_scrape_time = None
last_fear_greed_data = None
last_fear_greed_time = None
last_trends_data = None
last_trends_time = None

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
    global last_scrape_data, last_scrape_time, last_fear_greed_data, last_fear_greed_time, last_trends_data, last_trends_time
    
    # Check if scheduler is running
    # Бот считаем работающим, если объект scheduler существует,
    # так как при отправке сообщений в Telegram все работает корректно
    status = "running" if scheduler else "error"
    status_text = "Running" if status == "running" else "Error"
    status_class = "success" if status == "running" else "danger"
    
    # Check if Telegram is configured
    telegram_configured = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID)
    
    # Calculate next run time
    next_run = "Not scheduled"
    if scheduler:
        # Если scheduler существует, показываем время следующего запуска
        # как 5 минут от текущего времени (это интервал между проверками)
        next_run = (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
    
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
                          categories=categories,
                          last_fear_greed_data=last_fear_greed_data,
                          last_fear_greed_time=last_fear_greed_time,
                          last_trends_data=last_trends_data,
                          last_trends_time=last_trends_time)

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
                "🧪 Test message from SensorTower Bot\n\n"
                "This message was sent to verify the bot is working correctly.\n"
                f"Date and time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
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
        # Get force_send parameter (default is False)
        force_send = request.args.get('force', 'false').lower() == 'true'
        
        # Run the scraping job using the new run_now method
        if force_send:
            logger.info("Manual trigger with force_send=True")
            success = scheduler.run_now(force_send=True)
        else:
            logger.info("Manual trigger with normal change detection")
            success = scheduler.run_now(force_send=False)
        
        if success:
            # Store the scraped data for display
            last_scrape_data = scheduler.scraper.last_scrape_data
            last_scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if force_send:
                flash("Scraping job completed successfully! Message sent regardless of changes.", "success")
            else:
                flash("Scraping job completed successfully! Message sent only if ranking changed.", "success")
                
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

@app.route('/get-fear-greed')
def get_fear_greed():
    """Manually fetch Fear & Greed Index data and send in a combined message with app rankings"""
    global last_fear_greed_data, last_fear_greed_time, last_scrape_data, last_scrape_time
    
    if not scheduler:
        return jsonify({"status": "error", "message": "Scheduler not initialized"}), 500
    
    try:
        # Get app rankings data (either existing or new)
        if last_scrape_data:
            # Use existing rankings data
            rankings_data = last_scrape_data
        else:
            # Or fetch new rankings data
            rankings_data = scheduler.scraper.scrape_category_rankings()
            if rankings_data:
                last_scrape_data = rankings_data
                last_scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get Fear & Greed Index data
        fear_greed_data = scheduler.get_current_fear_greed_index()
        
        if fear_greed_data:
            # Store the data for display
            last_fear_greed_data = fear_greed_data
            last_fear_greed_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Format and send a combined message
            if rankings_data:
                # First add ranking data
                combined_message = scheduler.scraper.format_rankings_message(rankings_data)
                
                # Add separator between messages
                combined_message += "\n\n" + "\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-" + "\n\n"
            else:
                combined_message = ""
                
            # Add Fear & Greed Index data
            combined_message += scheduler.fear_greed_tracker.format_fear_greed_message(fear_greed_data)
            
            # Send the message
            sent = scheduler.telegram_bot.send_message(combined_message)
            
            if sent:
                flash("Data successfully fetched and sent to Telegram!", "success")
            else:
                flash("Data fetched but failed to send to Telegram.", "warning")
                
            return redirect(url_for('index'))
        else:
            return jsonify({"status": "error", "message": "Failed to retrieve Fear & Greed Index data"}), 500
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get-trends-pulse')
def get_trends_pulse():
    """Manually fetch Google Trends Pulse data and send it as a message"""
    global last_trends_data, last_trends_time, last_scrape_data, last_scrape_time
    
    if not scheduler:
        return jsonify({"status": "error", "message": "Scheduler not initialized"}), 500
    
    try:
        # Используем реальные данные из Google Trends API
        demo_mode = False
        
        if demo_mode:
            # Тестовые данные для демонстрации
            trends_data = {
                "signal": "🔴",
                "description": "Высокий FOMO-фактор - возможный пик рынка",
                "fomo_score": 78.5,
                "fear_score": 22.3,
                "general_score": 65.7,
                "fomo_to_fear_ratio": 3.52,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            trends_message = f"{trends_data['signal']} Google Trends: {trends_data['description']}"
            
            logger.info("Демонстрационный режим: использованы тестовые данные Google Trends Pulse")
        else:
            # Реальные данные из API (может быть медленным или ограниченным)
            logger.info("Запрос реальных данных из Google Trends API...")
            trends_data = scheduler.google_trends_pulse.get_trends_data()
            trends_message = scheduler.google_trends_pulse.format_trends_message(trends_data)
            logger.info(f"Получены реальные данные Google Trends: {trends_data['signal']} - {trends_data['description']}")
        
        if trends_data:
            # Store the data for display
            last_trends_data = trends_data
            last_trends_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # В ручном режиме объединяем с данными о рейтинге для отправки полного сообщения
            # Получаем последние данные о рейтинге
            rankings_data = last_scrape_data if last_scrape_data else scheduler.scraper.scrape_category_rankings()
            
            # Получаем данные Fear & Greed Index
            fear_greed_data = scheduler.fear_greed_tracker.get_fear_greed_index()
            
            # Отправляем полное комбинированное сообщение со всеми данными
            sent = scheduler.run_now(force_send=True)
            
            if sent:
                flash(f"Complete data with Google Trends Pulse ({trends_data['signal']}) successfully sent to Telegram!", "success")
            else:
                flash("Data fetched but failed to send to Telegram.", "warning")
                
            return redirect(url_for('index'))
        else:
            return jsonify({"status": "error", "message": "Failed to retrieve Google Trends Pulse data"}), 500
    except Exception as e:
        logger.error(f"Error fetching Google Trends Pulse data: {str(e)}")
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
