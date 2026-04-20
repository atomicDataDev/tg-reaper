"""
Telegram Device Emulation.
Uses a SINGLE fixed Desktop profile for ALL sessions.

Why Desktop:
- Telegram Desktop allows multiple simultaneous sessions.
- Less suspicion during mass automation tasks.
- Prevents session termination caused by device_model or system_version mismatches.
- Compatible with .session files created by other management tools.

Why a SINGLE profile:
- When a session opens, Telethon sends 'initConnection' with specific device parameters.
- If these parameters differ from those used during session creation, 
  Telegram may revoke the authorization (log out).
- A unified profile ensures stability and prevents sessions from being dropped.
"""


# -- Unified Desktop Profile for All Sessions --------------------

DESKTOP_DEVICE = {
    "device_model": "Desktop",
    "system_version": "Windows 10",
    "app_version": "4.16.8 x64",
    "lang_code": "en",
    "system_lang_code": "en-US",
}


def get_device_for_session(session_path: str) -> dict:
    """
    Returns the EXACT SAME Desktop profile for every session.
    
    This is critically important for stability:
    - Telethon triggers an 'initConnection' call using these parameters during connect().
    - If the device_model or system_version changes between launches, 
      Telegram is likely to terminate the session.
    - Using a fixed profile ensures sessions DO NOT drop.
    
    Args:
        session_path (str): The path to the session file (currently unused, 
                           but kept for interface backward compatibility).
    
    Returns:
        dict: A dictionary containing the device parameters (always identical).
    """
    return DESKTOP_DEVICE.copy()