from flask import Blueprint, jsonify, render_template, request
from history_api import HistoryAPI
from datetime import datetime

# Создаем Blueprint для маршрутов истории
history_bp = Blueprint('history', __name__)
history_api = HistoryAPI()

def format_timestamp(timestamp):
    """Форматирует timestamp для отображения в API"""
    if isinstance(timestamp, datetime):
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(timestamp, str):
        try:
            dt = datetime.fromisoformat(timestamp)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            return timestamp
    return timestamp

@history_bp.route('/history')
def history_page():
    """Отображает страницу с историей рейтинга"""
    # Загружаем историю из JSON-файлов
    rank_history = history_api.get_rank_history(limit=100)
    fear_greed_history = history_api.get_fear_greed_history(limit=100)
    trends_history = history_api.get_google_trends_history(limit=100)
    
    return render_template(
        'history.html', 
        rank_history=rank_history,
        fear_greed_history=fear_greed_history,
        trends_history=trends_history
    )

@history_bp.route('/api/history/rank')
def api_rank_history():
    """API-эндпоинт для получения истории рейтинга"""
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    rank_history = history_api.get_rank_history(limit=limit, offset=offset)
    
    # Форматируем timestamp для API
    for entry in rank_history:
        if 'timestamp' in entry:
            entry['timestamp'] = format_timestamp(entry['timestamp'])
    
    return jsonify({
        'status': 'success',
        'count': len(rank_history),
        'data': rank_history
    })

@history_bp.route('/api/history/fear-greed')
def api_fear_greed_history():
    """API-эндпоинт для получения истории индекса страха и жадности"""
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    fear_greed_history = history_api.get_fear_greed_history(limit=limit, offset=offset)
    
    # Форматируем timestamp для API
    for entry in fear_greed_history:
        if 'timestamp' in entry:
            entry['timestamp'] = format_timestamp(entry['timestamp'])
    
    return jsonify({
        'status': 'success',
        'count': len(fear_greed_history),
        'data': fear_greed_history
    })

@history_bp.route('/api/history/trends')
def api_trends_history():
    """API-эндпоинт для получения истории данных Google Trends"""
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    trends_history = history_api.get_google_trends_history(limit=limit, offset=offset)
    
    # Форматируем timestamp для API
    for entry in trends_history:
        if 'timestamp' in entry:
            entry['timestamp'] = format_timestamp(entry['timestamp'])
    
    return jsonify({
        'status': 'success',
        'count': len(trends_history),
        'data': trends_history
    })