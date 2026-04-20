"""Parsing links, usernames, phone numbers."""

import re


def parse_post_link(link: str) -> tuple:
    m = re.match(r"https?://t\.me/([a-zA-Z_][a-zA-Z0-9_]{3,})/(\d+)", link)
    if m:
        return m.group(1), int(m.group(2))
    m = re.match(r"https?://t\.me/c/(\d+)/(\d+)", link)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None


def parse_channel_link(link: str) -> tuple:
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
    phone = re.sub(r"[\s\(\)\-]", "", phone.strip())
    if not phone.startswith("+"):
        phone = "+" + phone
    return phone


def is_phone_number(value: str) -> bool:
    cleaned = re.sub(r"[\s\(\)\-\+]", "", value.strip())
    return bool(re.match(r"^\d{7,15}$", cleaned))


def format_phone(phone) -> str:
    if not phone:
        return "—"
    phone = str(phone)
    if not phone.startswith("+"):
        phone = "+" + phone
    return phone


def format_seconds(sec: int) -> str:
    if sec < 60:
        return f"{sec}с"
    elif sec < 3600:
        return f"{sec // 60}м {sec % 60}с"
    else:
        h = sec // 3600
        m = (sec % 3600) // 60
        return f"{h}ч {m}м"


def parse_selection(input_str: str, total_count: int) -> list | None:
    """Parses the user's choice: '1,3,5' or empty = all."""
    input_str = input_str.strip()
    if not input_str:
        return list(range(total_count))
    indices = []
    parts = input_str.replace(" ", "").split(",")
    for part in parts:
        try:
            num = int(part)
            if num < 1 or num > total_count:
                return None
            indices.append(num - 1)
        except ValueError:
            return None
    return list(dict.fromkeys(indices))