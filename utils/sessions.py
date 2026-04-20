"""Working with session files."""

import os
from core.client_factory import create_client
from ui import print_sessions_table


def get_session_files(directory: str = None) -> list[str]:
    from config import SESSIONS_DIR
    directory = directory or SESSIONS_DIR
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        return []
    files = []
    for f in sorted(os.listdir(directory)):
        if f.endswith(".session") and not f.startswith("_temp_"):
            files.append(
                os.path.join(directory, f.replace(".session", ""))
            )
    return files


def get_session_names(directory: str = None) -> list[str]:
    """Returns only session names (without path)."""
    from config import SESSIONS_DIR
    directory = directory or SESSIONS_DIR
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        return []
    names = []
    for f in sorted(os.listdir(directory)):
        if f.endswith(".session") and not f.startswith("_temp_"):
            names.append(f[:-8])
    return names


def print_sessions(sessions: list[str]):
    print_sessions_table(sessions)


async def find_working_session(sessions: list[str]) -> str | None:
    for s in sessions:
        client = create_client(s, receive_updates=False)
        try:
            await client.connect()
            if await client.is_user_authorized():
                await client.disconnect()
                return s
        except Exception:
            pass
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass
    return None