# src/core/liquidity.py
import pandas as pd

def identify_significant_liquidity_levels(df_context, lookback_period, num_levels=1):
    """
    Идентифицирует значимые уровни ликвидности (BSL/SSL) на контекстном таймфрейме (например, M15).
    Возвращает словари с BSL (самые высокие High) и SSL (самые низкие Low) за lookback_period.
    """
    if len(df_context) < lookback_period:
        return {'BSL': [], 'SSL': []}

    relevant_data = df_context.iloc[-lookback_period:]
    
    # Находим N самых высоких максимумов
    top_bsl = relevant_data.nlargest(num_levels, 'High')
    bsl_levels = [{'price': row['High'], 'timestamp': idx} for idx, row in top_bsl.iterrows()]

    # Находим N самых низких минимумов
    bottom_ssl = relevant_data.nsmallest(num_levels, 'Low')
    ssl_levels = [{'price': row['Low'], 'timestamp': idx} for idx, row in bottom_ssl.iterrows()]
    
    return {'BSL': bsl_levels, 'SSL': ssl_levels}


def check_liquidity_sweep_and_recovery(df_context_candle, target_liquidity_level,
                                       is_sweeping_below_ssl=True,
                                       recovery_bars_config=1,
                                       sweep_depth_atr_factor=0.0,
                                       atr_value_at_sweep=None):
    """
    Проверяет, произошел ли сбор ликвидности за target_liquidity_level и быстрый возврат.
    Args:
        df_context_candle (pd.Series): Текущая свеча контекстного таймфрейма (M15).
        target_liquidity_level (float): Цена уровня ликвидности (SSL или BSL).
        is_sweeping_below_ssl (bool): True, если ожидаем свип SSL (цена идет вниз).
                                     False, если ожидаем свип BSL (цена идет вверх).
        recovery_bars_config (int): Не используется в этой версии, так как проверяем по одной свече.
                                    В будущем можно анализировать несколько свечей для возврата.
        sweep_depth_atr_factor (float): Если > 0, проверяет минимальную глубину свипа.
        atr_value_at_sweep (float, optional): Значение ATR для проверки глубины.

    Returns:
        bool: True, если свип и возврат подтверждены на данной свече.
        float: Цена экстремума свипа (Low для SSL, High для BSL).
    """
    swept_price = None
    recovered = False

    if is_sweeping_below_ssl: # Свип SSL
        if df_context_candle['Low'] < target_liquidity_level:
            swept_price = df_context_candle['Low']
            depth_check_passed = True
            if sweep_depth_atr_factor > 0 and atr_value_at_sweep is not None:
                if (target_liquidity_level - swept_price) < (sweep_depth_atr_factor * atr_value_at_sweep):
                    depth_check_passed = False
            
            if depth_check_passed and df_context_candle['Close'] > target_liquidity_level: # Цена закрылась выше SSL
                recovered = True
    else: # Свип BSL
        if df_context_candle['High'] > target_liquidity_level:
            swept_price = df_context_candle['High']
            depth_check_passed = True
            if sweep_depth_atr_factor > 0 and atr_value_at_sweep is not None:
                if (swept_price - target_liquidity_level) < (sweep_depth_atr_factor * atr_value_at_sweep):
                    depth_check_passed = False

            if depth_check_passed and df_context_candle['Close'] < target_liquidity_level: # Цена закрылась ниже BSL
                recovered = True
    
    return recovered, swept_price
