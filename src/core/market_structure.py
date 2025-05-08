# src/core/market_structure.py (Очень Упрощенно)
import pandas as pd

def get_swing_highs_lows(df, window=5):
    """
    Упрощенное определение свинг-максимумов и минимумов.
    Нуждается в значительной доработке для точности.
    Это базовый пример, реальные свинг-точки определяются сложнее.
    """
    # df['Swing_High'] = df['High'][(df['High'].shift(1) < df['High']) & (df['High'].shift(-1) < df['High'])]
    # df['Swing_Low'] = df['Low'][(df['Low'].shift(1) > df['Low']) & (df['Low'].shift(-1) > df['Low'])]
    
    # Более простой вариант для примера, который просто находит локальные пики/впадины
    # Этот метод не идеален и требует доработки
    df['Swing_High'] = df['High'].rolling(window=window*2+1, center=True).apply(lambda x: x.iloc[window] if x.iloc[window] == x.max() else float('nan'), raw=False)
    df['Swing_Low'] = df['Low'].rolling(window=window*2+1, center=True).apply(lambda x: x.iloc[window] if x.iloc[window] == x.min() else float('nan'), raw=False)
    return df

def check_bos(current_price, last_significant_high, is_uptrend):
    """
    Упрощенная проверка Break of Structure (BOS).
    Для лонга: current_price пробивает last_significant_high.
    """
    if is_uptrend and current_price > last_significant_high:
        return True
    elif not is_uptrend and current_price < last_significant_high: # last_significant_low
        return True
    return False

def check_choch(current_price, last_relevant_swing_point, is_expecting_reversal_up):
    """
    Упрощенная проверка Change of Character (CHoCH).
    Для разворота вверх: цена пробивает последний minor high, который привел к LL.
    last_relevant_swing_point: для разворота вверх - это последний свинг-хай перед новым минимумом.
                               для разворота вниз - это последний свинг-лоу перед новым максимумом.
    """
    if is_expecting_reversal_up and current_price > last_relevant_swing_point:
        return True
    elif not is_expecting_reversal_up and current_price < last_relevant_swing_point:
        return True
    return False

# TODO: Добавить более продвинутые методы определения структуры рынка
