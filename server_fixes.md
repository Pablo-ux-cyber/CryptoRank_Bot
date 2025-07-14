# Исправления для сервера

## Проблемы найденные в логах:
1. `signal only works in main thread of the main interpreter` - Market Breadth в потоке
2. `RuntimeError: '<asyncio.locks.Event object> is bound to a different event loop'` - Telegram asyncio

## Исправление 1: scheduler.py (строки 409-458)

Заменить блок "Получаем данные о ширине рынка БЕЗ кеша" на:

```python
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
```

## Исправление 2: telegram_bot.py функция _get_event_loop (строки 66-85)

Заменить функцию _get_event_loop на:

```python
    def _get_event_loop(self):
        """
        Получить существующий event loop или создать новый для многопоточности
        
        Returns:
            asyncio.AbstractEventLoop: Активный event loop
        """
        try:
            # Сначала пытаемся получить текущий loop
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Loop is closed")
            return loop
        except RuntimeError:
            # Если в потоке нет loop или он закрыт, создаем новый
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return loop
            except Exception as e:
                logger.error(f"Ошибка создания event loop: {str(e)}")
                return None
```

## Применение исправлений на сервере:

1. Остановить бота: `sudo systemctl stop coinbasebot`
2. Сделать backup: `cp scheduler.py scheduler.py.backup && cp telegram_bot.py telegram_bot.py.backup`
3. Применить исправления в файлах
4. Запустить бота: `sudo systemctl start coinbasebot`
5. Проверить логи: `tail -f sensortower_bot.log`

После исправлений ошибки должны исчезнуть и сообщения будут отправляться успешно.