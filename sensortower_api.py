import requests
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SensorTowerParser:
    """
    Класс для получения и парсинга данных рейтинга приложения из SensorTower API.

    Извлекает историю позиций приложения в рейтинге по дням и сохраняет результат в JSON-файл.
    """
    API_URL = (
        "https://app.sensortower.com/api/ios/category/category_history?"
        "app_ids%5B%5D=886427730&categories%5B%5D=6015&categories%5B%5D=0&categories%5B%5D=36&"
        "chart_type_ids%5B%5D=topfreeipadapplications&chart_type_ids%5B%5D=topfreeapplications&"
        "chart_type_ids%5B%5D=toppaidapplications&countries%5B%5D=US&end_date=2025-07-03&start_date=2025-06-04"
    )

    def __init__(self, url=None):
        """
        Инициализация парсера.

        :param url: (str, optional) URL для запроса к API. Если не указан, используется стандартный API_URL.
        """
        self.url = url or self.API_URL

    def fetch_data(self):
        """
        Выполняет GET-запрос к API и возвращает ответ в формате JSON.

        :return: (dict) Данные, полученные из API.
        :raises: requests.HTTPError при ошибке запроса.
        """
        try:
            logger.info(f"Fetching data from SensorTower API: {self.url}")
            
            # Добавляем заголовки браузера для обхода блокировки
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            
            response = requests.get(self.url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            logger.info("Successfully fetched data from SensorTower API")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from SensorTower API: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response from SensorTower API: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching SensorTower data: {str(e)}")
            return None

    def parse_graph_data(self, data):
        """
        Извлекает из данных API историю позиций приложения по дням.

        :param data: (dict) Исходные данные, полученные из API.
        :return: (list of dict) Список словарей с ключами 'date' (строка, YYYY-MM-DD) и 'rank' (int).
        """
        try:
            graph_data = (
                data["886427730"]["US"]["36"]["topfreeapplications"]["graphData"]
            )
        except (KeyError, TypeError):
            logger.error("No graph data found in SensorTower API response")
            return []
        
        result = []
        for entry in graph_data:
            timestamp, rank, _ = entry
            date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
            result.append({"date": date, "rank": rank})
        return result

    def get_current_rank(self):
        """
        Получает текущий рейтинг приложения Coinbase.
        
        :return: Текущий рейтинг (int) или None при ошибке
        """
        try:
            data = self.fetch_data()
            if not data:
                logger.warning("No data received from SensorTower API")
                return None
                
            # Парсим график данных для получения рейтинга
            graph_data = self.parse_graph_data(data)
            if not graph_data:
                logger.warning("No graph data found in SensorTower API response")
                return None
                
            # Берем последний (самый свежий) рейтинг
            latest_entry = graph_data[-1]
            current_rank = latest_entry["rank"]
            
            logger.info(f"Successfully got current rank from SensorTower API: {current_rank}")
            return current_rank
            
        except Exception as e:
            logger.error(f"Error getting current rank from SensorTower API: {str(e)}")
            return None

    def save_to_json(self, parsed_data, filename="parsed_ranks.json"):
        """
        Сохраняет распарсенные данные в JSON-файл.

        :param parsed_data: (list of dict) Список данных для сохранения.
        :param filename: (str) Имя файла для сохранения.
        """
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=2)

    def run(self, save_path="parsed_ranks.json"):
        """
        Основной метод: получает данные, парсит их и сохраняет в файл.

        :param save_path: (str) Имя файла для сохранения результата.
        :return: (list of dict) Список распарсенных данных.
        """
        data = self.fetch_data()
        if not data:
            return []
        parsed = self.parse_graph_data(data)
        self.save_to_json(parsed, save_path)
        return parsed