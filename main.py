# main.py
import os
import pandas as pd
from datetime import datetime, timedelta

from src.utils.data_loader import load_historical_data_twelvedata
from src.strategies.amd_smc_strategy import AmdSMCStrategy
from src.config import (
    TRADING_PAIR, TIMEFRAME_CONTEXT, TIMEFRAME_EXECUTION, TWELVE_DATA_API_KEY,
    # Импортируем все параметры, которые могут понадобиться стратегии
    TRADING_SESSIONS_UTC, FILTER_BY_TRADING_SESSIONS,
    ACC_DIST_BARS_MIN, ACC_DIST_BARS_MAX, ACC_DIST_VOLATILITY_THRESHOLD, ACC_DIST_PRIOR_TREND_LOOKBACK,
    MANIPULATION_SWEEP_DEPTH_ATR_FACTOR, MANIPULATION_RECOVERY_BARS,
    CHOSHBOS_IMPULSE_ATR_FACTOR,
    POI_DISCOUNT_THRESHOLD, POI_PREMIUM_THRESHOLD, FVG_MIN_SIZE_ATR_FACTOR,
    SL_ATR_MULTIPLIER_EXECUTION, SL_OFFSET_POINTS, TAKE_PROFIT_RR_RATIO
)

def run_strategy_backtest():
    print("Запуск бэктеста стратегии AMD SMC с двумя таймфреймами...")

    if not TWELVE_DATA_API_KEY or TWELVE_DATA_API_KEY == "YOUR_TWELVE_DATA_API_KEY_PLACEHOLDER":
        print("ОШИБКА: API ключ для Twelve Data не настроен.")
        return

    # Собираем все параметры конфигурации в один словарь для передачи в стратегию
    strategy_config_params = {
        "FILTER_BY_TRADING_SESSIONS": FILTER_BY_TRADING_SESSIONS,
        "TRADING_SESSIONS_UTC": TRADING_SESSIONS_UTC,
        "ACC_DIST_BARS_MIN": ACC_DIST_BARS_MIN,
        "ACC_DIST_BARS_MAX": ACC_DIST_BARS_MAX,
        "ACC_DIST_VOLATILITY_THRESHOLD": ACC_DIST_VOLATILITY_THRESHOLD,
        "ACC_DIST_PRIOR_TREND_LOOKBACK": ACC_DIST_PRIOR_TREND_LOOKBACK,
        "MANIPULATION_SWEEP_DEPTH_ATR_FACTOR": MANIPULATION_SWEEP_DEPTH_ATR_FACTOR,
        "MANIPULATION_RECOVERY_BARS": MANIPULATION_RECOVERY_BARS,
        "CHOSHBOS_IMPULSE_ATR_FACTOR": CHOSHBOS_IMPULSE_ATR_FACTOR,
        "POI_DISCOUNT_THRESHOLD": POI_DISCOUNT_THRESHOLD,
        "POI_PREMIUM_THRESHOLD": POI_PREMIUM_THRESHOLD,
        "FVG_MIN_SIZE_ATR_FACTOR": FVG_MIN_SIZE_ATR_FACTOR,
        "SL_ATR_MULTIPLIER_EXECUTION": SL_ATR_MULTIPLIER_EXECUTION,
        "SL_OFFSET_POINTS": SL_OFFSET_POINTS,
        "TAKE_PROFIT_RR_RATIO": TAKE_PROFIT_RR_RATIO,
        # Добавьте другие параметры из config.py по мере необходимости
    }

    # 1. Загрузка данных для обоих таймфреймов
    # Увеличьте outputsize для достаточной истории
    print(f"Загрузка данных M15 ({TIMEFRAME_CONTEXT}) для {TRADING_PAIR}...")
    data_m15 = load_historical_data_twelvedata(
        api_key=TWELVE_DATA_API_KEY,
        symbol=TRADING_PAIR,
        interval=TIMEFRAME_CONTEXT,
        outputsize=1500 # Примерно 15 дней для M15
    )
    if data_m15 is None or data_m15.empty:
        print(f"Не удалось загрузить данные M15 для {TRADING_PAIR}.")
        return

    print(f"Загрузка данных M5 ({TIMEFRAME_EXECUTION}) для {TRADING_PAIR}...")
    data_m5 = load_historical_data_twelvedata(
        api_key=TWELVE_DATA_API_KEY,
        symbol=TRADING_PAIR,
        interval=TIMEFRAME_EXECUTION,
        outputsize=4500 # Столько же по времени, 15 дней * 3 (M15/M5)
    )
    if data_m5 is None or data_m5.empty:
        print(f"Не удалось загрузить данные M5 для {TRADING_PAIR}.")
        return
    
    print(f"Данные M15: {len(data_m15)} свечей, M5: {len(data_m5)} свечей.")

    # 2. Инициализация стратегии
    strategy = AmdSMCStrategy(df_context=data_m15, df_execution=data_m5, config_params=strategy_config_params)
    print("Стратегия инициализирована.")

    # 3. Цикл по свечам M5 для бэктестинга
    # Убедимся, что начинаем с момента, когда есть достаточно истории на M15
    # Найдем общую начальную дату, чтобы синхронизировать данные
    common_start_time = max(data_m15.index.min(), data_m5.index.min())
    
    # Отфильтруем данные, чтобы они начинались с общего времени
    data_m5_aligned = data_m5[data_m5.index >= common_start_time]
    
    # Начальный lookback для M15 (например, ACC_DIST_PRIOR_TREND_LOOKBACK + ACC_DIST_BARS_MAX)
    # чтобы у стратегии было достаточно данных для анализа M15 контекста с первой же M5 свечи.
    # Это упрощение; в реальности нужно аккуратно передавать срезы.
    
    min_m15_history_needed_for_start = strategy_config_params.get("ACC_DIST_PRIOR_TREND_LOOKBACK", 100) + \
                                       strategy_config_params.get("ACC_DIST_BARS_MAX", 50)

    signals_generated = []

    print(f"\nНачало бэктеста по свечам M5 с {data_m5_aligned.index.min()}...")
    for m5_candle_timestamp, m5_candle in data_m5_aligned.iterrows():
        # Получаем актуальный срез данных M15 до текущего времени M5
        # ВАЖНО: m15_slice должен содержать только ЗАКРЫТЫЕ M15 свечи
        # То есть, если m5_candle в 10:05, последняя закрытая M15 свеча - это 10:00.
        # Если m5_candle в 10:15, то M15 свеча 10:15 только что закрылась.
        
        # Округляем время M5 свечи вниз до ближайшего M15 интервала
        # (или берем M15 свечи, чье время <= времени M5 свечи)
        m15_slice_end_time = m5_candle_timestamp
        m15_relevant_slice = data_m15[data_m15.index <= m15_slice_end_time]

        if len(m15_relevant_slice) < min_m15_history_needed_for_start:
            continue # Недостаточно истории M15 для анализа

        # Передаем текущее время UTC (время закрытия M5 свечи)
        current_utc_time = pd.to_datetime(m5_candle_timestamp).tz_localize('UTC') # Убедимся, что UTC

        signal = strategy.process_new_candle(current_utc_time, m5_candle, m15_relevant_slice)
        
        if signal:
            signals_generated.append(signal)
            print(f"Сгенерирован сигнал: {signal}")

    print(f"\nБэктест завершен. Всего сигналов: {len(signals_generated)}")
    # Дальнейший анализ сигналов...

if __name__ == "__main__":
    # Для отладки путей и загрузки .env
    print(f"Текущая рабочая директория: {os.getcwd()}")
    project_r = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    env_p = os.path.join(project_r, '.env')
    print(f"Ожидаемый путь к .env: {env_p}, существует ли: {os.path.exists(env_p)}")
    
    run_strategy_backtest()
