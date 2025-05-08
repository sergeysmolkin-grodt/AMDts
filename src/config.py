# src/config.py

import os
from dotenv import load_dotenv

# Определение пути к корневой папке проекта (где находится main.py и .env)
# __file__ это src/config.py
# os.path.dirname(__file__) это src/
# os.path.join(os.path.dirname(__file__), '..') это корень проекта
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
dotenv_path = os.path.join(project_root, '.env')

# Загружаем переменные из .env файла, если он существует
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    # print(f".env файл найден и загружен из: {dotenv_path}") # для отладки
else:
    # print(f".env файл НЕ найден по пути: {dotenv_path}") # для отладки
    pass

# --- Twelve Data Configuration ---
# Загружаем API ключ из переменных окружения (которые были установлены из .env или системой)
TWELVE_DATA_API_KEY = os.getenv("TWELVEDATA_API_KEY")

if not TWELVE_DATA_API_KEY:
    print("ПРЕДУПРЕЖДЕНИЕ в config.py: API ключ TWELVEDATA_API_KEY не найден в переменных окружения или .env файле.")
    print("Пожалуйста, настройте его для доступа к Twelve Data. Установите значение по умолчанию или обработайте в коде.")
    TWELVE_DATA_API_KEY = "YOUR_TWELVE_DATA_API_KEY_PLACEHOLDER" # Заглушка, если ключ не найден

# Формат символа для Twelve Data (например, "EUR/USD")
TRADING_PAIR = "EUR/USD"
# Интервалы для Twelve Data: 1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 1day, 1week, 1month
TIMEFRAME = "1h" # Используем "1h" вместо "H1" для совместимости с Twelve Data

# --- Параметры стратегии ---
ACCUMULATION_RANGE_BARS = 50  # Количество свечей для анализа диапазона накопления/распределения
ACCUMULATION_VOLATILITY_THRESHOLD = 0.005 # Примерный порог для волатильности ATR (нужно настроить)

# Параметры для SMC
ORDER_BLOCK_REFINEMENT_PERCENT = 0.5 # Для определения тела ордер-блока (не используется в текущем упрощенном коде)
FVG_IMBALANCE_THRESHOLD = 0.001 # Минимальный размер дисбаланса (в пунктах или процентах, не используется в текущем коде)

# Параметры риска (примерные, для будущей реализации)
STOP_LOSS_ATR_MULTIPLIER = 1.5
TAKE_PROFIT_RR_RATIO = 2.0 # Соотношение риск/прибыль

LOG_LEVEL = "INFO" # Уровни логирования: DEBUG, INFO, WARNING, ERROR
