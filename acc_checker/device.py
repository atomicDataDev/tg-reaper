"""
Эмуляция устройства Telegram.
ОДИН фиксированный Desktop профиль для ВСЕХ сессий и ВСЕХ программ.

ВАЖНО: Этот файл ДОЛЖЕН быть идентичен файлу utils/device.py в TG REAPER.
Любое расхождение в DESKTOP_DEVICE = слёт сессий при открытии
одной сессии разными программами.

НЕ МЕНЯТЬ DESKTOP_DEVICE после создания сессий!
"""


DESKTOP_DEVICE = {
    "device_model": "Desktop",
    "system_version": "Windows 10",
    "app_version": "4.16.8 x64",
    "lang_code": "en",
    "system_lang_code": "en-US",
}


def get_device_for_session(session_path: str) -> dict:
    """
    Возвращает ОДИН И ТОТ ЖЕ Desktop профиль для любой сессии.

    Параметр session_path сохранён для обратной совместимости,
    но НЕ влияет на результат — профиль всегда одинаковый.

    Гарантирует:
    - Session Manager открывает сессию → Desktop Windows 10
    - TG REAPER открывает сессию → Desktop Windows 10
    - Telegram видит одно устройство → сессия НЕ слетает

    Args:
        session_path: путь к файлу сессии (игнорируется)

    Returns:
        dict с параметрами устройства (всегда одинаковый)
    """
    return DESKTOP_DEVICE.copy()