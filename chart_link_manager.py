import json
import hashlib
import time
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ChartLinkManager:
    """
    Создает временные скрытые ссылки на графики без раскрытия адреса сервера
    """
    
    def __init__(self, links_file="chart_links.json"):
        self.links_file = links_file
        self.links = self._load_links()
    
    def _load_links(self):
        """Загружает существующие ссылки из файла"""
        try:
            if os.path.exists(self.links_file):
                with open(self.links_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading links: {str(e)}")
        return {}
    
    def _save_links(self):
        """Сохраняет ссылки в файл"""
        try:
            with open(self.links_file, 'w') as f:
                json.dump(self.links, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving links: {str(e)}")
    
    def _generate_short_code(self, chart_data):
        """Генерирует уникальный короткий код для графика"""
        # Создаем хеш на основе данных и времени
        content = f"{chart_data}_{int(time.time())}"
        hash_obj = hashlib.md5(content.encode())
        return hash_obj.hexdigest()[:8]
    
    def create_chart_link(self, chart_data, expiry_hours=24):
        """
        Создает временную ссылку на график
        
        Args:
            chart_data (bytes): PNG данные графика
            expiry_hours (int): Срок действия ссылки в часах
            
        Returns:
            str: Короткий код для доступа к графику
        """
        try:
            # Генерируем короткий код
            short_code = self._generate_short_code(str(chart_data))
            
            # Сохраняем данные графика во временный файл
            chart_filename = f"temp_chart_{short_code}.png"
            with open(chart_filename, 'wb') as f:
                f.write(chart_data)
            
            # Время истечения
            expiry_time = datetime.now() + timedelta(hours=expiry_hours)
            
            # Сохраняем информацию о ссылке
            self.links[short_code] = {
                'filename': chart_filename,
                'created': datetime.now().isoformat(),
                'expiry': expiry_time.isoformat(),
                'accessed': 0
            }
            
            self._save_links()
            logger.info(f"Chart link created: {short_code}")
            
            return short_code
            
        except Exception as e:
            logger.error(f"Error creating chart link: {str(e)}")
            return None
    
    def get_chart_data(self, short_code):
        """
        Получает данные графика по короткому коду
        
        Args:
            short_code (str): Короткий код графика
            
        Returns:
            bytes or None: PNG данные графика или None если не найден/истек
        """
        try:
            if short_code not in self.links:
                return None
            
            link_info = self.links[short_code]
            
            # Проверяем срок действия
            expiry_time = datetime.fromisoformat(link_info['expiry'])
            if datetime.now() > expiry_time:
                self._cleanup_expired_link(short_code)
                return None
            
            # Читаем файл графика
            filename = link_info['filename']
            if not os.path.exists(filename):
                return None
            
            with open(filename, 'rb') as f:
                chart_data = f.read()
            
            # Увеличиваем счетчик обращений
            link_info['accessed'] += 1
            self._save_links()
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error getting chart data: {str(e)}")
            return None
    
    def _cleanup_expired_link(self, short_code):
        """Удаляет истекшую ссылку и файл"""
        try:
            if short_code in self.links:
                link_info = self.links[short_code]
                filename = link_info['filename']
                
                # Удаляем файл
                if os.path.exists(filename):
                    os.remove(filename)
                
                # Удаляем из списка
                del self.links[short_code]
                self._save_links()
                
                logger.info(f"Expired chart link cleaned up: {short_code}")
                
        except Exception as e:
            logger.error(f"Error cleaning up expired link: {str(e)}")
    
    def cleanup_all_expired(self):
        """Удаляет все истекшие ссылки"""
        current_time = datetime.now()
        expired_codes = []
        
        for short_code, link_info in self.links.items():
            expiry_time = datetime.fromisoformat(link_info['expiry'])
            if current_time > expiry_time:
                expired_codes.append(short_code)
        
        for code in expired_codes:
            self._cleanup_expired_link(code)
        
        logger.info(f"Cleaned up {len(expired_codes)} expired chart links")
    
    def get_public_url(self, short_code, base_url="https://replit.app"):
        """
        Создает публичную ссылку (но не раскрывает настоящий адрес)
        
        Args:
            short_code (str): Короткий код графика
            base_url (str): Базовый URL (можно использовать поддельный)
            
        Returns:
            str: Публичная ссылка на график
        """
        return f"{base_url}/chart/{short_code}"

# Глобальный экземпляр
chart_link_manager = ChartLinkManager()