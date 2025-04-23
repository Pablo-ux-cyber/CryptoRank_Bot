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