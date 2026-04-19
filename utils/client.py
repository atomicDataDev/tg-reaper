"""
TelegramClient Factory with Anti-Detection Parameters.
All modules must use create_client() instead of directly instantiating TelegramClient().

The unified Desktop User-Agent ensures consistency with the Session Manager,
preventing session termination caused by device switching.
"""

import os
from telethon import TelegramClient

from config import API_ID, API_HASH
from utils.device import get_device_for_session


def create_client(
    session_path: str,
    *,
    receive_updates: bool = True,
    flood_sleep_threshold: int = 60,
    request_retries: int = 5,
    connection_retries: int = 5,
    retry_delay: int = 1,
    auto_reconnect: bool = True,
    timeout: int = 30,
) -> TelegramClient:
    """
    Creates a TelegramClient instance with a fixed Desktop hardware profile.
    
    Device parameters are identical to the Session Manager, ensuring 
    that sessions remain stable and are not terminated by Telegram's security system.

    Args:
        session_path (str): Full path to the .session file.
        receive_updates (bool): Whether to handle incoming updates (False saves traffic/resources).
        flood_sleep_threshold (int): Max seconds to auto-sleep on FloodWait errors.
        request_retries (int): Number of retries for individual requests.
        connection_retries (int): Number of connection attempt retries.
        retry_delay (int): Delay between retry attempts in seconds.
        auto_reconnect (bool): Automatically attempt to reconnect on disconnect.
        timeout (int): Connection timeout in seconds.

    Returns:
        TelegramClient: Configured Telethon client instance.
    """
    device = get_device_for_session(session_path)

    client = TelegramClient(
        session_path,
        API_ID,
        API_HASH,
        device_model=device["device_model"],
        system_version=device["system_version"],
        app_version=device["app_version"],
        lang_code=device["lang_code"],
        system_lang_code=device["system_lang_code"],
        flood_sleep_threshold=flood_sleep_threshold,
        request_retries=request_retries,
        connection_retries=connection_retries,
        retry_delay=retry_delay,
        auto_reconnect=auto_reconnect,
        timeout=timeout,
        receive_updates=receive_updates,
    )

    return client


def get_session_name(session_path: str) -> str:
    """Returns the session name without the file extension"""
    return os.path.basename(session_path)