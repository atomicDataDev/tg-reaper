"""Account storage - accounts.json.

Device profile is generated ONCE when creating an entry
and NEVER changes. Every session always connects
with the same User-Agent."""

import os
import json
from datetime import datetime

from config import SESSIONS_DIR
from core.device_profiles import generate_random_device


ACCOUNTS_FILE = "accounts.json"

_cache: dict | None = None


def _load() -> dict:
    global _cache
    if _cache is not None:
        return _cache
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                _cache = json.load(f)
        except (json.JSONDecodeError, IOError):
            _cache = {}
    else:
        _cache = {}
    return _cache


def _save(data: dict):
    global _cache
    _cache = data
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _key(session_path: str) -> str:
    return os.path.basename(session_path).replace(".session", "")


def invalidate_cache():
    """Clears the cache (for rereading from disk)."""
    global _cache
    _cache = None


def get_all_accounts() -> dict:
    return dict(_load())


def get_account(session_path: str) -> dict | None:
    data = _load()
    return data.get(_key(session_path))


def update_account_info(
    session_path: str,
    user_id: int = None,
    phone: str = None,
    username: str = None,
    first_name: str = None,
    last_name: str = None,
    status: str = None,
):
    """Updates account information.

    device - generated ONCE when the entry is first created.
    Subsequent calls NEVER overwrite device."""
    data = _load()
    key = _key(session_path)

    is_new = key not in data
    if is_new:
        data[key] = {}

    acc = data[key]
    acc["last_checked"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if user_id is not None:
        acc["user_id"] = user_id
    if phone is not None:
        acc["phone"] = phone
    if username is not None:
        acc["username"] = username
    if first_name is not None:
        acc["first_name"] = first_name
    if last_name is not None:
        acc["last_name"] = last_name
    if status is not None:
        acc["status"] = status

    # ═══════════════════════════════════════════════════════
    # Device: created ONLY when creating an entry for the first time.
    # After this, it is NEVER overwritten.
    # ═══════════════════════════════════════════════════════
    if "device" not in acc:
        acc["device"] = generate_random_device()

    _save(data)


def remove_account(session_path: str, delete_session_file: bool = True):
    data = _load()
    key = _key(session_path)

    if key in data:
        del data[key]
        _save(data)

    if delete_session_file:
        for ext in (".session", ".session-journal"):
            for path in [
                session_path + ext,
                os.path.join(SESSIONS_DIR, key + ext),
            ]:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass


def get_device_for_session(session_path: str) -> dict:
    """Returns the device profile for the session.

    If the entry exists in accounts.json - ALWAYS returns
    saved profile (same every time you call).

    If there is no record, it generates a new one, SAVES and returns.
    The next call will return the same thing."""
    data = _load()
    key = _key(session_path)

    if key in data and "device" in data[key]:
        return data[key]["device"]

    # No entry or no device - create and SAVE
    if key not in data:
        data[key] = {}

    device = generate_random_device()
    data[key]["device"] = device
    _save(data)

    return device



def sync_sessions_with_store() -> tuple[int, int]:
    """Synchronizes session files with accounts.json.
    New sessions receive a random device (saved forever).
    Existing ones are NOT touched."""
    data = _load()

    session_files = []
    if os.path.isdir(SESSIONS_DIR):
        for f in os.listdir(SESSIONS_DIR):
            if f.endswith(".session") and not f.startswith("_temp_"):
                session_files.append(f.replace(".session", ""))

    for name in session_files:
        if name not in data:
            data[name] = {
                "status": "unknown",
                "device": generate_random_device(),
            }

    _save(data)
    return len(session_files), len(data)