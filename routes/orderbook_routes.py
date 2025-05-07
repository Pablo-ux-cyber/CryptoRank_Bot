#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from order_book_imbalance import OrderBookImbalance
from history_api import HistoryAPI

orderbook_bp = Blueprint('orderbook', __name__)
order_book_imbalance = OrderBookImbalance()
history_api = HistoryAPI()

@orderbook_bp.route('/orderbook')
def orderbook_page():
    """
    Отображает страницу с данными Order Book Imbalance и историей
    """
    # Получаем историю данных для графика
    history = history_api.get_order_book_imbalance_history(limit=100)
    
    # Получаем текущие данные
    current_data = order_book_imbalance.get_order_book_imbalance()
    
    # Форматируем данные для отображения
    formatted_history = []
    for record in sorted(history, key=lambda x: x.get('timestamp', ''), reverse=True):
        formatted_history.append({
            'timestamp': record.get('timestamp', ''),
            'signal': record.get('signal', '⚪'),
            'description': record.get('description', ''),
            'status': record.get('status', 'Neutral'),
            'imbalance': record.get('imbalance', 0.0)
        })
    
    return render_template('orderbook_imbalance.html', 
                          imbalance_data=current_data,
                          imbalance_history=formatted_history)

@orderbook_bp.route('/api/orderbook/refresh', methods=['POST'])
def refresh_orderbook():
    """
    API для принудительного обновления данных Order Book Imbalance
    """
    try:
        # Принудительно получаем новые данные
        data = order_book_imbalance.get_order_book_imbalance()
        
        # Сохраняем данные в историю
        if data:
            history_api.save_order_book_imbalance_history(
                signal=data['signal'],
                description=data['description'],
                status=data['status'],
                imbalance=data['imbalance']
            )
            
        return jsonify({
            'status': 'success', 
            'data': data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@orderbook_bp.route('/api/orderbook/data')
def get_orderbook_data():
    """
    API для получения текущих данных Order Book Imbalance
    """
    try:
        # Получаем данные
        data = order_book_imbalance.get_order_book_imbalance()
        return jsonify({
            'status': 'success', 
            'data': data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500