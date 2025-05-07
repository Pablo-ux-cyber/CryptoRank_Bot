#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from altcoin_season_index import AltcoinSeasonIndex
from history_api import HistoryAPI

altseason_bp = Blueprint('altseason', __name__)
altcoin_season_index = AltcoinSeasonIndex()
history_api = HistoryAPI()

@altseason_bp.route('/altseason')
def altseason_page():
    """
    Отображает страницу с данными Altcoin Season Index и историей
    """
    # Получаем историю данных для графика
    history = history_api.get_altseason_index_history(limit=100)
    
    # Получаем текущие данные
    current_data = altcoin_season_index.get_altseason_index()
    
    # Форматируем данные для отображения
    formatted_history = []
    for record in sorted(history, key=lambda x: x.get('timestamp', ''), reverse=True):
        formatted_history.append({
            'timestamp': record.get('timestamp', ''),
            'signal': record.get('signal', '⚪'),
            'description': record.get('description', ''),
            'status': record.get('status', 'Neutral'),
            'index': record.get('index', 0.0),
            'btc_performance': record.get('btc_performance', 0.0)
        })
    
    return render_template('altseason_index.html', 
                          altseason_data=current_data,
                          altseason_history=formatted_history)

@altseason_bp.route('/api/altseason/refresh', methods=['POST'])
def refresh_altseason():
    """
    API для принудительного обновления данных Altcoin Season Index
    """
    try:
        # Принудительно получаем новые данные
        data = altcoin_season_index.get_altseason_index()
        
        # Проверяем, что данные получены успешно
        if data is None:
            return jsonify({
                'status': 'error',
                'message': 'Failed to retrieve Altcoin Season Index data. CoinGecko API may be unavailable or rate-limited.'
            }), 400
        
        # Сохраняем данные в историю
        try:
            history_api.save_altseason_index_history(
                signal=data.get('signal', '⚪'),
                description=data.get('description', 'Neutral market'),
                status=data.get('status', 'Neutral'),
                index=data.get('index', 0.0),
                btc_performance=data.get('btc_performance', 0.0)
            )
        except Exception as history_error:
            # Логируем ошибку сохранения в историю, но не прерываем общий ответ
            altcoin_season_index.logger.error(f"Error saving to history: {str(history_error)}")
            
        return jsonify({
            'status': 'success', 
            'data': data
        })
    except Exception as e:
        altcoin_season_index.logger.error(f"Error in refresh_altseason API: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@altseason_bp.route('/api/altseason/data')
def get_altseason_data():
    """
    API для получения текущих данных Altcoin Season Index
    """
    try:
        # Получаем данные
        data = altcoin_season_index.get_altseason_index()
        
        if data is None:
            return jsonify({
                'status': 'error',
                'message': 'Unable to get Altcoin Season Index data. CoinGecko API may be unavailable or rate-limited.'
            }), 404
            
        return jsonify({
            'status': 'success', 
            'data': data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500