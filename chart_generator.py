import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io
import base64
import logging

logger = logging.getLogger(__name__)

class ChartGenerator:
    """
    Генератор графиков для индикаторов криптовалютного рынка
    """
    
    def __init__(self):
        """Инициализация генератора графиков"""
        # Настройка matplotlib для работы без GUI
        plt.switch_backend('Agg')
        
        # Настройка стиля
        plt.style.use('dark_background')
        
        logger.info("Chart generator initialized")
    
    def create_market_breadth_chart(self, market_breadth_data, save_path=None):
        """
        Создает график индикатора ширины рынка
        
        Args:
            market_breadth_data (dict): Данные индикатора ширины рынка
            save_path (str, optional): Путь для сохранения файла
            
        Returns:
            str: Путь к сохраненному файлу или base64 строка
        """
        try:
            # Создаем фигуру и оси
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Получаем текущие данные
            current_percentage = market_breadth_data['breadth_percentage']
            above_count = market_breadth_data['above_ma200_count']
            total_count = market_breadth_data['total_analyzed']
            market_condition = market_breadth_data['market_condition']
            timestamp = market_breadth_data['timestamp']
            
            # Создаем круговую диаграмму
            sizes = [above_count, total_count - above_count]
            labels = [f'Above MA200\n{above_count} coins', f'Below MA200\n{total_count - above_count} coins']
            colors = ['#00ff88', '#ff4444']
            explode = (0.05, 0)  # Выделяем зеленый сектор
            
            # Создаем pie chart
            pie_result = ax.pie(sizes, labels=labels, colors=colors, 
                               explode=explode, autopct='%1.1f%%', 
                               startangle=90, textprops={'fontsize': 12})
            
            # Распаковываем результат
            if len(pie_result) == 3:
                wedges, texts, autotexts = pie_result
                # Настройка цветов текста для autopct
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
            else:
                wedges, texts = pie_result
                autotexts = []
            
            # Настройка цветов текста для labels
            for text in texts:
                text.set_color('white')
                text.set_fontweight('bold')
            
            # Заголовок
            ax.set_title(f'Market Breadth Indicator\n{current_percentage:.1f}% - {market_condition}', 
                        fontsize=16, fontweight='bold', color='white', pad=20)
            
            # Добавляем информацию внизу
            info_text = f'Analysis Date: {timestamp.strftime("%Y-%m-%d %H:%M UTC")}\n'
            info_text += f'Sample: Top {total_count} cryptocurrencies\n'
            info_text += f'Technical: 200-day Moving Average'
            
            plt.figtext(0.5, 0.02, info_text, ha='center', va='bottom', 
                       fontsize=10, color='#cccccc')
            
            # Настройки фигуры
            plt.tight_layout()
            
            if save_path:
                # Сохраняем в файл
                plt.savefig(save_path, dpi=150, bbox_inches='tight', 
                           facecolor='#1a1a1a', edgecolor='none')
                plt.close()
                logger.info(f"Market breadth chart saved to {save_path}")
                return save_path
            else:
                # Возвращаем как base64
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                           facecolor='#1a1a1a', edgecolor='none')
                buffer.seek(0)
                
                image_base64 = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                buffer.close()
                
                logger.info("Market breadth chart generated as base64")
                return image_base64
                
        except Exception as e:
            logger.error(f"Error creating market breadth chart: {str(e)}")
            plt.close()
            return None
    
    def create_combined_indicators_chart(self, market_breadth_data, fear_greed_data=None, save_path=None):
        """
        Создает комбинированный график нескольких индикаторов
        
        Args:
            market_breadth_data (dict): Данные индикатора ширины рынка
            fear_greed_data (dict, optional): Данные индекса страха и жадности
            save_path (str, optional): Путь для сохранения файла
            
        Returns:
            str: Путь к сохраненному файлу или base64 строка
        """
        try:
            # Создаем фигуру с субплотами
            if fear_greed_data:
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
            else:
                fig, ax1 = plt.subplots(figsize=(12, 8))
                ax2 = None
            
            # График Market Breadth (левая панель)
            current_percentage = market_breadth_data['breadth_percentage']
            above_count = market_breadth_data['above_ma200_count']
            total_count = market_breadth_data['total_analyzed']
            
            sizes = [above_count, total_count - above_count]
            labels = [f'Above MA200\n{above_count} coins', f'Below MA200\n{total_count - above_count} coins']
            colors = ['#00ff88', '#ff4444']
            
            pie_result_1 = ax1.pie(sizes, labels=labels, colors=colors, 
                                   explode=(0.05, 0), autopct='%1.1f%%', 
                                   startangle=90, textprops={'fontsize': 10})
            
            # Распаковываем результат для первого графика
            if len(pie_result_1) == 3:
                wedges, texts, autotexts = pie_result_1
                # Настройка цветов текста для autopct
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
            else:
                wedges, texts = pie_result_1
                autotexts = []
            
            ax1.set_title(f'Market Breadth\n{current_percentage:.1f}%', 
                         fontsize=14, fontweight='bold', color='white')
            
            # Настройка цветов текста для labels
            for text in texts:
                text.set_color('white')
                text.set_fontweight('bold')
            
            # График Fear & Greed Index (правая панель)
            if fear_greed_data and ax2:
                fear_value = int(fear_greed_data['value'])
                fear_classification = fear_greed_data['classification']
                
                # Создаем gauge chart для Fear & Greed
                angles = np.linspace(0, np.pi, 100)
                values = np.linspace(0, 100, 100)
                
                # Цветовая схема для Fear & Greed
                colors_fg = []
                for val in values:
                    if val <= 25:
                        colors_fg.append('#ff0000')  # Extreme Fear - красный
                    elif val <= 45:
                        colors_fg.append('#ff8800')  # Fear - оранжевый
                    elif val <= 55:
                        colors_fg.append('#ffff00')  # Neutral - желтый
                    elif val <= 75:
                        colors_fg.append('#88ff00')  # Greed - светло-зеленый
                    else:
                        colors_fg.append('#00ff00')  # Extreme Greed - зеленый
                
                # Создаем полукруг
                for i in range(len(angles)-1):
                    ax2.fill_between([angles[i], angles[i+1]], [0, 0], [1, 1], 
                                   color=colors_fg[i], alpha=0.8)
                
                # Указатель для текущего значения
                current_angle = (fear_value / 100) * np.pi
                ax2.arrow(0, 0, np.cos(current_angle) * 0.8, np.sin(current_angle) * 0.8,
                         head_width=0.1, head_length=0.1, fc='white', ec='white', linewidth=3)
                
                # Настройки осей
                ax2.set_xlim(-1.2, 1.2)
                ax2.set_ylim(-0.2, 1.2)
                ax2.set_aspect('equal')
                ax2.axis('off')
                
                # Подписи
                ax2.text(0, -0.1, f'{fear_value}', ha='center', va='center', 
                        fontsize=24, fontweight='bold', color='white')
                ax2.set_title(f'Fear & Greed Index\n{fear_classification}', 
                             fontsize=14, fontweight='bold', color='white')
                
                # Подписи значений
                ax2.text(-1, 0, '0\nExtreme\nFear', ha='center', va='center', 
                        fontsize=8, color='white')
                ax2.text(1, 0, '100\nExtreme\nGreed', ha='center', va='center', 
                        fontsize=8, color='white')
                ax2.text(0, 1, '50\nNeutral', ha='center', va='center', 
                        fontsize=8, color='white')
            
            # Общий заголовок
            fig.suptitle('Cryptocurrency Market Indicators', 
                        fontsize=18, fontweight='bold', color='white', y=0.95)
            
            # Информация внизу
            timestamp = market_breadth_data['timestamp']
            info_text = f'Updated: {timestamp.strftime("%Y-%m-%d %H:%M UTC")}'
            plt.figtext(0.5, 0.02, info_text, ha='center', va='bottom', 
                       fontsize=10, color='#cccccc')
            
            plt.tight_layout()
            
            if save_path:
                # Сохраняем в файл
                plt.savefig(save_path, dpi=150, bbox_inches='tight', 
                           facecolor='#1a1a1a', edgecolor='none')
                plt.close()
                logger.info(f"Combined indicators chart saved to {save_path}")
                return save_path
            else:
                # Возвращаем как base64
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                           facecolor='#1a1a1a', edgecolor='none')
                buffer.seek(0)
                
                image_base64 = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                buffer.close()
                
                logger.info("Combined indicators chart generated as base64")
                return image_base64
                
        except Exception as e:
            logger.error(f"Error creating combined chart: {str(e)}")
            plt.close()
            return None