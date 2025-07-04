#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, jsonify, request, send_file
from ma200_demo import MA200Demo
import os

ma200_bp = Blueprint('ma200', __name__)
ma200_indicator = MA200Demo()

@ma200_bp.route('/ma200')
def ma200_page():
    """
    Отображает страницу с данными MA200 индикатора и историей
    """
    try:
        # Получаем текущие данные
        current_data = ma200_indicator.get_demo_ma200_indicator()
        
        # Проверяем, есть ли файл с историческими данными
        history_data = []
        if os.path.exists(ma200_indicator.results_file):
            try:
                import pandas as pd
                df = pd.read_csv(ma200_indicator.results_file)
                # Берем последние 30 дней для отображения в таблице
                recent_data = df.tail(30)
                history_data = recent_data.to_dict('records')
            except Exception as e:
                ma200_indicator.logger.error(f"Ошибка загрузки исторических данных: {str(e)}")
        
        return render_template('ma200_indicator.html', 
                              ma200_data=current_data,
                              history_data=history_data)
    except Exception as e:
        ma200_indicator.logger.error(f"Ошибка отображения страницы MA200: {str(e)}")
        return render_template('ma200_indicator.html', 
                              ma200_data=None,
                              history_data=[],
                              error=str(e))

@ma200_bp.route('/api/ma200/refresh', methods=['POST'])
def refresh_ma200():
    """
    API для принудительного обновления данных MA200 индикатора
    """
    try:
        # Принудительно получаем новые данные
        data = ma200_indicator.get_demo_ma200_indicator()
        if data:
            return jsonify({
                'status': 'success', 
                'data': data
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to fetch MA200 data'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@ma200_bp.route('/api/ma200/data')
def get_ma200_data():
    """
    API для получения текущих данных MA200 индикатора
    """
    try:
        # Получаем данные (кешированные или новые)
        data = ma200_indicator.get_demo_ma200_indicator()
        if data:
            return jsonify({
                'status': 'success', 
                'data': data
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'No MA200 data available'
            }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@ma200_bp.route('/api/ma200/chart')
def get_ma200_chart():
    """
    API для получения графика MA200 индикатора
    """
    try:
        if os.path.exists(ma200_indicator.chart_file):
            return send_file(ma200_indicator.chart_file, mimetype='image/png')
        else:
            return jsonify({
                'status': 'error',
                'message': 'Chart file not found'
            }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@ma200_bp.route('/api/ma200/download-csv')
def download_ma200_csv():
    """
    API для скачивания CSV файла с данными MA200
    """
    try:
        if os.path.exists(ma200_indicator.results_file):
            return send_file(ma200_indicator.results_file, 
                           mimetype='text/csv',
                           as_attachment=True,
                           download_name='ma200_data.csv')
        else:
            return jsonify({
                'status': 'error',
                'message': 'CSV file not found'
            }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@ma200_bp.route('/api/ma200/history')
def get_ma200_history():
    """
    API для получения полной истории MA200 данных
    """
    try:
        if os.path.exists(ma200_indicator.results_file):
            import pandas as pd
            df = pd.read_csv(ma200_indicator.results_file)
            history = df.to_dict('records')
            return jsonify({
                'status': 'success', 
                'data': history
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'No historical data available'
            }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500