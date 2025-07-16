#!/usr/bin/env python3
"""
Проверка влияния времени на результаты
"""

import logging
import requests
from datetime import datetime
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_time_factors():
    """Проверяет факторы времени которые могут влиять на результаты"""
    
    logger.info("ПРОВЕРКА ВРЕМЕННЫХ ФАКТОРОВ")
    logger.info("="*40)
    
    # Текущее время в разных зонах
    utc_now = datetime.utcnow()
    moscow_tz = pytz.timezone('Europe/Moscow')
    moscow_now = utc_now.replace(tzinfo=pytz.UTC).astimezone(moscow_tz)
    
    logger.info(f"UTC время: {utc_now}")
    logger.info(f"Московское время: {moscow_now}")
    
    # Проверка доступности CryptoCompare API
    try:
        response = requests.get('https://min-api.cryptocompare.com/data/pricemulti?fsyms=BTC&tsyms=USD', timeout=10)
        if response.status_code == 200:
            data = response.json()
            btc_price = data.get('BTC', {}).get('USD', 'N/A')
            logger.info(f"BTC цена (проверка API): ${btc_price:,}" if isinstance(btc_price, (int, float)) else f"BTC цена: {btc_price}")
        else:
            logger.warning(f"API ответ: {response.status_code}")
    except Exception as e:
        logger.error(f"Ошибка API: {e}")
    
    logger.info("\nВОЗМОЖНЫЕ ПРИЧИНЫ РАЗЛИЧИЙ:")
    logger.info("1. Разное время запроса (данные обновляются каждые несколько минут)")
    logger.info("2. Разные API ключи (могут давать разные лимиты/данные)")
    logger.info("3. Кеширование на стороне CryptoCompare API")
    logger.info("4. Различия в версиях библиотек")

if __name__ == "__main__":
    check_time_factors()