# src/utils/data_loader.py
import pandas as pd
from twelvedata import TDClient
# Импортируем ключ напрямую из config, так как config.py должен быть доступен через src.config
# from src.config import TWELVE_DATA_API_KEY # Ключ будет передан как аргумент функции

def load_historical_data_twelvedata(api_key, symbol, interval, outputsize=500, timezone="Etc/UTC"):
    """
    Загружает исторические данные с помощью Twelve Data API.

    Args:
        api_key (str): Ваш API ключ для Twelve Data.
        symbol (str): Торговый символ (например, "EUR/USD").
        interval (str): Таймфрейм (например, "1h", "15min", "1day").
        outputsize (int): Количество возвращаемых точек данных. Макс. 5000 для некоторых планов.
        timezone (str): Часовой пояс для данных. Рекомендуется UTC.

    Returns:
        pandas.DataFrame: DataFrame с OHLCV данными, индексированный по Timestamp,
                          или None в случае ошибки.
    """
    if not api_key or api_key == "YOUR_TWELVE_DATA_API_KEY_PLACEHOLDER":
        print("Ошибка в data_loader: API ключ для Twelve Data не предоставлен или является заглушкой.")
        return None

    try:
        td = TDClient(apikey=api_key)
        ts = td.time_series(
            symbol=symbol,
            interval=interval,
            outputsize=outputsize,
            timezone=timezone
        )

        if ts is None:
            print(f"Не удалось получить данные для {symbol} {interval} от Twelve Data. Ответ API был None.")
            return None

        df = ts.as_pandas()

        if df.empty:
            print(f"Данные для {symbol} {interval} от Twelve Data пусты.")
            return None

        # Twelve Data возвращает данные в обратном хронологическом порядке (новые вверху)
        # Пересортируем, чтобы старые были вверху (индекс от меньшего к большему)
        df = df.iloc[::-1]

        # Приведем названия колонок к нашему стандарту (Open, High, Low, Close, Volume)
        # Twelve Data обычно использует 'open', 'high', 'low', 'close', 'volume'
        df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }, inplace=True)
        
        # Убедимся, что индекс это DateTimeIndex (as_pandas обычно это делает)
        df.index.name = 'Timestamp'
        # Конвертируем числовые колонки в float, если они еще не такие
        cols_to_numeric = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in cols_to_numeric:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')


        print(f"Данные для {symbol} {interval} успешно загружены из Twelve Data. Всего записей: {len(df)}")
        return df

    except Exception as e:
        print(f"Ошибка при загрузке данных из Twelve Data: {e}")
        return None
