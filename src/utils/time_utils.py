# src/utils/time_utils.py
from datetime import datetime, time
import pytz # pip install pytz

def is_within_trading_session(current_dt_utc, sessions_config):
    """
    Проверяет, находится ли текущее время UTC в одной из заданных торговых сессий.

    Args:
        current_dt_utc (datetime): Текущее время и дата в UTC (timezone-aware).
        sessions_config (dict): Словарь конфигурации сессий из src/config.py.
                               Пример: {"London": {"start": "07:00", "end": "16:00"}, ...}
    Returns:
        bool: True, если время попадает в одну из сессий, иначе False.
        str: Название сессии, если время попадает, иначе None.
    """
    if not current_dt_utc.tzinfo:
        # print("Предупреждение: current_dt_utc не имеет информации о часовом поясе. Предполагается UTC.")
        current_dt_utc = pytz.utc.localize(current_dt_utc)
    else:
        current_dt_utc = current_dt_utc.astimezone(pytz.utc)

    current_time_utc = current_dt_utc.time()

    for session_name, times in sessions_config.items():
        try:
            start_time = datetime.strptime(times['start'], '%H:%M').time()
            end_time = datetime.strptime(times['end'], '%H:%M').time()

            if start_time <= end_time:
                # Сессия не пересекает полночь
                if start_time <= current_time_utc <= end_time:
                    return True, session_name
            else:
                # Сессия пересекает полночь (например, с 22:00 до 05:00)
                if current_time_utc >= start_time or current_time_utc <= end_time:
                    return True, session_name
        except ValueError:
            print(f"Ошибка: Неверный формат времени для сессии '{session_name}' в конфигурации.")
            continue
    return False, None

if __name__ == '__main__':
    # Пример использования
    from src.config import TRADING_SESSIONS_UTC # Убедитесь, что config.py доступен

    test_time_london = pytz.utc.localize(datetime.utcnow().replace(hour=8, minute=30, second=0, microsecond=0))
    test_time_ny_am = pytz.utc.localize(datetime.utcnow().replace(hour=14, minute=30, second=0, microsecond=0))
    test_time_ny_pm = pytz.utc.localize(datetime.utcnow().replace(hour=18, minute=30, second=0, microsecond=0))
    test_time_off_session = pytz.utc.localize(datetime.utcnow().replace(hour=3, minute=30, second=0, microsecond=0))

    print(f"Текущее время UTC: {pytz.utc.localize(datetime.utcnow())}")
    
    is_active, session = is_within_trading_session(test_time_london, TRADING_SESSIONS_UTC)
    print(f"Время {test_time_london.time()} в сессии? {is_active}, Сессия: {session}")

    is_active, session = is_within_trading_session(test_time_ny_am, TRADING_SESSIONS_UTC)
    print(f"Время {test_time_ny_am.time()} в сессии? {is_active}, Сессия: {session}")

    is_active, session = is_within_trading_session(test_time_ny_pm, TRADING_SESSIONS_UTC)
    print(f"Время {test_time_ny_pm.time()} в сессии? {is_active}, Сессия: {session}")

    is_active, session = is_within_trading_session(test_time_off_session, TRADING_SESSIONS_UTC)
    print(f"Время {test_time_off_session.time()} в сессии? {is_active}, Сессия: {session}")
