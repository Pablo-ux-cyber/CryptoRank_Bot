#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Простой тест Google Trends API
"""

import time
from datetime import datetime
from pytrends.request import TrendReq

print(f"Тест Google Trends API - {datetime.now()}")

# Создаём клиент с русским языком
print("Создание клиента с настройками 'ru-RU', tz=180...")
pytrends = TrendReq(hl='ru-RU', tz=180)

print("Формирование запроса для 'bitcoin'...")
# Формируем запрос с временным диапазоном в 12 месяцев
pytrends.build_payload(['bitcoin'], cat=0, timeframe='today 12-m')

print("Получение данных interest_over_time()...")
# Получаем индекс популярности
data = pytrends.interest_over_time()

print(f"Получено {len(data)} записей")
print("Первые 5 записей:")
print(data.head(5))

print("\nПроверка другого ключевого слова...")
time.sleep(3)  # Пауза между запросами

print("Формирование запроса для 'crypto crash'...")
pytrends.build_payload(['crypto crash'], cat=0, timeframe='today 12-m')

print("Получение данных interest_over_time()...")
fear_data = pytrends.interest_over_time()

print(f"Получено {len(fear_data)} записей для 'crypto crash'")
print("Первые 5 записей:")
print(fear_data.head(5))

# Рассчитаем средние значения
bitcoin_mean = data['bitcoin'].mean()
crash_mean = fear_data['crypto crash'].mean() if not fear_data.empty else 0

print(f"\nСреднее значение интереса:")
print(f"Bitcoin: {bitcoin_mean:.2f}")
print(f"Crypto crash: {crash_mean:.2f}")
print(f"Соотношение FOMO/Fear: {bitcoin_mean/max(crash_mean, 1):.2f}")

print("\nТест успешно завершен!")