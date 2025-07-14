import os
import time
import threading
import signal
import subprocess
from datetime import datetime, timedelta
import fcntl
from config import LOG_FILE
from logger import logger
from scraper import SensorTowerScraper
from telegram_bot import TelegramBot
from fear_greed_index import FearGreedIndexTracker
from altcoin_season_index import AltcoinSeasonIndex

class SensorTowerScheduler:
    """
    Планировщик для автоматического запуска задач скрапинга SensorTower
    """
    
    def __init__(self):
        """
        Инициализировать планировщик
        """
        self.scraper = SensorTowerScraper()
        self.telegram_bot = TelegramBot()
        self.fear_greed_tracker = FearGreedIndexTracker()
        self.altcoin_season_index = AltcoinSeasonIndex()
        self.market_breadth = None  # Will be initialized if needed
        
        # Переменные для отслеживания состояния
        self.stop_event = threading.Event()
        self.last_sent_rank = None
        self.rank_history_file = os.path.join(os.getcwd(), "rank_history.txt")
        self.lock_file = os.path.join(os.getcwd(), "coinbasebot.lock")
        self.lock_fd = None
        
        # Переменные для веб-интерфейса
        self.last_run_time = None
        self.last_run_status = None
        self.next_run_time = None
        
        logger.info(f"Файл истории рейтинга будет храниться по пути: {self.rank_history_file}")
        
        # Загружаем последний отправленный рейтинг из файла (если существует)
        self._load_last_sent_rank()
        
        # Получаем блокировку файла
        self._acquire_file_lock()
        
    def _load_last_sent_rank(self):
        """
        Загружаем последний отправленный рейтинг из файла
        """
        try:
            if os.path.exists(self.rank_history_file):
                with open(self.rank_history_file, "r") as f:
                    content = f.read().strip()
                    if content and content.isdigit():
                        self.last_sent_rank = int(content)
                        logger.info(f"Загружен предыдущий рейтинг из файла: {self.last_sent_rank}")
                    else:
                        logger.info("Файл истории рейтинга пуст или содержит некорректные данные")
                        self.last_sent_rank = None
            else:
                logger.info("Файл истории рейтинга не найден, начинаем с чистого листа")
                self.last_sent_rank = None
        except Exception as e:
            logger.error(f"Ошибка при загрузке последнего рейтинга из файла: {str(e)}")
            self.last_sent_rank = None
    
    def _acquire_file_lock(self):
        """
        Получение блокировки файла для предотвращения запуска нескольких экземпляров
        """
        logger.info(f"Файл блокировки будет храниться по пути: {self.lock_file}")
        
        try:
            # Проверяем, существует ли старый файл блокировки
            if os.path.exists(self.lock_file):
                # Проверяем возраст файла блокировки
                lock_age_minutes = (time.time() - os.path.getmtime(self.lock_file)) / 60
                if lock_age_minutes > 60:  # Если файл старше 60 минут
                    os.remove(self.lock_file)
                    logger.info(f"Удален устаревший файл блокировки (возраст: {lock_age_minutes:.1f} минут)")
                else:
                    logger.warning(f"Найден активный файл блокировки (возраст: {lock_age_minutes:.1f} минут)")
                    # Не выходим, продолжаем попытку получения блокировки
            
            # Создаем файл блокировки и пытаемся получить эксклюзивную блокировку
            self.lock_fd = os.open(self.lock_file, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Записываем PID в файл блокировки
            os.write(self.lock_fd, str(os.getpid()).encode())
            os.fsync(self.lock_fd)
            
            logger.info("Получена блокировка файла. Этот экземпляр бота будет единственным запущенным.")
        except (IOError, OSError) as e:
            logger.error(f"Не удалось получить блокировку файла: {str(e)}")
            logger.error("Возможно, другой экземпляр бота уже запущен.")
            # Не выходим из программы, продолжаем работу без блокировки
    
    def _release_file_lock(self):
        """
        Освобождение блокировки файла
        """
        try:
            if self.lock_fd is not None:
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                os.close(self.lock_fd)
                self.lock_fd = None
            
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
                
            logger.info("Блокировка файла освобождена")
        except Exception as e:
            logger.error(f"Ошибка при освобождении блокировки файла: {str(e)}")
    
    def stop(self):
        """
        Остановить планировщик
        """
        logger.info("Получена команда остановки планировщика")
        self.stop_event.set()
        self._release_file_lock()
    
    def _signal_handler(self, signum, frame):
        """
        Обработчик сигналов для корректного завершения работы
        """
        logger.info(f"Получен сигнал {signum}, останавливаем планировщик")
        self.stop()
    
    def run_rnk_script(self):
        """
        Запустить rnk.py для получения актуальных данных
        """
        try:
            logger.info("Запуск файла rnk.py...")
            result = subprocess.run(
                ['python', 'rnk.py'], 
                capture_output=True, 
                text=True, 
                timeout=120,  # Таймаут 2 минуты
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                logger.info("rnk.py выполнен успешно")
                if result.stdout:
                    logger.info(f"Вывод rnk.py: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"rnk.py завершен с ошибкой (код {result.returncode})")
                if result.stderr:
                    logger.error(f"Ошибка rnk.py: {result.stderr.strip()}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("rnk.py превысил время ожидания (120 секунд)")
        except Exception as e:
            logger.error(f"Ошибка при запуске rnk.py: {str(e)}")
    
    def _scheduler_loop(self):
        """
        The main scheduler loop that runs in a background thread.
        - ИСПРАВЛЕНО: Собирает ВСЕ данные включая рейтинг НЕПОСРЕДСТВЕННО в момент отправки в 8:01 UTC
        - Данные рейтинга загружаются через rnk.py прямо перед отправкой для максимальной актуальности
        - Все данные собираются за один раз и отправляются одним сообщением
        """
        # Переменные для отслеживания, когда последний раз обновлялись данные
        self.last_rank_update_date = None
        self.last_rnk_update_date = None
        
        # При запуске не будем загружать данные Google Trends - получим их вместе с общим обновлением
        logger.info("ИСПРАВЛЕНО: Планировщик запущен, ПОЛНЫЙ сбор данных + отправка в 11:01 MSK (без предварительного сбора в 10:59)")
        
        while not self.stop_event.is_set():
            try:
                now = datetime.now()
                
                # Проверяем, пора ли выполнить основное обновление (8:01 UTC = 11:01 MSK)
                if (now.hour == 8 and now.minute == 1 and now.second < 30):
                    logger.info(f"ИСПРАВЛЕНИЕ: Запланирован ПОЛНЫЙ сбор данных + отправка в {now} (UTC 8:01 = MSK 11:01)")
                    logger.info("Получение данных о рейтинге Coinbase (основное обновление в 8:1)")
                    
                    # Выполняем полное обновление данных
                    self.run_scraping_job(force_refresh=True)
                    self.last_run_time = now
                    
                    # Устанавливаем время следующего запуска
                    tomorrow = now + timedelta(days=1)
                    self.next_run_time = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 8, 1, 0)
                    logger.info(f"Данные о рейтинге Coinbase успешно обновлены: {now}")
                    
                    # Спим дольше после выполнения задачи, чтобы не запускать её повторно в ту же минуту
                    logger.info("Scheduler sleeping for 300 seconds (5 minutes)")
                    self.stop_event.wait(300)  # 5 минут
                else:
                    # Вычисляем время до следующего запуска
                    if self.next_run_time is None:
                        # Если это первый запуск, вычисляем время следующего запуска
                        if now.hour < 8 or (now.hour == 8 and now.minute < 1):
                            # Если ещё не было 8:01 сегодня
                            self.next_run_time = datetime(now.year, now.month, now.day, 8, 1, 0)
                        else:
                            # Если 8:01 уже прошло сегодня, запланировать на завтра
                            tomorrow = now + timedelta(days=1)
                            self.next_run_time = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 8, 1, 0)
                    
                    # Короткий сон между проверками
                    self.stop_event.wait(300)  # 5 минут
            
            except Exception as e:
                logger.error(f"Ошибка в основном цикле планировщика: {str(e)}")
                self.stop_event.wait(60)  # Короткий сон при ошибке
        
        logger.info("Планировщик остановлен")
    
    def start(self):
        """
        Запустить планировщик в фоновом потоке
        """
        # Настройка обработчиков сигналов
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Вычисляем время следующего запуска
        now = datetime.now()
        if now.hour < 8 or (now.hour == 8 and now.minute < 1):
            # Если ещё не было 8:01 сегодня
            self.next_run_time = datetime(now.year, now.month, now.day, 8, 1, 0)
        else:
            # Если 8:01 уже прошло сегодня, запланировать на завтра
            tomorrow = now + timedelta(days=1)
            self.next_run_time = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 8, 1, 0)
        
        logger.info(f"Scheduler started. Next run at: {self.next_run_time}")
        
        # Запуск основного цикла в отдельном потоке
        scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        scheduler_thread.start()
        
        return scheduler_thread
    
    def send_combined_message(self, rankings_data, fear_greed_data=None, altseason_data=None, market_breadth_data=None, image_uploader=None):
        """
        Отправить комбинированное сообщение с рейтингом приложения, 
        индексом страха и жадности, Altcoin Season Index и Market Breadth
        """
        try:
            # Проверяем, что есть хотя бы данные рейтинга
            if not rankings_data:
                logger.error("Нет данных рейтинга для отправки сообщения")
                return False
            
            # Начинаем с основного сообщения о рейтинге
            combined_message = self.scraper.format_rankings_message(rankings_data)
            
            # Добавляем Fear & Greed Index, если доступен
            if fear_greed_data:
                fear_greed_message = self.fear_greed_tracker.format_fear_greed_message(fear_greed_data)
                if fear_greed_message:
                    combined_message += "\n\n" + fear_greed_message
            
            # Добавляем Market Breadth с графиком, если доступен
            if market_breadth_data:
                try:
                    # Создаем график Market Breadth
                    from main import create_chart_from_web_endpoint
                    chart_image = create_chart_from_web_endpoint()
                    
                    if chart_image and image_uploader:
                        # Загружаем график на внешний сервис
                        external_url = image_uploader.upload_chart(chart_image)
                        
                        if external_url:
                            # Создаем сообщение с кликабельной ссылкой
                            market_breadth_message = f"Market by 200MA: {market_breadth_data['signal']} [{market_breadth_data['condition']}]({external_url}): {market_breadth_data['current_value']:.1f}%"
                            combined_message += f"\n\n{market_breadth_message}"
                            logger.info(f"Добавлены данные ширины рынка с внешним графиком: {market_breadth_data['signal']} - {market_breadth_data['condition']} ({market_breadth_data['current_value']:.1f}%)")
                        else:
                            # Fallback без ссылки
                            market_breadth_message = f"Market by 200MA: {market_breadth_data['signal']} {market_breadth_data['condition']}: {market_breadth_data['current_value']:.1f}%"
                            combined_message += f"\n\n{market_breadth_message}"
                            logger.info(f"Добавлены данные ширины рынка без графика (не удалось загрузить): {market_breadth_data['signal']} - {market_breadth_data['condition']} ({market_breadth_data['current_value']:.1f}%)")
                    else:
                        # Fallback без ссылки
                        market_breadth_message = f"Market by 200MA: {market_breadth_data['signal']} {market_breadth_data['condition']}: {market_breadth_data['current_value']:.1f}%"
                        combined_message += f"\n\n{market_breadth_message}"
                        logger.info(f"Добавлены данные ширины рынка без графика: {market_breadth_data['signal']} - {market_breadth_data['condition']} ({market_breadth_data['current_value']:.1f}%)")
                        
                except Exception as e:
                    logger.error(f"Ошибка при создании/загрузке графика для Market Breadth: {str(e)}")
                    # Fallback без ссылки
                    market_breadth_message = f"Market by 200MA: {market_breadth_data['signal']} {market_breadth_data['condition']}: {market_breadth_data['current_value']:.1f}%"
                    combined_message += f"\n\n{market_breadth_message}"
                    logger.info(f"Добавлены данные ширины рынка без графика (ошибка): {market_breadth_data['signal']} - {market_breadth_data['condition']} ({market_breadth_data['current_value']:.1f}%)")
            else:
                logger.info("Данные индикатора ширины рынка недоступны")
            
            # Altcoin Season Index удален из сообщений по запросу пользователя
            # Данные по-прежнему собираются для веб-интерфейса, но не отправляются в Telegram
            if altseason_data:
                logger.info(f"Altcoin Season Index data collected but not included in message: {altseason_data['signal']} - {altseason_data['status']}")
            else:
                logger.info("Altcoin Season Index данные недоступны")
            
            # Отправляем основное сообщение (теперь включает встроенную ссылку на график)
            if self.telegram_bot.send_message(combined_message):
                logger.info("Сообщение отправлено в Telegram канал")
                return True
            else:
                logger.error("Ошибка соединения с Telegram. Сообщение не отправлено.")
                return False
                
        except Exception as e:
            error_message = f"❌ Произошла ошибка при отправке сообщения: {str(e)}"
            logger.error(error_message)
            try:
                self.telegram_bot.send_message(error_message)
            except:
                pass
            return False
    
    def run_scraping_job(self, force_refresh=False):
        """
        Выполняет задание по скрапингу: получает данные SensorTower, Fear & Greed Index, 
        Altcoin Season Index и отправляет в Telegram только если рейтинг изменился или это первый запуск
        
        Args:
            force_refresh (bool): Если True, отправить сообщение даже если рейтинг не изменился
        """
        logger.info(f"Выполняется запланированное задание скрапинга в {datetime.now()}")
        
        try:
            # Проверяем соединение с Telegram
            if not self.telegram_bot.test_connection():
                logger.error("Ошибка соединения с Telegram. Задание прервано.")
                return False
            
            # ИСПРАВЛЕНИЕ: Собираем СВЕЖИЕ данные рейтинга НЕПОСРЕДСТВЕННО в момент отправки
            logger.info("ИСПРАВЛЕНИЕ: Собираем СВЕЖИЕ данные рейтинга через rnk.py прямо сейчас")
            
            # Сначала запускаем rnk.py для получения свежих данных
            try:
                logger.info("Запуск rnk.py для получения актуальных данных...")
                self.run_rnk_script()
                logger.info("rnk.py выполнен успешно, данные обновлены")
                
                # Небольшая пауза чтобы данные успели записаться
                import time
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Ошибка при запуске rnk.py: {str(e)}")
            
            # Теперь читаем свежие данные из JSON файла
            from json_rank_reader import get_rank_from_json, get_latest_rank_date
            
            current_rank = get_rank_from_json()
            current_date = get_latest_rank_date()
            
            logger.info(f"ИСПРАВЛЕНИЕ: Получен СВЕЖИЙ рейтинг {current_rank} на дату {current_date}")
            
            # Создаем структуру данных совместимую с остальным кодом
            rankings_data = {
                "app_name": "Coinbase",
                "app_id": "886427730",
                "date": current_date or time.strftime("%Y-%m-%d"),
                "categories": [
                    {"category": "US - iPhone - Top Free", "rank": str(current_rank) if current_rank is not None else "None"}
                ],
                "trend": {"direction": "same", "previous": None}
            }
            
            logger.info(f"ИСПРАВЛЕНИЕ: Текущий рейтинг из JSON: {current_rank} на дату {current_date}")
            
            # Получаем данные индекса страха и жадности
            fear_greed_data = None
            try:
                fear_greed_data = self.fear_greed_tracker.get_fear_greed_index()
                if fear_greed_data:
                    logger.info(f"Успешно получены данные Fear & Greed Index: {fear_greed_data['value']} ({fear_greed_data['classification']})")
                else:
                    logger.warning("Не удалось получить данные Fear & Greed Index")
            except Exception as e:
                logger.error(f"Ошибка при получении данных Fear & Greed Index: {str(e)}")
                
            # Получаем свежие данные Altcoin Season Index
            # Это всегда происходит при отправке сообщения, чтобы данные были актуальными
            altseason_data = None
            try:
                logger.info("Получение данных Altcoin Season Index для комбинированного сообщения")
                altseason_data = self.altcoin_season_index.get_altseason_index()
                if altseason_data:
                    logger.info(f"Успешно получены данные Altcoin Season Index: {altseason_data['signal']} - {altseason_data['status']} (Индекс: {altseason_data['index']})")
                else:
                    logger.warning("Не удалось получить данные Altcoin Season Index")
            except Exception as e:
                logger.error(f"Ошибка при получении данных Altcoin Season Index: {str(e)}")
            
            # Получаем данные о ширине рынка БЕЗ кеша (ИСПРАВЛЕНИЕ для многопоточности)
            market_breadth_data = None
            try:
                logger.info("ИСПРАВЛЕНИЕ: Получение данных индикатора ширины рынка БЕЗ кеша (thread-safe)")
                # Импортируем компоненты напрямую чтобы избежать matplotlib в потоке
                from crypto_analyzer_cryptocompare import CryptoAnalyzer
                import pandas as pd
                
                # Создание анализатора БЕЗ кеша
                analyzer = CryptoAnalyzer(cache=None)
                
                # Получение топ монет
                top_coins = analyzer.get_top_coins(50)
                if not top_coins:
                    logger.warning("ИСПРАВЛЕНИЕ: Не удалось получить список топ монет")
                else:
                    # Загрузка исторических данных БЕЗ кеша
                    historical_data = analyzer.load_historical_data(top_coins, 1400)  # 200 + 1095 + 100
                    
                    if historical_data:
                        # Расчет индикатора
                        indicator_data = analyzer.calculate_market_breadth(historical_data, 200, 1095)
                        
                        if not indicator_data.empty:
                            latest_percentage = indicator_data['percentage'].iloc[-1]
                            
                            # Определяем сигнал и условие
                            if latest_percentage >= 80:
                                signal = "🔴"
                                condition = "Overbought"
                            elif latest_percentage <= 20:
                                signal = "🟢"  
                                condition = "Oversold"
                            else:
                                signal = "🟡"
                                condition = "Neutral"
                            
                            market_breadth_data = {
                                'signal': signal,
                                'condition': condition,
                                'current_value': latest_percentage,
                                'percentage': round(latest_percentage, 1)
                            }
                            
                            logger.info(f"ИСПРАВЛЕНИЕ: Успешно получены СВЕЖИЕ данные ширины рынка: {signal} - {condition} ({latest_percentage:.1f}%)")
                        else:
                            logger.warning("ИСПРАВЛЕНИЕ: Пустые данные индикатора ширины рынка")
                    else:
                        logger.warning("ИСПРАВЛЕНИЕ: Не удалось загрузить исторические данные")
                        
            except Exception as e:
                logger.error(f"ИСПРАВЛЕНИЕ: Ошибка при получении данных ширины рынка БЕЗ кеша: {str(e)}")
            
            # Подробная проверка на изменение рейтинга
            if self.last_sent_rank is None:
                logger.info(f"Первый запуск, предыдущее значение отсутствует. Текущий рейтинг: {current_rank}")
                need_to_send = True
                # Для тестирования добавляем искусственный тренд, если есть числовое значение
                if current_rank is not None:
                    rankings_data["trend"] = {"direction": "up", "previous": current_rank + 5}
                    logger.info(f"Добавлен искусственный тренд для тестирования отображения индикаторов: {current_rank + 5} → {current_rank}")
                else:
                    rankings_data["trend"] = {"direction": "same", "previous": None}
            elif current_rank != self.last_sent_rank:
                logger.info(f"Обнаружено изменение рейтинга: {current_rank} (предыдущий: {self.last_sent_rank})")
                # Добавляем префикс для понимания, улучшение или ухудшение (только для числовых значений)
                if current_rank is not None and self.last_sent_rank is not None:
                    if current_rank < self.last_sent_rank:
                        logger.info(f"Улучшение рейтинга: {self.last_sent_rank} → {current_rank}")
                        rankings_data["trend"] = {"direction": "up", "previous": self.last_sent_rank}
                    else:
                        logger.info(f"Ухудшение рейтинга: {self.last_sent_rank} → {current_rank}")
                        rankings_data["trend"] = {"direction": "down", "previous": self.last_sent_rank}
                else:
                    # Если один из рейтингов None, просто показываем изменение
                    rankings_data["trend"] = {"direction": "same", "previous": self.last_sent_rank}
                need_to_send = True
            else:
                logger.info(f"Рейтинг не изменился ({current_rank} = {self.last_sent_rank}). Сообщение не отправлено.")
                need_to_send = False
            
            # Отправляем сообщение только если нужно
            if need_to_send:
                # Отправляем сообщение только если рейтинг изменился или это первый запуск
                success = force_refresh or need_to_send
                
                if success:
                    # Используем image_uploader для загрузки графиков
                    from image_uploader import image_uploader
                    
                    # Отправляем комбинированное сообщение
                    if self.send_combined_message(rankings_data, fear_greed_data, altseason_data, market_breadth_data, image_uploader):
                        # Обновляем последний отправленный рейтинг
                        previous_rank = self.last_sent_rank
                        self.last_sent_rank = current_rank
                        logger.info(f"Обновлен последний отправленный рейтинг: {previous_rank} → {self.last_sent_rank}")
                        
                        # Сохраняем рейтинг в файл для восстановления при перезапуске
                        # Делаем это синхронно с обновлением переменной, чтобы избежать рассинхронизации
                        try:
                            with open(self.rank_history_file, "w") as f:
                                f.write(str(current_rank))
                            logger.info(f"Рейтинг {current_rank} сохранен в файл {self.rank_history_file}")
                            
                            # Проверка записи в файл
                            if os.path.exists(self.rank_history_file):
                                with open(self.rank_history_file, "r") as check_file:
                                    saved_value = check_file.read().strip()
                                    if saved_value != str(current_rank):
                                        logger.error(f"Ошибка записи: в файле {saved_value}, должно быть {current_rank}")
                                        
                            # Дополнительно, сохраняем в JSON-историю через HistoryAPI
                            try:
                                # Импортируем API истории
                                from history_api import HistoryAPI
                                
                                # Создаем экземпляр API истории
                                history_api = HistoryAPI()
                                
                                # Сохраняем данные рейтинга
                                if current_rank is not None and previous_rank is not None:
                                    change_value = current_rank - previous_rank
                                    if change_value > 0:
                                        change_direction = "down"
                                        change_text = f"down {change_value}"
                                    elif change_value < 0:
                                        change_direction = "up" 
                                        change_text = f"up {abs(change_value)}"
                                    else:
                                        change_direction = "same"
                                        change_text = "same"
                                else:
                                    change_direction = "same"
                                    change_text = "same"
                                
                                history_api.save_rank_history(current_rank, change_text)
                                logger.info(f"Saved new rank history entry: {current_rank} (change: {change_text})")
                                
                                # Сохраняем данные Fear & Greed Index
                                if fear_greed_data:
                                    history_api.save_fear_greed_history(fear_greed_data['value'], fear_greed_data['classification'])
                                    logger.info(f"Saved new Fear & Greed Index history entry: {fear_greed_data['value']} ({fear_greed_data['classification']})")
                                
                                # Сохраняем данные Altcoin Season Index
                                if altseason_data:
                                    history_api.save_altseason_history(altseason_data['index'], altseason_data['signal'], altseason_data['status'])
                                    logger.info(f"Saved new Altcoin Season Index history entry: {altseason_data['signal']} - {altseason_data['status']} ({altseason_data['index']})")
                                    logger.info(f"Сохранены данные Altcoin Season Index в историю: {altseason_data['signal']} - {altseason_data['status']}")
                                
                                logger.info("История данных успешно сохранена в JSON-файлы")
                                
                            except ImportError:
                                logger.warning("HistoryAPI не найдено, данные сохранены только в текстовый файл")
                            except Exception as e:
                                logger.error(f"Ошибка при сохранении в JSON-историю: {str(e)}")
                                
                        except Exception as e:
                            logger.error(f"Ошибка при сохранении рейтинга в файл: {str(e)}")
                        
                        self.last_run_status = "success"
                        return True
                    else:
                        logger.error("Не удалось отправить сообщение в Telegram")
                        self.last_run_status = "failed"
                        return False
                else:
                    logger.info("Сообщение не отправлено (рейтинг не изменился)")
                    self.last_run_status = "skipped"
                    return True
            elif force_refresh:
                # Принудительная отправка даже если рейтинг не изменился
                logger.info("Принудительная отправка сообщения (force_refresh=True)")
                
                # Используем image_uploader для загрузки графиков
                from image_uploader import image_uploader
                
                if self.send_combined_message(rankings_data, fear_greed_data, altseason_data, market_breadth_data, image_uploader):
                    # Не обновляем last_sent_rank при принудительной отправке
                    logger.info("Принудительное сообщение отправлено успешно")
                    self.last_run_status = "success"
                    return True
                else:
                    logger.error("Не удалось отправить принудительное сообщение в Telegram")
                    self.last_run_status = "failed"
                    return False
            else:
                logger.info("Сообщение не отправлено (рейтинг не изменился и force_refresh=False)")
                self.last_run_status = "skipped"
                return True
                
        except Exception as e:
            error_message = f"❌ Произошла ошибка при выполнении задания скрапинга: {str(e)}"
            logger.error(error_message)
            try:
                self.telegram_bot.send_message(error_message)
            except:
                pass
            self.last_run_status = "error"
            return False
    
    def get_current_fear_greed_index(self):
        """
        Get current Fear & Greed Index data for testing/manual triggering
        
        Returns:
            dict: Fear & Greed Index data or None in case of error
        """
        try:
            return self.fear_greed_tracker.get_fear_greed_index()
        except Exception as e:
            logger.error(f"Error getting Fear & Greed Index: {str(e)}")
            return None
    
    def get_current_altseason_index(self):
        """
        Get current Altcoin Season Index data for testing/manual triggering
        
        Returns:
            dict: Altcoin Season Index data or None in case of error
        """
        try:
            return self.altcoin_season_index.get_altseason_index()
        except Exception as e:
            logger.error(f"Error getting Altcoin Season Index: {str(e)}")
            return None
            
    def run_now(self, force_send=False):
        """
        Manually trigger a scraping job immediately
        
        Args:
            force_send (bool): If True, send message even if rank hasn't changed
            
        Returns:
            bool: True if job ran successfully, False otherwise
        """
        logger.info("Manual scraping job triggered")
        
        # Выполняем операцию без использования файла блокировки
        # Примечание: Механизм файловой блокировки отключен, так как он вызывал проблемы
        # с плановым запуском задач и создавал permanent файл блокировки
        
        if force_send:
            # Temporarily save the old value
            old_last_sent_rank = self.last_sent_rank
            # Reset to force sending
            self.last_sent_rank = None
            
            result = self.run_scraping_job(force_refresh=True)
            
            # If job failed, restore the old value
            if not result:
                self.last_sent_rank = old_last_sent_rank
                # Также восстановим значение в файле истории
                try:
                    with open(self.rank_history_file, "w") as f:
                        f.write(str(old_last_sent_rank))
                    logger.info(f"Восстановлен рейтинг в файле: {old_last_sent_rank}")
                except Exception as e:
                    logger.error(f"Ошибка при восстановлении рейтинга в файле: {str(e)}")
        else:
            result = self.run_scraping_job(force_refresh=False)
            
        return result