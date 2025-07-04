"""
Routes for MA200 Market Indicator
"""
import threading
import time
from flask import Blueprint, render_template, jsonify, request
from ma200_indicator import MA200Indicator

ma200_bp = Blueprint('ma200', __name__)

# Global variable to track background refresh status
background_refresh_status = {
    'running': False,
    'progress': 0,
    'total': 50,
    'current_coin': '',
    'started_at': None,
    'completed_at': None
}

def background_refresh_all_coins():
    """Background function to refresh all 50 coins data"""
    global background_refresh_status
    
    background_refresh_status['running'] = True
    background_refresh_status['progress'] = 0
    background_refresh_status['started_at'] = time.time()
    background_refresh_status['completed_at'] = None
    
    try:
        ma200_indicator = MA200Indicator()
        
        # Monkey patch the logger to capture progress
        original_info = ma200_indicator.logger.info
        def patched_info(message):
            if "Обрабатываем монету" in message and "/" in message:
                try:
                    # Extract progress from message like "Обрабатываем монету 5/50: BTC"
                    parts = message.split("Обрабатываем монету ")[1].split("/")
                    current = int(parts[0])
                    background_refresh_status['progress'] = current
                    background_refresh_status['current_coin'] = message.split(": ")[-1] if ": " in message else ""
                except:
                    pass
            return original_info(message)
        
        ma200_indicator.logger.info = patched_info
        
        # Run the calculation
        ma200_indicator.calculate_ma200_percentage(force_refresh=True)
        background_refresh_status['completed_at'] = time.time()
        background_refresh_status['progress'] = 50
        
    except Exception as e:
        print(f"Background refresh error: {e}")
    finally:
        background_refresh_status['running'] = False

@ma200_bp.route('/ma200')
def ma200_page():
    """MA200 indicator page - shows cached data or triggers background refresh"""
    try:
        ma200_indicator = MA200Indicator()
        
        # Попробуем получить данные из кеша без принудительного обновления
        cache = ma200_indicator.load_cache()
        
        if cache and len(cache) >= 10:
            # Есть кешированные данные - показываем их быстро
            cached_data = ma200_indicator._calculate_from_cache(cache)
            
            if cached_data is not None and not cached_data.empty:
                def convert_numpy_types(obj):
                    if hasattr(obj, 'item'):  # numpy scalar
                        return obj.item()
                    elif isinstance(obj, dict):
                        return {k: convert_numpy_types(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [convert_numpy_types(v) for v in obj]
                    return obj
                
                # Получаем данные для отображения
                ma200_data = ma200_indicator.get_ma200_indicator()
                
                if ma200_data:
                    return render_template('ma200_indicator.html', 
                                         ma200_data=convert_numpy_types(ma200_data),
                                         cache_info=f"Показаны данные {len(cache)} монет из кеша")
                else:
                    return render_template('ma200_indicator.html', 
                                         message="Данные загружаются в фоне...")
        else:
            # Нет кешированных данных - запускаем фоновое обновление
            if not background_refresh_status['running']:
                import threading
                thread = threading.Thread(target=background_refresh, args=(ma200_indicator,))
                thread.daemon = True
                thread.start()
                
            return render_template('ma200_indicator.html', 
                                 message="Загрузка данных запущена в фоне. Обновите страницу через минуту.")
            
    except Exception as e:
        return render_template('ma200_indicator.html', 
                             error=f"Ошибка: {str(e)}")

@ma200_bp.route('/api/ma200')
def get_ma200_data():
    """Get MA200 indicator data (uses cache if available)"""
    try:
        ma200_indicator = MA200Indicator()
        data = ma200_indicator.get_ma200_indicator()
        
        if data:
            # Convert numpy types to native Python types for JSON serialization
            def convert_numpy_types(obj):
                if hasattr(obj, 'item'):  # numpy scalar
                    return obj.item()
                elif isinstance(obj, dict):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(v) for v in obj]
                return obj
            
            return jsonify({
                'status': 'success',
                'data': convert_numpy_types(data)
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to retrieve MA200 Market Indicator data'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error: {str(e)}'
        })

@ma200_bp.route('/api/ma200/refresh', methods=['POST'])
def refresh_ma200():
    """Start background refresh of all 50 coins"""
    global background_refresh_status
    
    if background_refresh_status['running']:
        return jsonify({
            'status': 'already_running',
            'message': 'Background refresh already in progress',
            'progress': background_refresh_status['progress']
        })
    
    # Start background thread for full refresh
    thread = threading.Thread(target=background_refresh_all_coins)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'status': 'started',
        'message': 'Background refresh of all 50 coins started',
        'estimated_time': '2-3 minutes'
    })

@ma200_bp.route('/api/ma200/status')
def refresh_status():
    """Get status of background refresh"""
    return jsonify(background_refresh_status)

@ma200_bp.route('/api/ma200/chart')
def get_ma200_chart():
    """Serve the MA200 chart image"""
    try:
        from flask import send_file
        import os
        
        chart_path = 'ma200_chart.png'
        if os.path.exists(chart_path):
            return send_file(chart_path, mimetype='image/png')
        else:
            # Создаем график если его нет
            ma200_indicator = MA200Indicator()
            ma200_data = ma200_indicator.get_ma200_indicator()
            if ma200_data and ma200_data.get('chart_path'):
                return send_file(chart_path, mimetype='image/png')
            else:
                return "График недоступен", 404
    except Exception as e:
        return f"Ошибка загрузки графика: {str(e)}", 500