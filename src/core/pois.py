# src/core/pois.py (Points of Interest - Order Blocks, FVG - Упрощенно)
import pandas as pd
import numpy as np # Для np.nan

def find_fvg(df_slice, candle_index, is_bullish_fvg_needed=True, fvg_min_size_atr_factor=0.0, atr_series=None):
    """
    Ищет Fair Value Gap (FVG) / Imbalance.
    Bullish FVG: Low[candle_index] > High[candle_index-2] (разрыв между candle_index-2 и candle_index, candle_index-1 импульсная вверх)
    Bearish FVG: High[candle_index] < Low[candle_index-2] (разрыв, candle_index-1 импульсная вниз)

    Args:
        df_slice (pd.DataFrame): Срез данных.
        candle_index (int): Индекс ПОСЛЕДНЕЙ из трех свечей, формирующих FVG, в df_slice.
        is_bullish_fvg_needed (bool): True для бычьего FVG, False для медвежьего.
        fvg_min_size_atr_factor (float): Минимальный размер FVG как множитель ATR. Если 0, не проверяется.
        atr_series (pd.Series, optional): Серия значений ATR для проверки минимального размера FVG.

    Returns:
        dict or None: Информация о FVG или None.
    """
    if candle_index < 2 or candle_index >= len(df_slice):
        return None

    candle_curr = df_slice.iloc[candle_index]
    candle_prev1 = df_slice.iloc[candle_index - 1] # Потенциально импульсная свеча
    candle_prev2 = df_slice.iloc[candle_index - 2]

    fvg_info = None
    fvg_top, fvg_bottom = np.nan, np.nan

    if is_bullish_fvg_needed:
        if candle_curr['Low'] > candle_prev2['High']: # Условие дисбаланса
            fvg_top = candle_curr['Low']
            fvg_bottom = candle_prev2['High']
            fvg_type = 'bullish_fvg'
    else: # Ищем медвежий FVG
        if candle_curr['High'] < candle_prev2['Low']: # Условие дисбаланса
            fvg_top = candle_prev2['Low']
            fvg_bottom = candle_curr['High']
            fvg_type = 'bearish_fvg'

    if pd.notna(fvg_top) and pd.notna(fvg_bottom) and fvg_top > fvg_bottom:
        fvg_size = fvg_top - fvg_bottom
        min_size_check_passed = True
        if fvg_min_size_atr_factor > 0 and atr_series is not None and not atr_series.empty:
            atr_val = atr_series.iloc[candle_index -1] # ATR на момент импульсной свечи
            if pd.notna(atr_val) and fvg_size < (fvg_min_size_atr_factor * atr_val):
                min_size_check_passed = False
        
        if min_size_check_passed:
            return {
                'type': fvg_type,
                'top': fvg_top,
                'bottom': fvg_bottom,
                'size': fvg_size,
                'middle_candle_index_in_slice': candle_index - 1,
                'timestamp': df_slice.index[candle_index - 1]
            }
    return None

def find_inverted_fvg(df_slice, fvg_to_invert, bos_choch_candle_index):
    """
    Проверяет, был ли данный FVG "инвертирован" (пробит) импульсным движением BOS/CHoCH.
    Инвертированный FVG становится зоной поддержки/сопротивления.

    Args:
        df_slice (pd.DataFrame): Срез данных.
        fvg_to_invert (dict): Словарь с информацией о FVG, полученный от find_fvg.
        bos_choch_candle_index (int): Индекс свечи в df_slice, которая совершила BOS/CHoCH, пробив FVG.

    Returns:
        dict or None: Информация об инвертированном FVG или None.
    """
    if not fvg_to_invert or bos_choch_candle_index >= len(df_slice):
        return None

    candle_bos_choch = df_slice.iloc[bos_choch_candle_index]
    inverted_fvg_info = None

    if fvg_to_invert['type'] == 'bearish_fvg': # Изначально был медвежий FVG, ищем бычий разворот
        # Цена должна была закрыться ВЫШЕ верхней границы медвежьего FVG
        if candle_bos_choch['Close'] > fvg_to_invert['top']:
            inverted_fvg_info = {
                'type': 'inverted_bullish_fvg', # Бывшая зона сопротивления стала поддержкой
                'original_fvg_type': fvg_to_invert['type'],
                'top': fvg_to_invert['top'], # Границы оригинального FVG
                'bottom': fvg_to_invert['bottom'],
                'size': fvg_to_invert['size'],
                'inverted_by_candle_index': bos_choch_candle_index,
                'timestamp': df_slice.index[bos_choch_candle_index]
            }
    elif fvg_to_invert['type'] == 'bullish_fvg': # Изначально был бычий FVG, ищем медвежий разворот
        # Цена должна была закрыться НИЖЕ нижней границы бычьего FVG
        if candle_bos_choch['Close'] < fvg_to_invert['bottom']:
            inverted_fvg_info = {
                'type': 'inverted_bearish_fvg', # Бывшая зона поддержки стала сопротивлением
                'original_fvg_type': fvg_to_invert['type'],
                'top': fvg_to_invert['top'],
                'bottom': fvg_to_invert['bottom'],
                'size': fvg_to_invert['size'],
                'inverted_by_candle_index': bos_choch_candle_index,
                'timestamp': df_slice.index[bos_choch_candle_index]
            }
    
    return inverted_fvg_info


def find_order_blocks(df_slice, candle_index, is_bullish_ob_needed=True, lookback=5):
    """
    Упрощенный поиск Order Block.
    Bullish OB: последняя медвежья свеча перед сильным ростом.
    Bearish OB: последняя бычья свеча перед сильным падением.
    candle_index: индекс свечи, ПОСЛЕ которой ищем OB (т.е. OB формируется до этой свечи).

    Возвращает словарь с информацией об OB или None.
    """
    # Эта функция остается очень упрощенной. В реальном SMC OB должен вызвать смещение цены (displacement)
    # и оставить за собой FVG или совершить BOS.
    
    # Ищем ОБ перед `candle_index`
    search_start_index = candle_index - 1
    if search_start_index < 0: return None

    for i in range(search_start_index, max(-1, search_start_index - lookback -1), -1):
        if i < 0 or i+1 >= len(df_slice): continue # Выход за пределы

        candle_ob_candidate = df_slice.iloc[i]
        # Свеча, следующая за кандидатом в ОБ, должна быть импульсной
        # Для простоты, здесь не проверяем импульс детально, а лишь направление
        # candle_after_ob = df_slice.iloc[i+1]

        if is_bullish_ob_needed: # Ищем бычий ОБ (медвежья свеча)
            if candle_ob_candidate['Close'] < candle_ob_candidate['Open']: # Медвежья свеча
                # Условие: следующая свеча должна поглотить эту или быть сильной бычьей
                # if candle_after_ob['Close'] > candle_ob_candidate['Open']: # Пример простого поглощения
                return {
                    'type': 'bullish_ob', 
                    'top': candle_ob_candidate['High'], 
                    'bottom': candle_ob_candidate['Low'],
                    'open': candle_ob_candidate['Open'],
                    'close': candle_ob_candidate['Close'],
                    'index_in_slice': i,
                    'timestamp': df_slice.index[i]
                }
        else: # Ищем медвежий ОБ (бычья свеча)
            if candle_ob_candidate['Close'] > candle_ob_candidate['Open']: # Бычья свеча
                # if candle_after_ob['Close'] < candle_ob_candidate['Open']:
                return {
                    'type': 'bearish_ob', 
                    'top': candle_ob_candidate['High'], 
                    'bottom': candle_ob_candidate['Low'],
                    'open': candle_ob_candidate['Open'],
                    'close': candle_ob_candidate['Close'],
                    'index_in_slice': i,
                    'timestamp': df_slice.index[i]
                }
    return None
