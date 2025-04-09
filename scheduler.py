import os
import threading
import time
from datetime import datetime, timedelta

from logger import logger
from scraper import SensorTowerScraper
from telegram_bot import TelegramBot
from fear_greed_index import FearGreedIndexTracker
from google_trends import GoogleTrendsTracker

class SensorTowerScheduler:
    def __init__(self):
        # Instead of using APScheduler, create a simple threading-based scheduler
        self.running = False
        self.thread = None
        self.stop_event = threading.Event()
        self.scraper = SensorTowerScraper()
        self.telegram_bot = TelegramBot()
        self.fear_greed_tracker = FearGreedIndexTracker()
        self.google_trends_tracker = GoogleTrendsTracker()
        self.rank_history_file = "/tmp/coinbasebot_rank_history.txt"
        self.last_google_trends_check = None  # Для отслеживания последней проверки Google Trends
        
        # Пытаемся загрузить последний отправленный рейтинг из файла
        try:
            if os.path.exists(self.rank_history_file):
                with open(self.rank_history_file, "r") as f:
                    saved_rank = f.read().strip()
                    if saved_rank and saved_rank.isdigit():
                        self.last_sent_rank = int(saved_rank)
                        logger.info(f"Загружен предыдущий рейтинг из файла: {self.last_sent_rank}")
                    else:
                        self.last_sent_rank = None
            else:
                self.last_sent_rank = None
        except Exception as e:
            logger.error(f"Ошибка при чтении файла истории рейтинга: {str(e)}")
            self.last_sent_rank = None
            
        self.lockfile = None  # Для блокировки файла (предотвращения запуска нескольких экземпляров)
    
    def _scheduler_loop(self):
        """
        The main scheduler loop that runs in a background thread.
        Sleeps for 5 minutes between executions.
        """
        google_trends_interval = 24 * 60 * 60  # Отправка Google Trends каждые 24 часа
        
        while not self.stop_event.is_set():
            try:
                # Run the job
                self.run_scraping_job()
                
                # Проверяем, нужно ли отправлять данные Google Trends
                current_time = datetime.now()
                if self.last_google_trends_check is None or (current_time - self.last_google_trends_check).total_seconds() >= google_trends_interval:
                    logger.info("Отправка данных Google Trends (запланированная)")
                    self.send_google_trends_message()
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
            
            # Sleep for 5 minutes
            seconds_to_sleep = 5 * 60  # 5 minutes in seconds
            logger.info(f"Scheduler sleeping for {seconds_to_sleep} seconds (5 minutes)")
            
            # Wait with checking for stop event
            for _ in range(seconds_to_sleep):
                if self.stop_event.is_set():
                    break
                time.sleep(1)
    
    def start(self):
        """Start the scheduler"""
        try:
            # Проверка на наличие уже запущенного экземпляра
            import fcntl
            import os
            
            self.lockfile = open("/tmp/coinbasebot.lock", "w")
            try:
                fcntl.lockf(self.lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
                logger.info("Получена блокировка файла. Этот экземпляр бота будет единственным запущенным.")
            except IOError:
                logger.error("Другой экземпляр бота уже запущен. Завершение работы.")
                return False
                
            if self.running:
                logger.warning("Scheduler is already running")
                return True
                
            self.running = True
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._scheduler_loop)
            self.thread.daemon = True
            self.thread.start()
            
            next_run = datetime.now() + timedelta(minutes=5)
            logger.info(f"Scheduler started. Next run at: {next_run}")
            
            # Uncomment to run immediately for testing
            # self.run_scraping_job()
            
            return True
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
            return False
    
    def stop(self):
        """Stop the scheduler"""
        if self.running:
            self.running = False
            self.stop_event.set()
            if self.thread:
                self.thread.join(timeout=1)
            # Освобождаем блокировку файла при остановке
            if hasattr(self, 'lockfile'):
                import fcntl
                try:
                    fcntl.lockf(self.lockfile, fcntl.LOCK_UN)
                    self.lockfile.close()
                    logger.info("Блокировка файла освобождена")
                except Exception as e:
                    logger.error(f"Ошибка при освобождении блокировки файла: {str(e)}")
            logger.info("Scheduler stopped")
    
    def _send_combined_message(self, rankings_data, fear_greed_data=None):
        """
        Отправляет комбинированное сообщение с данными о рейтинге и индексе страха и жадности
        
        Args:
            rankings_data (dict): Данные о рейтинге приложения
            fear_greed_data (dict, optional): Данные индекса страха и жадности
            
        Returns:
            bool: True если сообщение успешно отправлено, False в противном случае
        """
        try:
            # Убедимся, что телеграм-бот правильно инициализирован
            if not self.telegram_bot.test_connection():
                logger.error("Ошибка соединения с Telegram. Сообщение не отправлено.")
                return False
                
            # Извлекаем рейтинг из данных
            if not rankings_data or "categories" not in rankings_data or not rankings_data["categories"]:
                logger.error("Неверный формат данных о рейтинге")
                return False
                
            rank = rankings_data["categories"][0]["rank"]
            
            # Создаем сообщение
            trend_icon = ""
            
            # Добавляем индикатор тренда, если доступна информация о тренде
            if "trend" in rankings_data:
                trend_direction = rankings_data["trend"]["direction"]
                if trend_direction == "up":
                    # Лучший рейтинг = меньшее число, зеленая стрелка вверх
                    trend_icon = "🔼 "
                elif trend_direction == "down":
                    # Худший рейтинг = большее число, красная стрелка вниз
                    trend_icon = "🔽 "
            
            combined_message = f"{trend_icon}Coinbase Appstore Rank: {rank}\n\n"
            
            # Затем добавляем данные индекса страха и жадности, если доступны
            if fear_greed_data:
                value = fear_greed_data.get("value", "N/A")
                label = fear_greed_data.get("classification", "Unknown")
                
                # Выбираем эмодзи в зависимости от классификации
                filled_char = "⚪" # По умолчанию
                if label == "Extreme Fear":
                    emoji = "😱"
                    filled_char = "🔴"
                elif label == "Fear":
                    emoji = "😨"
                    filled_char = "🟠"
                elif label == "Neutral":
                    emoji = "😐"
                    filled_char = "🟡"
                elif label == "Greed":
                    emoji = "😏"
                    filled_char = "🟢"
                elif label == "Extreme Greed":
                    emoji = "🤑"
                    filled_char = "🟢"
                else:
                    emoji = "❓"
                
                # Добавляем данные индекса страха и жадности
                combined_message += f"{emoji} {label}: {value}/100\n"
                
                # Добавляем прогресс-бар
                progress_bar = self.fear_greed_tracker._generate_progress_bar(int(value), 100, 10, filled_char)
                combined_message += f"{progress_bar}"
            
            # Отправляем комбинированное сообщение
            if not self.telegram_bot.send_message(combined_message):
                logger.error("Не удалось отправить комбинированное сообщение в Telegram.")
                return False
            
            logger.info("Комбинированное сообщение успешно отправлено")
            return True
            
        except Exception as e:
            error_message = f"❌ Произошла ошибка при отправке сообщения: {str(e)}"
            logger.error(error_message)
            try:
                self.telegram_bot.send_message(error_message)
            except:
                pass
            return False
    
    def run_scraping_job(self):
        """
        Выполняет задание по скрапингу: получает данные SensorTower и отправляет в Telegram
        только если рейтинг изменился или это первый запуск
        """
        logger.info(f"Выполняется запланированное задание скрапинга в {datetime.now()}")
        
        try:
            # Проверяем соединение с Telegram
            if not self.telegram_bot.test_connection():
                logger.error("Ошибка соединения с Telegram. Задание прервано.")
                return False
            
            # Получаем данные о рейтинге
            rankings_data = self.scraper.scrape_category_rankings()
            
            if not rankings_data:
                error_message = "❌ Failed to scrape SensorTower data."
                logger.error(error_message)
                self.telegram_bot.send_message(error_message)
                return False
            
            # Проверяем наличие данных о категориях и рейтинге
            if not rankings_data.get("categories") or not rankings_data["categories"]:
                logger.error("Не найдены данные о категориях в полученных данных")
                return False
                
            # Получаем текущий рейтинг
            current_rank = int(rankings_data["categories"][0]["rank"])
            
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
            
            # Подробная проверка на изменение рейтинга
            if self.last_sent_rank is None:
                logger.info(f"Первый запуск, предыдущее значение отсутствует. Текущий рейтинг: {current_rank}")
                need_to_send = True
                # Нет предыдущего значения, тренд не указываем
            elif current_rank != self.last_sent_rank:
                logger.info(f"Обнаружено изменение рейтинга: {current_rank} (предыдущий: {self.last_sent_rank})")
                # Добавляем префикс для понимания, улучшение или ухудшение
                if current_rank < self.last_sent_rank:
                    logger.info(f"Улучшение рейтинга: {self.last_sent_rank} → {current_rank}")
                    # Добавляем информацию о тренде в данные для отображения стрелки вверх
                    rankings_data["trend"] = {"direction": "up", "previous": self.last_sent_rank}
                else:
                    logger.info(f"Ухудшение рейтинга: {self.last_sent_rank} → {current_rank}")
                    # Добавляем информацию о тренде в данные для отображения стрелки вниз
                    rankings_data["trend"] = {"direction": "down", "previous": self.last_sent_rank}
                need_to_send = True
            else:
                logger.info(f"Рейтинг не изменился ({current_rank} = {self.last_sent_rank}). Сообщение не отправлено.")
                need_to_send = False
            
            # Отправляем сообщение только если нужно
            if need_to_send:
                # Отправляем сообщение только если рейтинг изменился или это первый запуск
                result = self._send_combined_message(rankings_data, fear_greed_data)
                
                if result:
                    # Обновляем последний отправленный рейтинг
                    previous_rank = self.last_sent_rank
                    self.last_sent_rank = current_rank
                    logger.info(f"Успешно обновлен последний отправленный рейтинг: {previous_rank} → {self.last_sent_rank}")
                    
                    # Сохраняем рейтинг в файл для восстановления при перезапуске
                    try:
                        with open(self.rank_history_file, "w") as f:
                            f.write(str(current_rank))
                        logger.info(f"Рейтинг {current_rank} сохранен в файл {self.rank_history_file}")
                    except Exception as e:
                        logger.error(f"Ошибка при сохранении рейтинга в файл: {str(e)}")
                return result
            else:
                return True  # Работа выполнена успешно, сообщение не требовалось отправлять
                
        except Exception as e:
            error_message = f"❌ Произошла ошибка во время задания скрапинга: {str(e)}"
            logger.error(error_message)
            try:
                self.telegram_bot.send_message(error_message)
            except:
                pass
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
    
    def get_google_trends_data(self, terms=None, timeframe=None, geo=None):
        """
        Получает данные Google Trends для указанных терминов
        
        Args:
            terms (list, optional): Список терминов для отслеживания
            timeframe (str, optional): Период времени в формате Google Trends
            geo (str, optional): Код страны или '' для всего мира
            
        Returns:
            dict: Данные трендов или None в случае ошибки
        """
        try:
            return self.google_trends_tracker.get_interest_over_time(terms, timeframe, geo)
        except Exception as e:
            logger.error(f"Ошибка при получении данных Google Trends: {str(e)}")
            return None
        
    def send_google_trends_message(self):
        """
        Отправляет сообщение с данными Google Trends в Telegram
        
        Returns:
            bool: True если сообщение успешно отправлено, False в противном случае
        """
        try:
            # Убедимся, что телеграм-бот правильно инициализирован
            if not self.telegram_bot.test_connection():
                logger.error("Ошибка соединения с Telegram. Сообщение Google Trends не отправлено.")
                return False
            
            # Получаем данные трендов
            trends_data = self.get_google_trends_data()
            
            if not trends_data:
                logger.error("Не удалось получить данные Google Trends.")
                return False
            
            # Форматируем сообщение
            message = self.google_trends_tracker.format_trends_message(trends_data)
            
            # Отправляем сообщение
            if not self.telegram_bot.send_message(message):
                logger.error("Не удалось отправить сообщение Google Trends в Telegram.")
                return False
            
            logger.info("Сообщение Google Trends успешно отправлено")
            self.last_google_trends_check = datetime.now()
            return True
            
        except Exception as e:
            error_message = f"❌ Произошла ошибка при отправке сообщения Google Trends: {str(e)}"
            logger.error(error_message)
            try:
                self.telegram_bot.send_message(error_message)
            except:
                pass
            return False
            
    def run_now(self, force_send=False):
        """
        Manually trigger a scraping job immediately
        
        Args:
            force_send (bool): If True, send message even if rank hasn't changed
            
        Returns:
            bool: True if job ran successfully, False otherwise
        """
        logger.info("Manual scraping job triggered")
        
        if force_send:
            # Temporarily save the old value
            old_last_sent_rank = self.last_sent_rank
            # Reset to force sending
            self.last_sent_rank = None
            
            result = self.run_scraping_job()
            
            # If job failed, restore the old value
            if not result:
                self.last_sent_rank = old_last_sent_rank
                
            return result
        else:
            # Regular run with change detection
            return self.run_scraping_job()
