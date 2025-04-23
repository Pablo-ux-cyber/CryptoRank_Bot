import os
import threading
import time
from datetime import datetime, timedelta

from logger import logger
from scraper import SensorTowerScraper
from telegram_bot import TelegramBot
from fear_greed_index import FearGreedIndexTracker
from google_trends_pulse import GoogleTrendsPulse

class SensorTowerScheduler:
    def __init__(self):
        # Instead of using APScheduler, create a simple threading-based scheduler
        self.running = False
        self.thread = None
        self.stop_event = threading.Event()
        self.scraper = SensorTowerScraper()
        self.telegram_bot = TelegramBot()
        self.fear_greed_tracker = FearGreedIndexTracker()
        self.google_trends_pulse = GoogleTrendsPulse()
        
        # Определяем пути для хранения данных непосредственно в директории бота вместо /tmp
        # Используем корневую директорию бота для файлов истории
        self.data_dir = os.path.dirname(os.path.abspath(__file__))
        self.rank_history_file = os.path.join(self.data_dir, "rank_history.txt")
        logger.info(f"Файл истории рейтинга будет храниться по пути: {self.rank_history_file}")
        
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
        - Проверяет рейтинг приложения и Fear & Greed Index каждые 5 минут
        - Проверяет Google Trends только раз в день, примерно в 10:00
        """
        # Переменная для отслеживания, когда последний раз обновлялись данные Google Trends
        self.last_trends_update_date = None
        
        # При старте получаем свежие данные Google Trends
        try:
            logger.info("Получение свежих данных Google Trends при запуске планировщика")
            self.google_trends_pulse.refresh_trends_data()
            self.last_trends_update_date = datetime.now().date()
            logger.info(f"Данные Google Trends успешно обновлены: {datetime.now()}")
        except Exception as e:
            logger.error(f"Ошибка при получении данных Google Trends при запуске: {str(e)}")
        
        while not self.stop_event.is_set():
            try:
                # Проверяем, не нужно ли обновить данные Google Trends
                # (только один раз в день, примерно в 10:00)
                now = datetime.now()
                today = now.date()
                update_trends = False
                
                # Если сейчас примерно 10 часов (9:45 - 10:15) и мы ещё не обновляли данные сегодня
                if (now.hour == 9 and now.minute >= 45) or (now.hour == 10 and now.minute <= 15):
                    if self.last_trends_update_date is None or self.last_trends_update_date < today:
                        update_trends = True
                        logger.info(f"Запланировано обновление данных Google Trends в {now}")
                
                # Обновляем данные Google Trends, если нужно
                if update_trends:
                    try:
                        logger.info("Получение свежих данных Google Trends (ежедневное обновление)")
                        self.google_trends_pulse.refresh_trends_data()
                        self.last_trends_update_date = today
                        logger.info(f"Данные Google Trends успешно обновлены: {now}")
                    except Exception as e:
                        logger.error(f"Ошибка при получении данных Google Trends: {str(e)}")
                
                # Проверяем, не выполняется ли ручная операция скрапинга
                manual_lock_file = os.path.join(self.data_dir, "manual_operation.lock")
                
                if os.path.exists(manual_lock_file):
                    try:
                        import fcntl
                        with open(manual_lock_file, "r") as manual_lock:
                            try:
                                # Пытаемся получить блокировку без ожидания
                                fcntl.lockf(manual_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                                # Если получили блокировку, значит никто ее не держит
                                fcntl.lockf(manual_lock, fcntl.LOCK_UN)
                                # Запускаем задание (используем кешированные данные Google Trends)
                                self.run_scraping_job()
                            except IOError:
                                # Блокировка занята - пропускаем текущий запуск
                                logger.info("Пропуск планового запуска из-за выполнения ручной операции")
                    except Exception as e:
                        logger.error(f"Ошибка при проверке блокировки ручной операции: {str(e)}")
                        # В случае ошибки работы с блокировкой все равно выполняем задание
                        self.run_scraping_job()
                else:
                    # Файла блокировки нет, запускаем задание как обычно
                    self.run_scraping_job()
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
            
            # Перемещаем файл блокировки также в директорию данных
            lockfile_path = os.path.join(self.data_dir, "coinbasebot.lock")
            logger.info(f"Файл блокировки будет храниться по пути: {lockfile_path}")
            
            # Если файл блокировки существует, но стар (> 30 минут), удаляем его
            if os.path.exists(lockfile_path):
                try:
                    file_time = os.path.getmtime(lockfile_path)
                    current_time = time.time()
                    # Если файл старше 30 минут
                    if current_time - file_time > 30 * 60:
                        os.remove(lockfile_path)
                        logger.info(f"Удален устаревший файл блокировки (возраст: {(current_time - file_time)/60:.1f} минут)")
                except Exception as e:
                    logger.warning(f"Ошибка при проверке старого файла блокировки: {str(e)}")
            
            try:
                self.lockfile = open(lockfile_path, "w")
                fcntl.lockf(self.lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
                logger.info("Получена блокировка файла. Этот экземпляр бота будет единственным запущенным.")
            except IOError:
                logger.error("Другой экземпляр бота уже запущен. Завершение работы.")
                self.lockfile = None
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
            if hasattr(self, 'lockfile') and self.lockfile is not None:
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
        Отправляет комбинированное сообщение с данными о рейтинге, индексе страха и жадности,
        и сигналом от Google Trends Pulse в упрощенном формате
        
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
                
            # Используем метод scraper для форматирования сообщения о рейтинге
            formatted_rankings = self.scraper.format_rankings_message(rankings_data)
            combined_message = formatted_rankings
            
            # Затем добавляем данные индекса страха и жадности, если доступны
            if fear_greed_data:
                # Используем метод fear_greed_tracker для форматирования сообщения
                fear_greed_message = self.fear_greed_tracker.format_fear_greed_message(fear_greed_data)
                combined_message += f"\n\n{fear_greed_message}"
            
            # Добавляем данные от Google Trends Pulse
            try:
                # Получаем данные трендов
                trends_data = self.google_trends_pulse.get_trends_data()
                if trends_data:
                    # Форматируем сообщение о трендах используя обновленный метод
                    trends_message = self.google_trends_pulse.format_trends_message(trends_data)
                    
                    # Проверяем, что сообщение не None (в случае отсутствия реальных данных)
                    if trends_message is not None:
                        combined_message += f"\n\n{trends_message}"
                        logger.info(f"Added Google Trends Pulse data: {trends_data.get('signal', 'None')} - {trends_data.get('description', 'N/A')}")
                    else:
                        logger.info("Google Trends данные недоступны - не включаем в сообщение")
            except Exception as e:
                logger.error(f"Ошибка при получении данных Google Trends Pulse: {str(e)}")
                # Продолжаем без данных трендов
            
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
    
    def run_scraping_job(self, check_google_trends=True):
        """
        Выполняет задание по скрапингу: получает данные SensorTower и отправляет в Telegram
        только если рейтинг изменился или это первый запуск
        
        Args:
            check_google_trends (bool): Проверять ли данные Google Trends или использовать кеш
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
                # Отправляем сообщение об ошибке, но только если это не связано с ошибкой получения данных
                if "Failed to scrape SensorTower data" not in error_message:
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
                
                # Обновляем последний отправленный рейтинг независимо от результата отправки
                # Это поможет избежать множественных сообщений при сбоях отправки
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
                        
                        # Создаем экземпляр API и сохраняем данные
                        history_api = HistoryAPI(self.data_dir)
                        
                        # Сохраняем рейтинг в историю с предыдущим значением для подсчета изменения
                        history_api.save_rank_history(
                            rank=current_rank, 
                            previous_rank=previous_rank
                        )
                        
                        # Если доступны данные индекса страха и жадности, сохраняем и их
                        if fear_greed_data and 'value' in fear_greed_data and 'classification' in fear_greed_data:
                            history_api.save_fear_greed_history(
                                value=int(fear_greed_data['value']), 
                                classification=fear_greed_data['classification']
                            )
                            
                        # Если доступны данные Google Trends, сохраняем и их
                        trends_data = self.google_trends_pulse.get_trends_data()
                        # Проверяем, что данные содержат реальный сигнал (не None)
                        if (trends_data and 
                            'signal' in trends_data and 
                            'description' in trends_data and 
                            trends_data['signal'] is not None):
                            history_api.save_google_trends_history(
                                signal=trends_data['signal'],
                                description=trends_data['description'],
                                fomo_score=trends_data.get('fomo_score'),
                                fear_score=trends_data.get('fear_score'),
                                general_score=trends_data.get('general_score'),
                                fomo_to_fear_ratio=trends_data.get('fomo_to_fear_ratio')
                            )
                            
                        logger.info(f"История данных успешно сохранена в JSON-файлы")
                    except ImportError:
                        # API истории недоступен, пропускаем сохранение в историю
                        logger.debug("API истории недоступен. История рейтинга сохранена только в файл.")
                    except Exception as history_error:
                        logger.error(f"Ошибка при сохранении истории в JSON-файлы: {str(history_error)}")
                        
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
            
    def run_now(self, force_send=False):
        """
        Manually trigger a scraping job immediately
        
        Args:
            force_send (bool): If True, send message even if rank hasn't changed
            
        Returns:
            bool: True if job ran successfully, False otherwise
        """
        logger.info("Manual scraping job triggered")
        
        # Добавляем дополнительную блокировку для предотвращения гонки состояний
        # при одновременном запуске из веб-интерфейса и планировщика
        manual_lock_file = os.path.join(self.data_dir, "manual_operation.lock")
        
        try:
            import fcntl
            with open(manual_lock_file, "w") as manual_lock:
                try:
                    # Пытаемся получить блокировку без ожидания
                    fcntl.lockf(manual_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    
                    # Блокировка получена, выполняем операцию
                    if force_send:
                        # Temporarily save the old value
                        old_last_sent_rank = self.last_sent_rank
                        # Reset to force sending
                        self.last_sent_rank = None
                        
                        result = self.run_scraping_job()
                        
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
                        result = self.run_scraping_job()
                    
                    # Освобождаем блокировку
                    fcntl.lockf(manual_lock, fcntl.LOCK_UN)
                    return result
                    
                except IOError:
                    # Не удалось получить блокировку - другой процесс уже выполняет операцию
                    logger.warning("Другой процесс уже выполняет операцию скрапинга. Задание пропущено.")
                    return False
                    
        except Exception as e:
            logger.error(f"Ошибка при работе с блокировкой ручной операции: {str(e)}")
            # Продолжаем выполнение без блокировки в случае ошибки
            if force_send:
                old_last_sent_rank = self.last_sent_rank
                self.last_sent_rank = None
                result = self.run_scraping_job()
                if not result:
                    self.last_sent_rank = old_last_sent_rank
                return result
            else:
                return self.run_scraping_job()
