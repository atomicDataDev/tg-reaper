"""
Recipient resolve by username or moblie phone
"""

import re
import random
from telethon import TelegramClient
from telethon.tl.functions.contacts import (
    ImportContactsRequest,
    DeleteContactsRequest,
    ResolvePhoneRequest,
)
from telethon.tl.types import InputPhoneContact
from telethon.errors import FloodWaitError

from config import API_ID, API_HASH
from ui import print_success, print_error, print_info, print_dim, print_trash, ask_target_input
from utils.parsers import normalize_phone, is_phone_number


def ask_target(prompt: str = None) -> dict:
    """Интерактивный ввод цели."""
    raw = ask_target_input(prompt)

    if not raw:
        return {"type": "invalid", "value": None, "display": ""}

    m = re.match(r"https?://t\.me/([a-zA-Z_][a-zA-Z0-9_]{3,})/?$", raw)
    if m:
        username = m.group(1)
        return {"type": "username", "value": username, "display": f"@{username}"}

    cleaned = raw.lstrip("@")

    if is_phone_number(cleaned):
        phone = normalize_phone(cleaned)
        return {"type": "phone", "value": phone, "display": phone}

    username = cleaned
    if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]{3,}$", username):
        return {"type": "username", "value": username, "display": f"@{username}"}

    if username:
        return {"type": "username", "value": username, "display": f"@{username}"}

    return {"type": "invalid", "value": None, "display": ""}


async def resolve_target(
    client: TelegramClient,
    target_info: dict,
    session_name: str = "",
    add_contact: bool = True,
    remove_contact_after: bool = True,
) -> tuple:
    """Резолвит цель в entity."""
    prefix = f"[{session_name}] " if session_name else ""

    if target_info["type"] == "username":
        try:
            entity = await client.get_entity(target_info["value"])
            name = getattr(entity, "first_name", "") or ""
            if getattr(entity, "last_name", ""):
                name += f" {entity.last_name}"
            name = name.strip() or target_info["display"]
            return entity, name
        except Exception as e:
            return None, f"{type(e).__name__}: {e}"

    elif target_info["type"] == "phone":
        phone = target_info["value"]

        try:
            result = await client(ResolvePhoneRequest(phone=phone))
            if result and result.users:
                user = result.users[0]
                entity = await client.get_entity(user.id)
                name = f"{user.first_name or ''} {user.last_name or ''}".strip() or phone
                print_success(f"{prefix}Найден через ResolvePhone: {name}")
                return entity, name
        except AttributeError:
            pass
        except Exception as e:
            if "PHONE_NOT_OCCUPIED" in str(e):
                return None, f"Номер {phone} не зарегистрирован в Telegram"
            print_dim(f"{prefix}ResolvePhone: {type(e).__name__}, другой метод...")

        try:
            entity = await client.get_entity(phone)
            name = getattr(entity, "first_name", "") or ""
            if getattr(entity, "last_name", ""):
                name += f" {entity.last_name}"
            name = name.strip() or phone
            print_success(f"{prefix}Найден напрямую: {name}")
            return entity, name
        except Exception:
            pass

        if add_contact:
            contact_id = None
            try:
                random_id = random.randint(100000, 999999)
                contact = InputPhoneContact(
                    client_id=random_id,
                    phone=phone,
                    first_name="Temp",
                    last_name=f"Contact_{random_id}",
                )
                result = await client(ImportContactsRequest(contacts=[contact]))

                if result.users:
                    user = result.users[0]
                    contact_id = user.id
                    entity = await client.get_entity(user.id)
                    name = f"{user.first_name or ''} {user.last_name or ''}".strip() or phone
                    print_success(f"{prefix}Найден через контакты: {name}")

                    if remove_contact_after and contact_id:
                        try:
                            input_user = await client.get_input_entity(contact_id)
                            await client(DeleteContactsRequest(id=[input_user]))
                            print_trash(f"{prefix}Временный контакт удалён")
                        except Exception:
                            pass
                    return entity, name
                else:
                    if result.retry_contacts:
                        return None, f"Номер {phone} не найден (retry_contacts)"
                    return None, f"Номер {phone} не зарегистрирован или скрыт"
            except FloodWaitError as e:
                return None, f"FloodWait {e.seconds} сек при добавлении контакта"
            except Exception as e:
                return None, f"Ошибка импорта контакта: {type(e).__name__}: {e}"

        return None, f"Не удалось найти пользователя по номеру {phone}"
    else:
        return None, "Некорректный формат получателя"


async def resolve_target_with_session(session_path: str, target_info: dict) -> tuple:
    """Резолвит цель через указанную сессию."""
    import os
    client = TelegramClient(session_path, API_ID, API_HASH)
    name = os.path.basename(session_path)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            return None, "Не авторизован"
        entity, display = await resolve_target(client, target_info, name)
        if entity:
            return entity.id, display
        return None, display
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"
    finally:
        await client.disconnect()