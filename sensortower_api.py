import requests
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SensorTowerParser:
    """
    Класс для получения и парсинга данных рейтинга приложения из SensorTower API.
    Извлекает текущий рейтинг приложения Coinbase из официального API.
    """
    
    def __init__(self, app_id="886427730"):
        """
        Инициализация парсера.
        
        :param app_id: ID приложения Coinbase в App Store
        """
        self.app_id = app_id
        self.base_url = "https://app.sensortower.com/api/ios/category/category_history"
        
    def _build_api_url(self, days_back=30):
        """
        Строит URL для запроса к SensorTower API
        
        :param days_back: Количество дней назад для получения данных
        :return: Полный URL для запроса
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        url = (
            f"{self.base_url}?"
            f"app_ids%5B%5D={self.app_id}&"
            f"categories%5B%5D=6015&categories%5B%5D=0&categories%5B%5D=36&"
            f"chart_type_ids%5B%5D=topfreeipadapplications&"
            f"chart_type_ids%5B%5D=topfreeapplications&"
            f"chart_type_ids%5B%5D=toppaidapplications&"
            f"countries%5B%5D=US&"
            f"end_date={end_date}&"
            f"start_date={start_date}"
        )
        return url

    def fetch_data(self, days_back=30, api_key=None):
        """
        Выполняет GET-запрос к API и возвращает ответ в формате JSON.
        
        :param days_back: Количество дней назад для получения данных
        :param api_key: API ключ для аутентификации (опционально)
        :return: Данные, полученные из API, или None при ошибке
        """
        try:
            url = self._build_api_url(days_back)
            headers = {}
            
            # Добавляем аутентификацию если предоставлен API ключ
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'
            
            logger.info("Attempting to fetch data from SensorTower API")
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 403:
                logger.warning("SensorTower API returned 403 Forbidden - authentication required")
                logger.info("SensorTower API requires authentication. Please provide API key for access.")
                return None
            elif response.status_code == 401:
                logger.warning("SensorTower API returned 401 Unauthorized - invalid API key")
                return None
            
            response.raise_for_status()
            
            data = response.json()
            logger.info("Successfully fetched data from SensorTower API")
            return data
            
        except requests.exceptions.RequestException as e:
            if "403" in str(e):
                logger.warning("SensorTower API access denied (403) - authentication required")
            elif "401" in str(e):
                logger.warning("SensorTower API authentication failed (401) - invalid credentials")
            else:
                logger.error(f"Error fetching data from SensorTower API: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response from SensorTower API: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching SensorTower data: {str(e)}")
            return None

    def get_current_rank(self, api_key=None):
        """
        Получает текущий рейтинг приложения Coinbase.
        
        :param api_key: API ключ для аутентификации (опционально)
        :return: Текущий рейтинг (int) или None при ошибке
        """
        try:
            data = self.fetch_data(days_back=7, api_key=api_key)  # Получаем данные за последнюю неделю
            if not data:
                logger.warning("No data received from SensorTower API")
                return None
                
            # Извлекаем данные графика для topfreeapplications (основная категория)
            try:
                graph_data = (
                    data[self.app_id]["US"]["36"]["topfreeapplications"]["graphData"]
                )
            except (KeyError, TypeError) as e:
                logger.error(f"Error extracting graph data: {str(e)}")
                logger.debug(f"Available data structure: {list(data.keys()) if data else 'No data'}")
                return None
            
            if not graph_data:
                logger.warning("No graph data available")
                return None
            
            # Получаем самую свежую запись (последний элемент)
            latest_entry = graph_data[-1]
            timestamp, rank, _ = latest_entry
            
            # Преобразуем timestamp в дату для логирования
            date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
            logger.info(f"Latest rank from SensorTower API: {rank} (date: {date})")
            
            return int(rank)
            
        except Exception as e:
            logger.error(f"Error getting current rank from SensorTower: {str(e)}")
            return None

    def parse_graph_data(self, data):
        """
        Извлекает из данных API историю позиций приложения по дням.
        
        :param data: Исходные данные, полученные из API
        :return: Список словарей с ключами 'date' и 'rank'
        """
        try:
            graph_data = (
                data[self.app_id]["US"]["36"]["topfreeapplications"]["graphData"]
            )
        except (KeyError, TypeError):
            logger.error("Error extracting graph data for parsing")
            return []
            
        result = []
        for entry in graph_data:
            timestamp, rank, _ = entry
            date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
            result.append({"date": date, "rank": rank})
            
        return result

    def save_to_json(self, parsed_data, filename="sensortower_ranks.json"):
        """
        Сохраняет распарсенные данные в JSON-файл.
        
        :param parsed_data: Список данных для сохранения
        :param filename: Имя файла для сохранения
        """
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(parsed_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Data saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving data to {filename}: {str(e)}")

    def get_rank_history(self, days_back=30, save_to_file=True):
        """
        Получает историю рейтингов за указанный период.
        
        :param days_back: Количество дней назад
        :param save_to_file: Сохранить данные в файл
        :return: Список данных с историей рейтингов
        """
        try:
            data = self.fetch_data(days_back)
            if not data:
                return []
                
            parsed = self.parse_graph_data(data)
            
            if save_to_file and parsed:
                self.save_to_json(parsed)
                
            logger.info(f"Retrieved {len(parsed)} rank history entries")
            return parsed
            
        except Exception as e:
            logger.error(f"Error getting rank history: {str(e)}")
            return []