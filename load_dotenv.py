"""
Модуль для загрузки переменных окружения из .env файла
"""
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def load_dotenv(dotenv_path=None):
    """
    Загружает переменные окружения из .env файла
    
    Args:
        dotenv_path (str, optional): Путь к .env файлу. По умолчанию ищет .env в текущей директории.
    
    Returns:
        bool: True если переменные загружены успешно, False в противном случае
    """
    try:
        # Если путь не указан, используем .env в текущей директории
        if dotenv_path is None:
            dotenv_path = Path(os.path.dirname(os.path.abspath(__file__))) / ".env"
        
        # Проверяем существование файла
        if not os.path.exists(dotenv_path):
            logger.warning(f"Файл .env не найден по пути: {dotenv_path}")
            return False
            
        # Открываем файл и читаем переменные
        with open(dotenv_path, "r") as f:
            for line in f:
                line = line.strip()
                # Пропускаем комментарии и пустые строки
                if not line or line.startswith("#"):
                    continue
                    
                # Разбиваем строку на имя и значение
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Удаляем кавычки, если они есть
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                        
                    # Устанавливаем переменную окружения
                    os.environ[key] = value
                    
        logger.info(f"Переменные окружения успешно загружены из файла: {dotenv_path}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке переменных окружения: {str(e)}")
        return False