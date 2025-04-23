#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from google_trends_pulse import GoogleTrendsPulse

trends_bp = Blueprint('trends', __name__)
trends_pulse = GoogleTrendsPulse()

@trends_bp.route('/trends')
def trends_page():
    """
    Отображает страницу с данными Google Trends Pulse и историей
    """
    # Получаем историю трендов для графика
    history = trends_pulse.history_data
    
    # Получаем текущие данные
    current_data = trends_pulse.get_trends_data()
    
    # Форматируем данные для отображения
    formatted_history = []
    for record in sorted(history, key=lambda x: x.get('timestamp', ''), reverse=True):
        formatted_history.append({
            'timestamp': record.get('timestamp', ''),
            'signal': record.get('signal', '⚪'),
            'description': record.get('description', ''),
            'fomo_score': record.get('fomo_score', 0),
            'fear_score': record.get('fear_score', 0),
            'general_score': record.get('general_score', 0),
            'fomo_to_fear_ratio': record.get('fomo_to_fear_ratio', 1.0)
        })
    
    return render_template('google_trends.html', 
                          trends_data=current_data,
                          trends_history=formatted_history)

@trends_bp.route('/api/trends/refresh', methods=['POST'])
def refresh_trends():
    """
    API для принудительного обновления данных Google Trends
    """
    try:
        # Принудительно получаем новые данные
        data = trends_pulse.refresh_trends_data()
        return jsonify({
            'status': 'success', 
            'data': data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@trends_bp.route('/api/trends/data')
def get_trends_data():
    """
    API для получения текущих данных Google Trends
    """
    try:
        # Получаем данные (кешированные или новые)
        data = trends_pulse.get_trends_data()
        return jsonify({
            'status': 'success', 
            'data': data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500