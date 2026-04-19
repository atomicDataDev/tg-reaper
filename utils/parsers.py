"""
Links, username, phone numbers parser
"""

import re


def parse_post_link(link: str) -> tuple:
    """Parses link for post in channel (канал + ID)."""
    m = re.match(r"https?://t\.me/([a-zA-Z_][a-zA-Z0-9_]{3,})/(\d+)", link)
    if m:
        return m.group(1), int(m.group(2))
    m = re.match(r"https?://t\.me/c/(\d+)/(\d+)", link)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None


def parse_channel_link(link: str) -> tuple:
    """Parses link for channel / invite."""
    link = link.strip().lstrip("@")
    m = re.match(r"https?://t\.me/\+([a-zA-Z0-9_\-]+)", link)
    if m:
        return "hash", m.group(1)
    m = re.match(r"https?://t\.me/joinchat/([a-zA-Z0-9_\-]+)", link)
    if m:
        return "hash", m.group(1)
    m = re.match(r"https?://t\.me/([a-zA-Z_][a-zA-Z0-9_]{3,})", link)
    if m:
        return "username", m.group(1)
    if link:
        return "raw", link
    return "unknown", None


def parse_target_link(link: str) -> dict:
    """Parses target link (post/username)."""
    link = link.strip()
    m = re.match(r"https?://t\.me/([a-zA-Z_][a-zA-Z0-9_]{3,})/(\d+)", link)
    if m:
        return {"type": "post", "channel": m.group(1), "post_id": int(m.group(2))}
    m = re.match(r"https?://t\.me/c/(\d+)/(\d+)", link)
    if m:
        return {"type": "private_post", "channel": int(m.group(1)), "post_id": int(m.group(2))}
    m = re.match(r"https?://t\.me/([a-zA-Z_][a-zA-Z0-9_]{3,})/?$", link)
    if m:
        return {"type": "username", "channel": m.group(1), "post_id": None}
    clean = link.lstrip("@")
    if clean and re.match(r"^[a-zA-Z_][a-zA-Z0-9_]{3,}$", clean):
        return {"type": "username", "channel": clean, "post_id": None}
    return {"type": "unknown", "channel": None, "post_id": None}


def normalize_phone(phone: str) -> str:
    """normalizes phone number"""
    phone = re.sub(r"[\s\(\)\-]", "", phone.strip())
    if not phone.startswith("+"):
        phone = "+" + phone
    return phone


def is_phone_number(value: str) -> bool:
    """Checks is string a phone number"""
    cleaned = re.sub(r"[\s\(\)\-\+]", "", value.strip())
    return bool(re.match(r"^\d{7,15}$", cleaned))