"""
Session File Management and Validation.
"""

import os
from utils.client import create_client
from ui import print_sessions_table


def get_session_files(directory: str) -> list[str]:
    """
    Scans a directory for .session files and returns their paths without extensions.
    
    If the directory does not exist, it will be created automatically.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        return []
    
    files = []
    # Sort files for consistent output in the UI
    for f in sorted(os.listdir(directory)):
        if f.endswith(".session"):
            # Return path without .session extension as required by Telethon
            session_path = os.path.join(directory, f.replace(".session", ""))
            files.append(session_path)
    return files


def print_sessions(sessions: list[str]):
    """
    Displays the list of sessions in a formatted UI table.
    """
    print_sessions_table(sessions)


async def find_working_session(sessions: list[str]) -> str | None:
    """
    Iterates through session files and returns the path of the first authorized session.
    
    Utilizes create_client() to maintain a unified Desktop User-Agent,
    preventing session revocation during the check.
    """
    for s in sessions:
        # Initialize client with updates disabled to save resources
        client = create_client(s, receive_updates=False)
        try:
            await client.connect()
            if await client.is_user_authorized():
                await client.disconnect()
                return s
        except Exception:
            # Silently ignore errors (connection issues, banned accounts, etc.)
            pass
        finally:
            # Ensure the client is always closed properly
            try:
                await client.disconnect()
            except Exception:
                pass
    return None