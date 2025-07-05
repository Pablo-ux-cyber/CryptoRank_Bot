import requests
import base64
import json
import logging

logger = logging.getLogger(__name__)

class ImageUploader:
    """
    Загружает изображения на внешние сервисы для получения публичных ссылок
    без раскрытия адреса сервера
    """
    
    def __init__(self):
        pass
    
    def upload_to_imgbb(self, image_data, api_key=""):
        """
        Загружает изображение на imgbb.com (бесплатный сервис)
        
        Args:
            image_data (bytes): PNG данные изображения
            api_key (str): API ключ (можно использовать без регистрации)
            
        Returns:
            str or None: URL изображения или None в случае ошибки
        """
        try:
            # Кодируем изображение в base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            url = "https://api.imgbb.com/1/upload"
            
            # Используем бесплатный API без ключа (с ограничениями)
            payload = {
                'image': image_base64,
                'expiration': 600  # 10 минут
            }
            
            if api_key:
                payload['key'] = api_key
            
            response = requests.post(url, data=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result['data']['url']
            
            logger.error(f"ImgBB upload failed: {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"Error uploading to ImgBB: {str(e)}")
            return None
    
    def upload_to_telegra_ph(self, image_data):
        """
        Загружает изображение на telegra.ph (без регистрации)
        
        Args:
            image_data (bytes): PNG данные изображения
            
        Returns:
            str or None: URL изображения или None в случае ошибки
        """
        try:
            url = "https://telegra.ph/upload"
            
            files = {
                'file': ('chart.png', image_data, 'image/png')
            }
            
            response = requests.post(url, files=files, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return f"https://telegra.ph{result[0]['src']}"
            
            logger.error(f"Telegraph upload failed: {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"Error uploading to Telegraph: {str(e)}")
            return None
    
    def upload_to_0x0(self, image_data):
        """
        Загружает изображение на 0x0.st (бесплатный файлообменник)
        
        Args:
            image_data (bytes): PNG данные изображения
            
        Returns:
            str or None: URL изображения или None в случае ошибки
        """
        try:
            url = "https://0x0.st"
            
            files = {
                'file': ('chart.png', image_data, 'image/png')
            }
            
            response = requests.post(url, files=files, timeout=30)
            
            if response.status_code == 200:
                return response.text.strip()
            
            logger.error(f"0x0.st upload failed: {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"Error uploading to 0x0.st: {str(e)}")
            return None
    
    def upload_to_imgur(self, image_data, client_id=""):
        """
        Загружает изображение на imgur.com
        
        Args:
            image_data (bytes): PNG данные изображения 
            client_id (str): Client ID из Imgur API
            
        Returns:
            str or None: URL изображения или None в случае ошибки
        """
        try:
            # Кодируем изображение в base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            url = "https://api.imgur.com/3/image"
            
            headers = {}
            if client_id:
                headers['Authorization'] = f'Client-ID {client_id}'
            
            payload = {
                'image': image_base64,
                'type': 'base64'
            }
            
            response = requests.post(url, headers=headers, data=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result['data']['link']
            
            logger.error(f"Imgur upload failed: {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"Error uploading to Imgur: {str(e)}")
            return None
    
    def upload_chart(self, image_data):
        """
        Пытается загрузить изображение на различные сервисы
        
        Args:
            image_data (bytes): PNG данные изображения
            
        Returns:
            str or None: URL изображения или None если все сервисы недоступны
        """
        # Пробуем разные сервисы по очереди
        services = [
            self.upload_to_telegra_ph,
            self.upload_to_0x0,
            self.upload_to_imgbb,
        ]
        
        for service in services:
            try:
                url = service(image_data)
                if url:
                    logger.info(f"Image uploaded successfully: {url}")
                    return url
            except Exception as e:
                logger.warning(f"Service failed: {str(e)}")
                continue
        
        logger.error("All image upload services failed")
        return None

# Глобальный экземпляр
image_uploader = ImageUploader()