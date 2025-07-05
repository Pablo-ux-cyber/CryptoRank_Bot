import hashlib
import json
import os
from urllib.parse import urlparse

class URLShortener:
    """
    Простой URL shortener для скрытия адресов сервера в Telegram сообщениях
    """
    
    def __init__(self, base_url="https://short.ly", storage_file="short_urls.json"):
        self.base_url = base_url
        self.storage_file = storage_file
        self.urls = self._load_urls()
    
    def _load_urls(self):
        """Загружает сохраненные короткие URL из файла"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_urls(self):
        """Сохраняет короткие URL в файл"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.urls, f, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения URL: {e}")
    
    def _generate_short_code(self, url):
        """Генерирует короткий код для URL"""
        # Используем MD5 hash первых 6 символов
        hash_object = hashlib.md5(url.encode())
        return hash_object.hexdigest()[:6]
    
    def shorten_url(self, original_url):
        """
        Создает короткую ссылку для оригинального URL
        
        Args:
            original_url (str): Полный URL для сокращения
            
        Returns:
            str: Короткая ссылка
        """
        # Проверяем, есть ли уже такой URL
        for short_code, stored_url in self.urls.items():
            if stored_url == original_url:
                return f"{self.base_url}/{short_code}"
        
        # Создаем новый короткий код
        short_code = self._generate_short_code(original_url)
        
        # Если код уже существует, добавляем суффикс
        counter = 1
        original_code = short_code
        while short_code in self.urls:
            short_code = f"{original_code}{counter}"
            counter += 1
        
        # Сохраняем
        self.urls[short_code] = original_url
        self._save_urls()
        
        return f"{self.base_url}/{short_code}"
    
    def get_original_url(self, short_code):
        """
        Получает оригинальный URL по короткому коду
        
        Args:
            short_code (str): Короткий код
            
        Returns:
            str or None: Оригинальный URL или None если не найден
        """
        return self.urls.get(short_code)
    
    def create_chart_short_url(self, server_host):
        """
        Создает короткую ссылку для графика
        
        Args:
            server_host (str): Адрес сервера (например, request.host)
            
        Returns:
            str: Короткая ссылка
        """
        chart_url = f"/chart-view"
        short_code = self._generate_short_code(chart_url)
        
        # Проверяем, есть ли уже такой URL
        for code, stored_url in self.urls.items():
            if stored_url == chart_url:
                return f"https://{server_host}/s/{code}"
        
        # Создаем новый короткий код
        counter = 1
        original_code = short_code
        while short_code in self.urls:
            short_code = f"{original_code}{counter}"
            counter += 1
        
        # Сохраняем
        self.urls[short_code] = chart_url
        self._save_urls()
        
        return f"https://{server_host}/s/{short_code}"

# Глобальный экземпляр для использования в приложении
url_shortener = URLShortener()