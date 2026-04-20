"""Resolve recipients by username or phone."""

import re
import random
from telethon import TelegramClient
from telethon.tl.functions.contacts import (
    ImportContactsRequest, DeleteContactsRequest,
    ResolvePhoneRequest,
)
from telethon.tl.types import InputPhoneContact
from telethon.errors import FloodWaitError

from core.client_factory import create_client
from ui import (
    print_success, print_error, print_dim,
    print_trash, ask_target_input,
)
from utils.parsers import normalize_phone, is_phone_number


def ask_target(prompt: str = None) -> dict:
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

    if cleaned:
        return {"type": "username", "value": cleaned, "display": f"@{cleaned}"}

    return {"type": "invalid", "value": None, "display": ""}


async def resolve_target(
    client: TelegramClient,
    target_info: dict,
    session_name: str = "",
    add_contact: bool = True,
    remove_contact_after: bool = True,
) -> tuple:
    prefix = f"[{session_name}] " if session_name else ""

    if target_info["type"] == "username":
        try:
            entity = await client.get_entity(target_info["value"])
            name = getattr(entity, "first_name", "") or ""
            if getattr(entity, "last_name", ""):
                name += f" {entity.last_name}"
            return entity, name.strip() or target_info["display"]
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
                return None, f"Номер {phone} не зарегистрирован"
            print_dim(f"{prefix}ResolvePhone: {type(e).__name__}")

        try:
            entity = await client.get_entity(phone)
            name = getattr(entity, "first_name", "") or ""
            if getattr(entity, "last_name", ""):
                name += f" {entity.last_name}"
            return entity, name.strip() or phone
        except Exception:
            pass

        if add_contact:
            try:
                random_id = random.randint(100000, 999999)
                contact = InputPhoneContact(
                    client_id=random_id, phone=phone,
                    first_name="Temp", last_name=f"Contact_{random_id}",
                )
                result = await client(ImportContactsRequest(contacts=[contact]))
                if result.users:
                    user = result.users[0]
                    entity = await client.get_entity(user.id)
                    name = f"{user.first_name or ''} {user.last_name or ''}".strip() or phone
                    if remove_contact_after:
                        try:
                            input_user = await client.get_input_entity(user.id)
                            await client(DeleteContactsRequest(id=[input_user]))
                            print_trash(f"{prefix}Временный контакт удалён")
                        except Exception:
                            pass
                    return entity, name
                return None, f"Номер {phone} не зарегистрирован или скрыт"
            except FloodWaitError as e:
                return None, f"FloodWait {e.seconds} сек"
            except Exception as e:
                return None, f"Ошибка: {type(e).__name__}: {e}"

        return None, f"Не удалось найти по номеру {phone}"
    return None, "Некорректный формат"


async def resolve_target_with_session(
    session_path: str, target_info: dict,
) -> tuple:
    import os
    client = create_client(session_path, receive_updates=False)
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