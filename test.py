#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from datetime import datetime, timedelta

from pytrends.request import TrendReq
from pytrends.exceptions import TooManyRequestsError

def safe_interest_over_time(pytrends, retries=5, initial_delay=10):
    """
    Пытается получить данные, при TooManyRequestsError —
    ждёт и повторяет с удвоением задержки.
    """
    delay = initial_delay
    for attempt in range(1, retries + 1):
        try:
            return pytrends.interest_over_time()
        except TooManyRequestsError:
            if attempt == retries:
                # После последней неудачи — пробрасываем ошибку
                raise
            print(f"429 Too Many Requests (attempt {attempt}/{retries}), sleeping {delay}s…")
            time.sleep(delay)
            delay *= 2

def main():
    KEYWORD = 'bitcoin'

    # Создаём клиента: англ. локаль, UTC
    pytrends = TrendReq(hl='en-US', tz=0
                        # , proxies=['https://user:pass@proxy:port']  # при необходимости
                       )

    # Диапазон за последние 30 дней
    today = datetime.utcnow().date()
    start = today - timedelta(days=30)
    timeframe = f"{start} {today}"  # "YYYY-MM-DD YYYY-MM-DD"

    # Формируем запрос
    pytrends.build_payload([KEYWORD], cat=0, timeframe=timeframe)

    # Надёжно тянем данные с бэкоффом
    data = safe_interest_over_time(pytrends, retries=4, initial_delay=10)

    # Отфильтровываем строку за текущий (неполный) день
    if 'isPartial' in data.columns:
        data = data[~data['isPartial']]

    print(data)

if __name__ == "__main__":
    main()
