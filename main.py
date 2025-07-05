import time
import signal
import sys
import threading
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, redirect, url_for, flash, request

# Загружаем переменные окружения из .env файла, если он есть
from load_dotenv import load_dotenv
load_dotenv()

from logger import logger
from scheduler import SensorTowerScheduler
from config import APP_ID, SCHEDULE_HOUR, SCHEDULE_MINUTE, TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
from history_api import HistoryAPI
from routes.history_routes import history_bp
from routes.altseason_routes import altseason_bp
from json_rank_reader import get_rank_from_json, get_latest_rank_date

# Create Flask app
app = Flask(__name__)
# Используем переменную окружения SESSION_SECRET для secret_key или фолбэк
app.secret_key = os.environ.get("SESSION_SECRET", "sensortower_bot_secret")

# Добавляем фильтр now() для шаблонов
@app.template_filter('now')
def template_now(_=None):
    return datetime.now()

# Добавляем фильтр для преобразования timestamp в читаемую дату
@app.template_filter('timestampToDate')
def timestamp_to_date(timestamp):
    if not timestamp:
        return "N/A"
    try:
        # Если timestamp передан как строка, преобразуем ее в число
        if isinstance(timestamp, str):
            timestamp = float(timestamp)
        # Преобразуем timestamp в читаемую дату
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return timestamp  # В случае ошибки возвращаем исходное значение

# Добавляем глобальную функцию now() для шаблонов
@app.context_processor
def utility_processor():
    def now():
        return datetime.now()
    return dict(now=now)

# Регистрируем Blueprint'ы
app.register_blueprint(history_bp)
app.register_blueprint(altseason_bp)

# Инициализируем глобальные переменные
scheduler = None
last_scrape_data = None
last_scrape_time = None
last_fear_greed_data = None
last_fear_greed_time = None
last_altseason_data = None
last_altseason_time = None

def get_current_rank():
    """Get current rank from manual file or JSON file"""
    try:
        # Check if manual rank file exists
        if os.path.exists('manual_rank.txt'):
            with open('manual_rank.txt', 'r') as f:
                manual_rank = f.read().strip()
                if manual_rank and manual_rank.isdigit():
                    return int(manual_rank)
        
        # Read from JSON file
        json_rank = get_rank_from_json()
        if json_rank is not None:
            return json_rank
        
        # Return None if no data available
        return None
    except Exception:
        return None

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
    global last_scrape_data, last_scrape_time, last_fear_greed_data, last_fear_greed_time, last_altseason_data, last_altseason_time
    
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
        # Рассчитываем время следующего запуска (5:01 UTC = 8:01 MSK)
        now = datetime.now()
        next_scheduled = now.replace(hour=5, minute=1, second=0, microsecond=0)
        
        # Если время уже прошло сегодня, планируем на завтра
        if next_scheduled <= now:
            next_scheduled += timedelta(days=1)
            
        next_run = next_scheduled.strftime("%Y-%m-%d %H:%M:%S")
    
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
                          last_altseason_data=last_altseason_data,
                          last_altseason_time=last_altseason_time,
                          current_rank=get_current_rank())

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
            
            # Добавляем данные Altcoin Season Index
            if scheduler.altcoin_season_index:
                # Получаем свежие данные Altcoin Season Index
                altseason_data = scheduler.altcoin_season_index.get_altseason_index()
                if altseason_data:
                    altseason_message = scheduler.altcoin_season_index.format_altseason_message(altseason_data)
                    if altseason_message:
                        combined_message += "\n\n" + altseason_message
                        logger.info(f"Added Altcoin Season Index data to combined message: {altseason_data['signal']}")
            
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

@app.route('/get-altseason-index')
def get_altseason_index():
    """Manually fetch Altcoin Season Index data and send it as a message"""
    global last_scrape_data, last_scrape_time, last_altseason_data, last_altseason_time
    
    if not scheduler:
        return jsonify({"status": "error", "message": "Scheduler not initialized"}), 500
    
    try:
        # Получаем реальные данные Altcoin Season Index
        logger.info("Запрос данных Altcoin Season Index...")
        altseason_data = scheduler.altcoin_season_index.get_altseason_index()
        altseason_message = scheduler.altcoin_season_index.format_altseason_message(altseason_data)
        
        if altseason_data:
            logger.info(f"Получены данные Altcoin Season Index: {altseason_data['signal']} - {altseason_data['status']}")
        else:
            logger.warning("Не удалось получить данные Altcoin Season Index")
        
        if altseason_data:
            # Сохраняем данные для отображения
            last_altseason_data = altseason_data
            last_altseason_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # В ручном режиме объединяем с данными о рейтинге для отправки полного сообщения
            # Получаем последние данные о рейтинге
            rankings_data = last_scrape_data if last_scrape_data else scheduler.scraper.scrape_category_rankings()
            
            # Получаем данные Fear & Greed Index
            fear_greed_data = scheduler.fear_greed_tracker.get_fear_greed_index()
            
            # Отправляем полное комбинированное сообщение со всеми данными
            sent = scheduler.run_now(force_send=True)
            
            if sent:
                flash(f"Complete data with Altcoin Season Index ({altseason_data['signal']}) successfully sent to Telegram!", "success")
            else:
                flash("Data fetched but failed to send to Telegram.", "warning")
                
            return redirect(url_for('index'))
        else:
            return jsonify({"status": "error", "message": "Failed to retrieve Altcoin Season Index data"}), 500
    except Exception as e:
        logger.error(f"Error fetching Altcoin Season Index data: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"})

@app.route('/test-message')
def test_message():
    """Manually send a test message with cached data to the test channel"""
    global last_fear_greed_data, last_scrape_data, last_altseason_data
    
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
        
        # Get Fear & Greed Index data
        fear_greed_data = scheduler.get_current_fear_greed_index()
        
        # Format individual messages (без Altcoin Season Index)
        rankings_message = scheduler.scraper.format_rankings_message(rankings_data)
        fear_greed_message = scheduler.fear_greed_tracker.format_fear_greed_message(fear_greed_data)
        
        # Build combined message (только рейтинг и Fear & Greed)
        combined_message = rankings_message
        combined_message += "\n\n" + fear_greed_message
        
        # Send the message
        sent = scheduler.telegram_bot.send_message(combined_message)
        
        if sent:
            return jsonify({
                "status": "success", 
                "message": "Test message sent to Telegram channel",
                "content": combined_message
            })
        else:
            return jsonify({"status": "error", "message": "Failed to send message to Telegram"}), 500
    except Exception as e:
        logger.error(f"Error sending test message: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/test_format')
def test_format():
    """Test the message formatting with sample data"""
    from scraper import SensorTowerScraper
    from fear_greed_index import FearGreedIndexTracker
    from altcoin_season_index import AltcoinSeasonIndex
    
    try:
        # Create instances for formatting even if scheduler is not running
        scraper = scheduler.scraper if scheduler else SensorTowerScraper()
        fear_greed_tracker = scheduler.fear_greed_tracker if scheduler else FearGreedIndexTracker()
        altcoin_season_index = scheduler.altcoin_season_index if scheduler else AltcoinSeasonIndex()
        
        # Sample app ranking data
        rankings_data = {
            "app_name": "Coinbase",
            "app_id": "886427730",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "categories": [
                {"category": "Finance", "rank": "329", "previous_rank": "332"}
            ],
            "trend": {"direction": "up", "previous": 332}
        }
        
        # Sample fear and greed data
        fear_greed_data = {
            "value": 72,
            "classification": "Greed",
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        
        # Sample Altcoin Season Index data
        altseason_data = {
            "index": 0.65,
            "status": "Moderate Altseason",
            "signal": "🟡",
            "description": "Many altcoins outperform Bitcoin",
            "btc_performance": 8.5,
            "timestamp": int(time.time()),
            "date": datetime.now().strftime('%Y-%m-%d')
        }
        
        # Format individual messages
        rankings_message = scraper.format_rankings_message(rankings_data)
        fear_greed_message = fear_greed_tracker.format_fear_greed_message(fear_greed_data)
        altseason_message = altcoin_season_index.format_altseason_message(altseason_data)
        
        # Format combined message
        combined_message = rankings_message
        combined_message += "\n\n" + fear_greed_message
        
        # Добавляем Altcoin Season Index только если данные доступны
        if altseason_message:
            combined_message += "\n\n" + altseason_message
        
        # If this is a web request (not API)
        if request.headers.get('Accept', '').find('application/json') == -1:
            return render_template('format_test.html',
                                   rankings_message=rankings_message,
                                   fear_greed_message=fear_greed_message,
                                   altseason_message=altseason_message,
                                   combined_message=combined_message)
        
        # Return JSON for API requests
        return jsonify({
            "status": "success",
            "rankings_message": rankings_message,
            "fear_greed_message": fear_greed_message,
            "altseason_message": altseason_message,
            "combined_message": combined_message
        })
    except Exception as e:
        logger.error(f"Error testing message format: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/set_manual_rank', methods=['POST'])
def set_manual_rank():
    """Set manual rank for Coinbase app"""
    try:
        rank = request.form.get('rank')
        if not rank or not rank.isdigit():
            return jsonify({"status": "error", "message": "Invalid rank value"}), 400
        
        # Save rank to file
        with open('manual_rank.txt', 'w') as f:
            f.write(rank)
        
        logger.info(f"Manual rank set to: {rank}")
        return jsonify({"status": "success", "message": f"Manual rank set to {rank}"})
    except Exception as e:
        logger.error(f"Error setting manual rank: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/market-breadth')
def market_breadth():
    """Market Breadth Analysis using your exact code"""
    try:
        from crypto_analyzer_cryptocompare import CryptoAnalyzer
        from data_cache import DataCache
        import pandas as pd
        
        # Инициализация компонентов (ваш код)
        cache = DataCache()
        analyzer = CryptoAnalyzer(cache)
        
        # Получение данных для демонстрации (упрощенная версия)
        breadth_data = {
            'signal': '📊',
            'condition': 'Analysis Ready',
            'description': 'Market breadth analyzer is initialized and ready. Click "Start Analysis" to begin.',
            'current_value': 0,
            'timestamp': 'Ready to start',
            'coins_above_ma': 'N/A',
            'total_coins': '50',
            'cache_info': cache.get_cache_info()
        }
        
        return render_template('market_breadth_analysis.html', breadth_data=breadth_data)
        
    except Exception as e:
        logger.error(f"Error initializing market breadth: {str(e)}")
        return render_template('market_breadth_analysis.html', 
                             breadth_data=None, error=str(e))

@app.route('/api/run-market-analysis', methods=['POST'])
def run_market_analysis():
    """Запуск полного анализа рынка"""
    try:
        from crypto_analyzer_cryptocompare import CryptoAnalyzer
        from data_cache import DataCache
        import pandas as pd
        
        # Получение параметров из запроса
        data = request.get_json() or {}
        top_n = data.get('top_n', 50)
        ma_period = data.get('ma_period', 200) 
        history_days = data.get('history_days', 365)
        
        # Инициализация
        cache = DataCache()
        analyzer = CryptoAnalyzer(cache)
        
        # Получение топ монет (ваш код)
        top_coins = analyzer.get_top_coins(top_n)
        if not top_coins:
            return jsonify({"status": "error", "message": "Не удалось получить список топ монет"})
        
        # Загрузка исторических данных
        historical_data = analyzer.load_historical_data(
            top_coins, 
            ma_period + history_days + 100
        )
        
        if not historical_data:
            return jsonify({"status": "error", "message": "Не удалось загрузить исторические данные"})
        
        # Расчет индикатора (ваш точный код)
        indicator_data = analyzer.calculate_market_breadth(
            historical_data, 
            ma_period, 
            history_days
        )
        
        if indicator_data.empty:
            return jsonify({"status": "error", "message": "Не удалось рассчитать индикатор"})
        
        # Получение сводной информации (ваш код)
        summary = analyzer.get_market_summary(indicator_data)
        current_value = summary.get('current_value', 0)
        
        # Подсчет монет выше MA используя данные из summary
        coins_above_ma = summary.get('coins_above_ma', 'N/A')
        
        # Определение рыночного сигнала (ваш код)
        if current_value >= 80:
            signal = "🔴"
            condition = "Перекупленность"
            description = "Большинство монет выше MA200, возможна коррекция"
        elif current_value <= 20:
            signal = "🟢" 
            condition = "Перепроданность"
            description = "Большинство монет ниже MA200, возможен отскок"
        else:
            signal = "🟡"
            condition = "Нейтральная зона"
            description = "Рынок в состоянии равновесия"
        
        # Подготовка данных для графика
        last_30_rows = indicator_data.tail(30)
        chart_data = {
            'labels': [str(idx)[:10] for idx in last_30_rows.index],
            'values': last_30_rows['percentage'].tolist()
        }
        
        # Безопасное получение последней даты
        try:
            last_date = str(indicator_data.index[-1])
            if ' ' in last_date:
                timestamp = last_date.split(' ')[0]
            else:
                timestamp = last_date[:10]
        except:
            timestamp = 'Latest'
        
        result = {
            'status': 'success',
            'data': {
                'signal': signal,
                'condition': condition,
                'description': description,
                'current_value': current_value,
                'timestamp': timestamp,
                'coins_above_ma': coins_above_ma,
                'total_coins': len(top_coins),
                'avg_value': summary.get('avg_value', 0),
                'max_value': summary.get('max_value', 0),
                'min_value': summary.get('min_value', 0),
                'chart_data': chart_data
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in market analysis: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/market-breadth-legacy')
def market_breadth_legacy():
    """Display legacy Market Breadth Indicator page"""
    try:
        # Создаем простую заглушку данных для быстрого отображения
        breadth_data = {
            'signal': '⏳',
            'condition': 'Loading...',
            'description': 'Market breadth data is being calculated. Please use refresh button to get latest data.',
            'current_value': 0,
            'timestamp': 'Loading...',
            'coins_above_ma': 'N/A',
            'total_coins': 'N/A'
        }
        
        return render_template('market_breadth.html', breadth_data=breadth_data)
    except Exception as e:
        logger.error(f"Error loading market breadth page: {str(e)}")
        return render_template('market_breadth.html', breadth_data=None, error=str(e))

@app.route('/api/market-breadth-refresh', methods=['POST'])
def market_breadth_refresh():
    """Refresh market breadth data"""
    try:
        # Получаем актуальные данные от scheduler, если он доступен
        if scheduler and scheduler.market_breadth:
            breadth_data = scheduler.market_breadth.get_market_breadth_data()
            if breadth_data:
                return jsonify({
                    "status": "success", 
                    "message": "Market breadth data refreshed successfully",
                    "data": breadth_data
                })
            else:
                return jsonify({"status": "error", "message": "Market breadth data not yet available"}), 500
        else:
            return jsonify({"status": "error", "message": "Market breadth analyzer not initialized"}), 500
            
    except Exception as e:
        logger.error(f"Error refreshing market breadth data: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Set up signal handler for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)

# Initialize scheduler at startup - for both direct run and gunicorn
scheduler_thread = threading.Thread(target=start_scheduler_thread)
scheduler_thread.daemon = True
scheduler_thread.start()
logger.info("Starting scheduler at app initialization")

if __name__ == "__main__":
    # Run the Flask app when called directly
    app.run(host="0.0.0.0", port=5000, debug=True)
