"""Factory of Telethon clients.
Proxy automatically from accounts.json.
Device profile is fixed for each session."""

import os
from telethon import TelegramClient

from config import API_ID, API_HASH
from core.account_store import get_device_for_session


def get_session_name(session_path: str) -> str:
    return os.path.basename(session_path).replace(".session", "")


def create_client(
    session_path: str,
    receive_updates: bool = True,
) -> TelegramClient:
    """Creates a TelegramClient with device from accounts.json."""
    device = get_device_for_session(session_path)

    client = TelegramClient(
        session_path,
        API_ID,
        API_HASH,
        device_model=device.get("device_model", "Desktop"),
        system_version=device.get("system_version", "Windows 10"),
        app_version=device.get("app_version", "4.16.8 x64"),
        lang_code=device.get("lang_code", "en"),
        system_lang_code=device.get("system_lang_code", "en-US"),
        receive_updates=receive_updates,
        timeout=20,
        connection_retries=3,
        retry_delay=2,
        request_retries=3,
    )

    return client