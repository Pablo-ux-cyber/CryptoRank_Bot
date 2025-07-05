import time
import signal
import sys
import threading
import os
import io
import base64
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, redirect, url_for, flash, request, send_file

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

@app.route('/test-chart')
def test_chart():
    """Test sending chart link to Telegram"""
    try:
        if not scheduler or not scheduler.telegram_bot:
            flash("❌ Telegram bot not available", "danger")
            return redirect(url_for('index'))
        
        # Создаем ссылку на график  
        chart_url = f"https://{request.host}/chart-view"
        
        # Получаем данные для подписи
        if scheduler.market_breadth:
            market_breadth_data = scheduler.market_breadth.get_market_breadth_data()
            if market_breadth_data:
                caption = f"📊 Market Breadth Analysis Test\n{market_breadth_data['signal']} {market_breadth_data['condition']}: {market_breadth_data['current_value']:.1f}%"
            else:
                caption = "📊 Market Breadth Analysis Test"
        else:
            caption = "📊 Market Breadth Analysis Test"
        
        # Создаем короткую ссылку на график (скрывает адрес сервера)
        try:
            from url_shortener import url_shortener
            
            # Создаем короткую ссылку
            short_url = url_shortener.create_chart_short_url(request.host)
            
            # Отправляем сообщение с короткой ссылкой
            message = f"{caption}\n\n📈 Chart: {short_url}"
            
            if scheduler.telegram_bot.send_message(message):
                flash("✅ Chart link sent to Telegram successfully", "success")
            else:
                flash("❌ Failed to send chart link to Telegram", "danger")
                
        except Exception as e:
            flash(f"❌ Error: {str(e)}", "danger")
            
        return redirect(url_for('index'))
    except Exception as e:
        flash(f"❌ Error: {str(e)}", "danger")
        return redirect(url_for('index'))

@app.route('/chart-view')
def chart_view():
    """Direct PNG chart for Telegram links"""
    try:
        # Создаем PNG график напрямую
        chart_image = create_chart_from_web_endpoint()
        
        if chart_image:
            from flask import Response
            return Response(chart_image, mimetype='image/png')
        else:
            return "❌ Failed to generate chart", 500
        
    except Exception as e:
        logger.error(f"Error generating PNG chart: {str(e)}")
        return f"❌ Error: {str(e)}", 500

@app.route('/s/<short_code>')
def redirect_short_url(short_code):
    """Перенаправляет короткие ссылки на оригинальные URL"""
    try:
        from url_shortener import url_shortener
        
        original_url = url_shortener.get_original_url(short_code)
        if original_url:
            # Если это локальный URL, преобразуем в полный
            if original_url.startswith('/'):
                original_url = f"https://{request.host}{original_url}"
            elif 'localhost' in original_url:
                original_url = original_url.replace('localhost:5000', request.host)
            
            return redirect(original_url)
        else:
            return "Short URL not found", 404
            
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/market-breadth')
def market_breadth():
    """Market Breadth Analysis - ваш точный интерфейс"""
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
        
        return render_template('market_breadth_plotly.html', breadth_data=breadth_data)
        
    except Exception as e:
        logger.error(f"Error initializing market breadth: {str(e)}")
        return render_template('market_breadth_plotly.html', 
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
        history_days = data.get('history_days', 1095)  # 3 года по умолчанию
        
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

@app.route('/api/run-market-analysis-plotly', methods=['POST'])
def run_market_analysis_plotly():
    """Запуск полного анализа рынка с Plotly графиками (ваш точный код)"""
    try:
        from crypto_analyzer_cryptocompare import CryptoAnalyzer
        from data_cache import DataCache
        import pandas as pd
        from datetime import datetime, timedelta
        
        # Получение параметров из запроса
        data = request.get_json() or {}
        top_n = data.get('top_n', 50)
        ma_period = data.get('ma_period', 200) 
        history_days = data.get('history_days', 1095)  # 3 года по умолчанию
        
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
        
        # Создание Plotly данных (ваш точный код)
        plotly_data = []
        annotations = []
        shapes = []
        
        # График Bitcoin сверху
        if 'BTC' in historical_data:
            btc_data = historical_data['BTC'].copy()
            btc_data['date'] = pd.to_datetime(btc_data['date'])
            
            # Фильтрация по тому же периоду
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=history_days)
            btc_data = btc_data[(btc_data['date'].dt.date >= start_date) & (btc_data['date'].dt.date <= end_date)]
            
            if not btc_data.empty:
                plotly_data.append({
                    'x': btc_data['date'].dt.strftime('%Y-%m-%d').tolist(),
                    'y': btc_data['price'].tolist(),
                    'mode': 'lines',
                    'name': 'Bitcoin',
                    'line': {'color': '#FF6B35', 'width': 3},
                    'hovertemplate': '<b>%{x}</b><br>BTC Price: $%{y:,.0f}<extra></extra>',
                    'yaxis': 'y'
                })
        
        # График индикатора снизу
        indicator_data_reset = indicator_data.reset_index()
        plotly_data.append({
            'x': indicator_data_reset['date'].dt.strftime('%Y-%m-%d').tolist() if 'date' in indicator_data_reset.columns else [str(d)[:10] for d in indicator_data_reset.index],
            'y': indicator_data_reset['percentage'].tolist(),
            'mode': 'lines',
            'name': '% Of Cryptocurrencies Above 200-Day Moving Average',
            'line': {'color': '#2563EB', 'width': 3},
            'hovertemplate': '<b>%{x}</b><br>Above MA: %{y:.1f}%<extra></extra>',
            'yaxis': 'y2'
        })
        
        # Линии уровней для индикатора
        shapes.extend([
            # Линия 80% - перекупленность  
            {
                'type': 'line',
                'x0': 0, 'x1': 1,
                'y0': 80, 'y1': 80,
                'xref': 'paper', 'yref': 'y2',
                'line': {'color': '#EF4444', 'width': 1.5, 'dash': 'dash'}
            },
            # Линия 20% - перепроданность
            {
                'type': 'line',
                'x0': 0, 'x1': 1,
                'y0': 20, 'y1': 20,
                'xref': 'paper', 'yref': 'y2',
                'line': {'color': '#10B981', 'width': 1.5, 'dash': 'dash'}
            },
            # Линия 50% - нейтральная зона
            {
                'type': 'line',
                'x0': 0, 'x1': 1,
                'y0': 50, 'y1': 50,
                'xref': 'paper', 'yref': 'y2',
                'line': {'color': '#9CA3AF', 'width': 1, 'dash': 'dot'}
            },
            # Зона перекупленности (красная)
            {
                'type': 'rect',
                'x0': 0, 'x1': 1,
                'y0': 80, 'y1': 100,
                'xref': 'paper', 'yref': 'y2',
                'fillcolor': '#FEF2F2', 'opacity': 0.7,
                'layer': 'below', 'line': {'width': 0}
            },
            # Зона перепроданности (зеленая) 
            {
                'type': 'rect',
                'x0': 0, 'x1': 1,
                'y0': 0, 'y1': 20,
                'xref': 'paper', 'yref': 'y2',
                'fillcolor': '#F0FDF4', 'opacity': 0.7,
                'layer': 'below', 'line': {'width': 0}
            },
            # Нейтральная зона (серая)
            {
                'type': 'rect',
                'x0': 0, 'x1': 1,
                'y0': 20, 'y1': 80,
                'xref': 'paper', 'yref': 'y2',
                'fillcolor': '#F9FAFB', 'opacity': 0.5,
                'layer': 'below', 'line': {'width': 0}
            }
        ])
        
        # Аннотации
        annotations.extend([
            {
                'x': 1, 'y': 80,
                'xref': 'paper', 'yref': 'y2',
                'text': 'Overbought (80%)',
                'showarrow': False,
                'xanchor': 'right',
                'font': {'size': 10}
            },
            {
                'x': 1, 'y': 20,
                'xref': 'paper', 'yref': 'y2',
                'text': 'Oversold (20%)',
                'showarrow': False,
                'xanchor': 'right',
                'font': {'size': 10}
            },
            {
                'x': 1, 'y': 50,
                'xref': 'paper', 'yref': 'y2',
                'text': 'Neutral Zone (50%)',
                'showarrow': False,
                'xanchor': 'right',
                'font': {'size': 10}
            },
            {
                'x': 0.05, 'y': 90,
                'xref': 'paper', 'yref': 'y2',
                'text': '<b>80%+ = Market too hot</b><br><b>20%- = Buying opportunity</b><br>Shows how many coins are above 200-day average',
                'showarrow': False,
                'xanchor': 'left',
                'yanchor': 'top',
                'font': {'size': 11, 'color': '#2c3e50'},
                'bgcolor': 'rgba(255,255,255,0.95)',
                'bordercolor': '#2563EB',
                'borderwidth': 2,
                'borderpad': 10
            }
        ])
        
        # Расчет корреляций (ваш код)
        correlations = []
        if 'BTC' in historical_data:
            btc_data = historical_data['BTC'].copy()
            btc_data['date'] = pd.to_datetime(btc_data['date'])
            btc_data = btc_data.set_index('date')
            
            for coin_symbol, df in historical_data.items():
                if coin_symbol != 'BTC' and df is not None:
                    try:
                        df = df.copy()
                        df['date'] = pd.to_datetime(df['date'])
                        df = df.set_index('date')
                        
                        # Объединение данных по датам
                        merged = btc_data[['price']].join(df[['price']], rsuffix='_alt', how='inner')
                        
                        if len(merged) > 10:
                            correlation = merged['price'].corr(merged['price_alt'])
                            if pd.notna(correlation):
                                correlations.append({
                                    'coin': coin_symbol,
                                    'correlation': f"{correlation:.3f}"
                                })
                    except Exception as e:
                        logger.debug(f"Error calculating correlation for {coin_symbol}: {e}")
                        continue
        
        # Сортировка корреляций
        correlations.sort(key=lambda x: float(x['correlation']), reverse=True)
        
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
                'plotly_data': {
                    'data': plotly_data,
                    'annotations': annotations,
                    'shapes': shapes
                },
                'correlations': correlations[:20]  # Топ 20 корреляций
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in Plotly market analysis: {str(e)}")
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

def create_market_chart_screenshot():
    """
    Создает скриншот графика рынка для отправки в Telegram
    
    Returns:
        bytes: PNG изображение графика или None в случае ошибки
    """
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        import plotly.io as pio
        from crypto_analyzer_cryptocompare import CryptoAnalyzer
        from data_cache import DataCache
        import pandas as pd
        
        # Инициализация
        cache = DataCache()
        analyzer = CryptoAnalyzer(cache)
        
        # Параметры анализа
        top_n = 50
        ma_period = 200
        history_days = 1095  # 3 года для Telegram графика
        
        # Получение данных
        top_coins = analyzer.get_top_coins(top_n)
        if not top_coins:
            logger.error("Не удалось получить список топ монет для скриншота")
            return None
        
        # Загрузка исторических данных
        historical_data = analyzer.load_historical_data(
            top_coins, 
            ma_period + history_days + 100
        )
        
        if not historical_data:
            logger.error("Не удалось загрузить исторические данные для скриншота")
            return None
        
        # Расчет индикатора
        indicator_data = analyzer.calculate_market_breadth(
            historical_data, 
            ma_period, 
            history_days
        )
        
        if indicator_data.empty:
            logger.error("Не удалось рассчитать индикатор для скриншота")
            return None
        
        # Создание упрощенного графика для Telegram
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Bitcoin Price (USD)', '% Of Cryptocurrencies Above 200-Day Moving Average'),
            vertical_spacing=0.08,
            row_heights=[0.6, 0.4]
        )
        
        # График Bitcoin (верхний)
        if 'BTC' in historical_data:
            btc_data = historical_data['BTC'].copy()
            logger.info(f"BTC data columns: {btc_data.columns.tolist()}")
            logger.info(f"BTC data shape: {btc_data.shape}")
            
            # Проверяем наличие нужных колонок
            if 'date' not in btc_data.columns:
                btc_data.reset_index(inplace=True)
            
            btc_data['date'] = pd.to_datetime(btc_data['date'])
            
            # Определяем правильное название колонки с ценой
            price_column = 'close'
            if 'close' not in btc_data.columns:
                # Попробуем найти альтернативные названия
                possible_names = ['Close', 'price', 'Price', 'last', 'Last']
                for name in possible_names:
                    if name in btc_data.columns:
                        price_column = name
                        break
                else:
                    # Если не нашли, используем первую числовую колонку
                    numeric_cols = btc_data.select_dtypes(include=[float, int]).columns
                    if len(numeric_cols) > 0:
                        price_column = numeric_cols[0]
                    else:
                        logger.error(f"Не найдена колонка с ценой Bitcoin: {btc_data.columns.tolist()}")
                        return None
            
            # Фильтрация по периоду анализа
            btc_recent = btc_data.tail(history_days)
            
            fig.add_trace(
                go.Scatter(
                    x=btc_recent['date'],
                    y=btc_recent[price_column],
                    name='Bitcoin',
                    line=dict(color='#f7931a', width=2),
                    showlegend=False
                ),
                row=1, col=1
            )
        
        # График индикатора (нижний)
        logger.info(f"Indicator data columns: {indicator_data.columns.tolist()}")
        logger.info(f"Indicator data shape: {indicator_data.shape}")
        
        # Определяем правильное название колонки с индикатором
        breadth_column = 'percentage_above_ma'
        if 'percentage_above_ma' not in indicator_data.columns:
            # Попробуем найти альтернативные названия
            possible_names = ['market_breadth', 'breadth', 'percentage', 'above_ma']
            for name in possible_names:
                if name in indicator_data.columns:
                    breadth_column = name
                    break
            else:
                # Если не нашли, используем первую числовую колонку
                numeric_cols = indicator_data.select_dtypes(include=[float, int]).columns
                if len(numeric_cols) > 0:
                    breadth_column = numeric_cols[0]
                else:
                    logger.error(f"Не найдена колонка с индикатором: {indicator_data.columns.tolist()}")
                    return None
        
        fig.add_trace(
            go.Scatter(
                x=pd.to_datetime(indicator_data.index),
                y=indicator_data[breadth_column],
                name='Market Breadth',
                line=dict(color='#2563EB', width=2),
                showlegend=False
            ),
            row=2, col=1
        )
        
        # Горизонтальные линии для зон
        fig.add_hline(y=80, line_dash="dash", line_color="red", opacity=0.7, row=2, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="gray", opacity=0.5, row=2, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="green", opacity=0.7, row=2, col=1)
        
        # Настройка макета
        fig.update_layout(
            title={
                'text': 'Cryptocurrency Market Analysis',
                'x': 0.5,
                'font': {'size': 20, 'color': '#2c3e50'}
            },
            height=600,
            width=800,
            font=dict(family="Arial", size=12),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        # Настройка осей
        fig.update_xaxes(
            gridcolor='lightgray',
            gridwidth=0.5,
            showgrid=True
        )
        fig.update_yaxes(
            gridcolor='lightgray',
            gridwidth=0.5,
            showgrid=True
        )
        
        # Создание PNG изображения с fallback на matplotlib
        try:
            img_bytes = pio.to_image(
                fig, 
                format='png',
                width=800,
                height=600,
                scale=2  # Высокое разрешение
            )
            logger.info("График для Telegram успешно создан через Kaleido")
            return img_bytes
        except Exception as kaleido_error:
            logger.warning(f"Kaleido не работает: {str(kaleido_error)}, пробуем matplotlib")
            
            # Fallback на matplotlib
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from io import BytesIO
            
            # Создаем график с matplotlib
            fig_mpl, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            # График Bitcoin (верхний)
            if 'BTC' in historical_data:
                btc_data = historical_data['BTC'].copy()
                if 'date' not in btc_data.columns:
                    btc_data.reset_index(inplace=True)
                btc_data['date'] = pd.to_datetime(btc_data['date'])
                
                # Определяем правильное название колонки с ценой
                price_column = 'price' if 'price' in btc_data.columns else 'close'
                if price_column not in btc_data.columns:
                    numeric_cols = btc_data.select_dtypes(include=[float, int]).columns
                    if len(numeric_cols) > 0:
                        price_column = numeric_cols[0]
                
                btc_recent = btc_data.tail(history_days)
                ax1.plot(btc_recent['date'], btc_recent[price_column], 
                        color='#f7931a', linewidth=2, label='Bitcoin')
                ax1.set_title('Bitcoin Price (USD)', fontsize=14, fontweight='bold')
                ax1.grid(True, alpha=0.3)
                ax1.set_ylabel('Price (USD)')
                
            # График индикатора (нижний)
            breadth_column = 'percentage'
            if breadth_column in indicator_data.columns:
                ax2.plot(pd.to_datetime(indicator_data.index), indicator_data[breadth_column],
                        color='#2563EB', linewidth=2, label='Market Breadth')
                
                # Горизонтальные линии
                ax2.axhline(y=80, color='red', linestyle='--', alpha=0.7, label='Overbought (80%)')
                ax2.axhline(y=50, color='gray', linestyle=':', alpha=0.5, label='Neutral (50%)')
                ax2.axhline(y=20, color='green', linestyle='--', alpha=0.7, label='Oversold (20%)')
                
                ax2.set_title('% Of Cryptocurrencies Above 200-Day Moving Average', fontsize=14, fontweight='bold')
                ax2.set_ylabel('Percentage (%)')
                ax2.grid(True, alpha=0.3)
                ax2.set_ylim(0, 100)
                
                # Форматирование дат
                ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
                ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
                
            plt.tight_layout()
            plt.suptitle('Cryptocurrency Market Analysis', fontsize=16, fontweight='bold', y=0.98)
            
            # Сохранение в BytesIO
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            img_bytes = img_buffer.getvalue()
            plt.close(fig_mpl)
            
            logger.info("График для Telegram успешно создан через matplotlib")
            return img_bytes
        
    except Exception as e:
        logger.error(f"Ошибка создания скриншота графика: {str(e)}")
        return None

def create_web_ui_chart_screenshot():
    """
    Создает график с точными параметрами веб-интерфейса
    """
    try:
        from crypto_analyzer_cryptocompare import CryptoAnalyzer
        from data_cache import DataCache
        import pandas as pd
        import plotly.graph_objects as go
        import plotly.io as pio
        from datetime import datetime, timedelta
        import numpy as np
        
        logger.info("Создание графика с параметрами веб-интерфейса...")
        
        # ТОЧНО ТЕ ЖЕ параметры что в веб-интерфейсе
        top_n = 50
        ma_period = 200
        history_days = 1095  # 3 года
        
        # Инициализация
        cache = DataCache()
        analyzer = CryptoAnalyzer(cache)
        
        # Получение данных
        top_coins = analyzer.get_top_coins(top_n)
        if not top_coins:
            logger.error("Не удалось получить топ монеты")
            return None
            
        # Загружаем достаточно данных для расчета
        total_days_needed = ma_period + history_days + 100
        historical_data = analyzer.load_historical_data(top_coins, total_days_needed)
        
        if not historical_data:
            logger.error("Не удалось загрузить исторические данные")
            return None
        
        # Расчет индикатора
        indicator_data = analyzer.calculate_market_breadth(
            historical_data, 
            ma_period, 
            history_days
        )
        
        if indicator_data.empty:
            logger.error("Не удалось рассчитать индикатор")
            return None
        
        logger.info(f"Рассчитан индикатор для {len(indicator_data)} дней")
        
        # Получение данных Bitcoin для верхнего графика
        btc_data = None
        if 'BTC' in historical_data:
            btc_data = historical_data['BTC'].copy()
            btc_data['date'] = pd.to_datetime(btc_data['date'])
            
            # Фильтрация по тому же периоду
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=history_days)
            btc_data = btc_data[
                (btc_data['date'].dt.date >= start_date) & 
                (btc_data['date'].dt.date <= end_date)
            ].sort_values('date')
        
        # Создание ТОЧНО ТАКОГО ЖЕ графика как в веб-интерфейсе
        fig = go.Figure()
        
        # Bitcoin график (верхний)
        if btc_data is not None and not btc_data.empty:
            fig.add_trace(go.Scatter(
                x=btc_data['date'],
                y=btc_data['price'],
                mode='lines',
                name='Bitcoin',
                line=dict(color='#FF6B35', width=2),
                yaxis='y1'
            ))
        
        # Market breadth график (нижний)
        indicator_filtered = indicator_data.tail(history_days)
        dates = pd.to_datetime(indicator_filtered.index)
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=indicator_filtered['percentage'],
            mode='lines',
            name='% Of Cryptocurrencies Above 200-Day Moving Average',
            line=dict(color='#2563EB', width=2),
            yaxis='y2'
        ))
        
        # Layout точно как в веб-интерфейсе
        fig.update_layout(
            title=dict(
                text='',
                x=0.5,
                font=dict(size=16, color='#2D3748')
            ),
            showlegend=True,
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=60, r=60, t=80, b=120),
            height=700,
            width=1200,
            font=dict(family="Arial, sans-serif", size=12, color='#4A5568'),
            
            # Двойная ось Y
            yaxis=dict(
                title='Bitcoin Price (USD)',
                side='left',
                titlefont=dict(color='#FF6B35'),
                tickfont=dict(color='#FF6B35'),
                domain=[0.55, 1],
                showgrid=True,
                gridcolor='#E2E8F0',
                gridwidth=1
            ),
            yaxis2=dict(
                title='Percentage (%)',
                side='left',
                titlefont=dict(color='#2563EB'),
                tickfont=dict(color='#2563EB'),
                domain=[0, 0.45],
                range=[0, 100],
                showgrid=True,
                gridcolor='#E2E8F0',
                gridwidth=1
            ),
            xaxis=dict(
                title='Date',
                showgrid=True,
                gridcolor='#E2E8F0',
                gridwidth=1,
                domain=[0, 1]
            ),
            legend=dict(
                x=0.02,
                y=0.98,
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='#CBD5E0',
                borderwidth=1
            )
        )
        
        # Добавляем зоны на нижний график
        fig.add_hline(y=80, line=dict(color='#FCA5A5', width=1, dash='dash'), yref='y2')
        fig.add_hline(y=50, line=dict(color='#9CA3AF', width=1, dash='dash'), yref='y2')
        fig.add_hline(y=20, line=dict(color='#86EFAC', width=1, dash='dash'), yref='y2')
        
        # Добавляем цветные зоны
        fig.add_hrect(y0=80, y1=100, fillcolor='#FEF2F2', opacity=0.3, yref='y2')
        fig.add_hrect(y0=20, y1=80, fillcolor='#F9FAFB', opacity=0.2, yref='y2')
        fig.add_hrect(y0=0, y1=20, fillcolor='#F0FDF4', opacity=0.3, yref='y2')
        
        # Конвертация в PNG
        try:
            img_bytes = pio.to_image(
                fig, 
                format='png',
                width=1200,
                height=700,
                scale=2
            )
            logger.info("График создан через Plotly успешно")
            return img_bytes
        except Exception as plotly_error:
            logger.error(f"Ошибка конвертации Plotly в PNG: {plotly_error}")
            # Fallback на matplotlib
            return create_matplotlib_fallback_chart(indicator_data, btc_data, history_days)
            
    except Exception as e:
        logger.error(f"Ошибка создания графика: {str(e)}")
        import traceback
        logger.error(f"Полная ошибка: {traceback.format_exc()}")
        return None

def create_matplotlib_fallback_chart(indicator_data, btc_data, history_days):
    """
    Fallback функция для создания графика через matplotlib
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from io import BytesIO
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        fig.patch.set_facecolor('white')
        
        # Bitcoin график
        if btc_data is not None and not btc_data.empty:
            ax1.plot(btc_data['date'], btc_data['price'], 
                    color='#FF6B35', linewidth=2, label='Bitcoin')
            ax1.set_title('Bitcoin Price (USD)', fontsize=14, fontweight='bold', color='#2D3748')
            ax1.set_ylabel('Bitcoin Price (USD)', fontsize=12, color='#4A5568')
            ax1.grid(True, alpha=0.3, color='#E2E8F0')
        
        # Market breadth график
        indicator_filtered = indicator_data.tail(history_days)
        dates = pd.to_datetime(indicator_filtered.index)
        
        ax2.plot(dates, indicator_filtered['percentage'], 
                color='#2563EB', linewidth=2)
        
        # Зоны
        ax2.axhspan(80, 100, alpha=0.3, color='#FEF2F2')
        ax2.axhspan(0, 20, alpha=0.3, color='#F0FDF4')
        ax2.axhspan(20, 80, alpha=0.2, color='#F9FAFB')
        
        ax2.set_title('% Of Cryptocurrencies Above 200-Day Moving Average', 
                     fontsize=14, fontweight='bold', color='#2D3748')
        ax2.set_ylabel('Percentage (%)', fontsize=12, color='#4A5568')
        ax2.set_xlabel('Date', fontsize=12, color='#4A5568')
        ax2.set_ylim(0, 100)
        ax2.grid(True, alpha=0.3, color='#E2E8F0')
        
        plt.tight_layout()
        
        # Сохранение
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        img_buffer.seek(0)
        img_bytes = img_buffer.getvalue()
        plt.close(fig)
        
        logger.info("График создан через matplotlib fallback")
        return img_bytes
        
    except Exception as e:
        logger.error(f"Ошибка создания matplotlib fallback: {str(e)}")
        return None

def create_chart_from_web_endpoint():
    """
    Создает график точно как в веб-интерфейсе с 3-летними данными
    """
    try:
        logger.info("Создаем график точно как в веб-интерфейсе...")
        
        # Точные параметры веб-интерфейса
        top_n = 50
        ma_period = 200
        history_days = 1095  # 3 года как в веб-интерфейсе
        
        # Создаем график с точными параметрами веб-интерфейса
        return create_exact_web_interface_chart(top_n, ma_period, history_days)
            
    except Exception as e:
        logger.error(f"Ошибка создания графика веб-интерфейса: {str(e)}")
        return None

def create_exact_web_interface_chart(top_n, ma_period, history_days):
    """
    Создает график точно такой же как в веб-интерфейсе
    """
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        import pandas as pd
        from datetime import datetime, timedelta
        from crypto_analyzer_cryptocompare import CryptoAnalyzer
        from data_cache import DataCache
        from io import BytesIO
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        
        logger.info(f"Создаем точную копию веб-интерфейса: {top_n} монет, {ma_period}MA, {history_days} дней")
        
        # Инициализация точно как в веб-интерфейсе
        cache = DataCache()
        analyzer = CryptoAnalyzer(cache)
        
        # Получение данных
        top_coins = analyzer.get_top_coins(top_n)
        if not top_coins:
            logger.error("Не удалось получить топ монеты")
            return None
        
        # Исключаем стейблкоины как в веб-интерфейсе
        stablecoins = ['USDT', 'USDC', 'DAI']
        filtered_coins = [coin for coin in top_coins if coin['symbol'] not in stablecoins]
        logger.info(f"Отфильтровано {len(filtered_coins)} монет (исключены стейблкоины)")
        
        # Загружаем полные данные как в веб-интерфейсе
        total_days_needed = ma_period + history_days + 100
        historical_data = analyzer.load_historical_data(filtered_coins, total_days_needed)
        
        if not historical_data:
            logger.error("Не удалось загрузить исторические данные")
            return None
        
        # Расчет индикатора точно как в веб-интерфейсе
        indicator_data = analyzer.calculate_market_breadth(
            historical_data, 
            ma_period, 
            history_days
        )
        
        if indicator_data.empty:
            logger.error("Не удалось рассчитать индикатор")
            return None
            
        logger.info(f"Рассчитан индикатор для {len(indicator_data)} дней")
        
        # Создание двухпанельного графика как в веб-интерфейсе
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        fig.patch.set_facecolor('white')
        
        # Bitcoin график (верхняя панель)
        if 'BTC' in historical_data:
            btc_data = historical_data['BTC'].copy()
            btc_data['date'] = pd.to_datetime(btc_data['date'])
            
            # Фильтрация по точному периоду веб-интерфейса
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=history_days)
            btc_filtered = btc_data[
                (btc_data['date'].dt.date >= start_date) & 
                (btc_data['date'].dt.date <= end_date)
            ].sort_values('date')
            
            if not btc_filtered.empty:
                ax1.plot(btc_filtered['date'], btc_filtered['price'], 
                        color='#FF6B35', linewidth=2.5, label='Bitcoin')
                ax1.set_title('Bitcoin Price (USD)', 
                            fontsize=16, fontweight='bold', pad=20)
                ax1.set_ylabel('Bitcoin Price (USD)', fontsize=13)
                ax1.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
                ax1.tick_params(axis='both', which='major', labelsize=11)
                
                # Форматирование цены
                ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Market breadth график (нижняя панель) - точно как в веб-интерфейсе
        indicator_filtered = indicator_data.tail(history_days)
        dates = pd.to_datetime(indicator_filtered.index)
        
        # Основная линия индикатора
        ax2.plot(dates, indicator_filtered['percentage'], 
                color='#2563EB', linewidth=2.5, label='Market Breadth')
        
        # Цветные зоны точно как в веб-интерфейсе
        ax2.axhspan(80, 100, alpha=0.25, color='#FFE4E1', label='Overbought Zone (80%+)')
        ax2.axhspan(0, 20, alpha=0.25, color='#F0FFF0', label='Oversold Zone (20%-)')
        ax2.axhspan(20, 80, alpha=0.1, color='#F5F5F5', label='Neutral Zone (20%-80%)')
        
        # Горизонтальные линии
        ax2.axhline(y=80, color='#FF6B6B', linestyle='--', alpha=0.7, linewidth=1)
        ax2.axhline(y=50, color='#666666', linestyle='-', alpha=0.5, linewidth=1)
        ax2.axhline(y=20, color='#4ECDC4', linestyle='--', alpha=0.7, linewidth=1)
        
        # Заголовок точно как в веб-интерфейсе
        ax2.set_title('% Of Cryptocurrencies Above 200-Day Moving Average', 
                     fontsize=16, fontweight='bold', pad=20)
        ax2.set_ylabel('Percentage (%)', fontsize=13)
        ax2.set_xlabel('Date', fontsize=13)
        ax2.set_ylim(0, 100)
        ax2.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        ax2.tick_params(axis='both', which='major', labelsize=11)
        
        # Форматирование дат точно как в веб-интерфейсе
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        
        # Добавляем аннотацию как в веб-интерфейсе
        current_value = indicator_filtered['percentage'].iloc[-1]
        ax2.text(0.02, 0.98, 
                f'Current: {current_value:.1f}%\nAnalyzing {len(filtered_coins)} cryptocurrencies\nOver {history_days} days with {ma_period}-day MA',
                transform=ax2.transAxes, fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='gray'))
        
        # Общий заголовок
        plt.suptitle('📊 Cryptocurrency Market Breadth Analysis', 
                    fontsize=18, fontweight='bold', y=0.98)
        
        # Финальное оформление
        plt.tight_layout()
        plt.subplots_adjust(top=0.94, hspace=0.3)
        
        # Сохранение в высоком качестве
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=200, bbox_inches='tight', 
                   facecolor='white', edgecolor='none', 
                   pad_inches=0.2)
        img_buffer.seek(0)
        img_bytes = img_buffer.getvalue()
        plt.close(fig)
        
        logger.info("График веб-интерфейса создан успешно")
        return img_bytes
        
    except Exception as e:
        logger.error(f"Ошибка создания точного графика веб-интерфейса: {str(e)}")
        import traceback
        logger.error(f"Полная ошибка: {traceback.format_exc()}")
        return None

def create_quick_chart():
    """
    Создает график с сокращенным периодом для быстрой отправки
    """
    try:
        from crypto_analyzer_cryptocompare import CryptoAnalyzer
        from data_cache import DataCache
        import pandas as pd
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from io import BytesIO
        from datetime import datetime, timedelta
        
        logger.info("Создаем быстрый график...")
        
        # Сокращенные параметры для быстрой работы
        top_n = 30  # Меньше монет
        ma_period = 200
        history_days = 365  # 1 год вместо 3
        
        # Инициализация
        cache = DataCache()
        analyzer = CryptoAnalyzer(cache)
        
        # Получение данных
        top_coins = analyzer.get_top_coins(top_n)
        if not top_coins:
            logger.error("Не удалось получить топ монеты")
            return None
            
        # Загружаем меньше данных
        total_days_needed = ma_period + history_days + 50
        historical_data = analyzer.load_historical_data(top_coins, total_days_needed)
        
        if not historical_data:
            logger.error("Не удалось загрузить исторические данные")
            return None
        
        # Расчет индикатора
        indicator_data = analyzer.calculate_market_breadth(
            historical_data, 
            ma_period, 
            history_days
        )
        
        if indicator_data.empty:
            logger.error("Не удалось рассчитать индикатор")
            return None
        
        logger.info(f"Рассчитан индикатор для {len(indicator_data)} дней")
        
        # Создание графика через matplotlib (быстрее)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        fig.patch.set_facecolor('white')
        
        # Bitcoin график
        if 'BTC' in historical_data:
            btc_data = historical_data['BTC'].copy()
            btc_data['date'] = pd.to_datetime(btc_data['date'])
            
            # Фильтрация по периоду
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=history_days)
            btc_filtered = btc_data[
                (btc_data['date'].dt.date >= start_date) & 
                (btc_data['date'].dt.date <= end_date)
            ].sort_values('date')
            
            if not btc_filtered.empty:
                ax1.plot(btc_filtered['date'], btc_filtered['price'], 
                        color='#FF6B35', linewidth=2, label='Bitcoin')
                ax1.set_title('Bitcoin Price (USD)', fontsize=14, fontweight='bold')
                ax1.set_ylabel('Bitcoin Price (USD)', fontsize=12)
                ax1.grid(True, alpha=0.3)
        
        # Market breadth график
        indicator_filtered = indicator_data.tail(history_days)
        dates = pd.to_datetime(indicator_filtered.index)
        
        ax2.plot(dates, indicator_filtered['percentage'], 
                color='#2563EB', linewidth=2)
        
        # Зоны
        ax2.axhspan(80, 100, alpha=0.3, color='#FFE4E1', label='Overbought (80%+)')
        ax2.axhspan(0, 20, alpha=0.3, color='#F0FFF0', label='Oversold (20%-)')
        ax2.axhspan(20, 80, alpha=0.1, color='#F5F5F5', label='Neutral Zone')
        
        ax2.set_title('% Of Cryptocurrencies Above 200-Day Moving Average', 
                     fontsize=14, fontweight='bold')
        ax2.set_ylabel('Percentage (%)', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_ylim(0, 100)
        ax2.grid(True, alpha=0.3)
        
        # Форматирование дат
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        
        plt.suptitle('📊 Cryptocurrency Market Breadth Analysis', 
                    fontsize=16, fontweight='bold', y=0.98)
        plt.tight_layout()
        
        # Сохранение
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        img_buffer.seek(0)
        img_bytes = img_buffer.getvalue()
        plt.close(fig)
        
        logger.info("Быстрый график создан успешно")
        return img_bytes
        
    except Exception as e:
        logger.error(f"Ошибка создания быстрого графика: {str(e)}")
        import traceback
        logger.error(f"Полная ошибка: {traceback.format_exc()}")
        return None

def create_matplotlib_chart_from_data(market_data):
    """
    Создает график из готовых данных планировщика
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from io import BytesIO
        import pandas as pd
        
        logger.info("Создаем график из данных планировщика")
        
        indicator_data = market_data['indicator_data']
        
        # Создание графика
        fig, ax = plt.subplots(1, 1, figsize=(12, 6))
        fig.patch.set_facecolor('white')
        
        # Market breadth график
        dates = pd.to_datetime(indicator_data.index)
        
        ax.plot(dates, indicator_data['percentage'], 
                color='#2563EB', linewidth=2)
        
        # Зоны
        ax.axhspan(80, 100, alpha=0.3, color='#FFE4E1')
        ax.axhspan(0, 20, alpha=0.3, color='#F0FFF0')
        ax.axhspan(20, 80, alpha=0.1, color='#F5F5F5')
        
        ax.set_title('% Of Cryptocurrencies Above 200-Day Moving Average', 
                     fontsize=14, fontweight='bold')
        ax.set_ylabel('Percentage (%)', fontsize=12)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylim(0, 100)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Сохранение
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        img_buffer.seek(0)
        img_bytes = img_buffer.getvalue()
        plt.close(fig)
        
        logger.info("График из данных планировщика создан")
        return img_bytes
        
    except Exception as e:
        logger.error(f"Ошибка создания графика из данных: {str(e)}")
        return None

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
