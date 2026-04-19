"""
Mode 7: Secret Chats (TTL-Spam).
"""

import os
import asyncio

from telethon.errors import FloodWaitError, UserPrivacyRestrictedError, PeerFloodError

from config import TTL_OPTIONS
from utils.client import create_client, get_session_name
from ui import (
    print_header, print_info, print_success, print_error,
    print_warning, print_action, print_wait, print_lock, print_timer,
    print_trash, print_dim, print_stats_box, print_round,
    print_choices, print_config_box, print_description_box,
    ask_confirm, ask_input, print_interrupted,
)
from utils.target import ask_target, resolve_target, resolve_target_with_session
from utils.sessions import find_working_session
from utils.delays import get_delay, ask_delay
from utils.dialog import delete_dialog_for_sender
from crypto.secret_chat import SecretChatManager

try:
    from telethon.errors import EncryptionDeclinedError, EncryptionAlreadyDeclinedError
except ImportError:
    EncryptionDeclinedError = Exception
    EncryptionAlreadyDeclinedError = Exception


async def create_secret_chat_session(
    session_path, target_info, ttl_seconds,
    delete_after, delete_delay, wait_timeout,
) -> bool:
    # Creates secret chat from a single account
    client = create_client(session_path)
    name = get_session_name(session_path)
    mgr = None
    chat_id = None

    try:
        await client.connect()
        if not await client.is_user_authorized():
            print_error(f"{name} — не авторизован.")
            return False

        me = await client.get_me()
        info = me.username or me.phone or f"id:{me.id}"
        print_action(f"{name} ({info})")

        entity, display = await resolve_target(client, target_info, name)
        if not entity:
            print_error(f"{name} — получатель не найден: {display}")
            return False

        mgr = SecretChatManager(client)
        print_lock(f"{name} — создаю секретный чат с {display}...")
        chat_data = await mgr.create(entity)
        if not chat_data:
            return False

        chat_id = chat_data["id"]
        print_wait(f"{name} — жду принятия (до {wait_timeout} сек)...")

        ok = await mgr.wait_accept(chat_id, timeout=wait_timeout)
        if not ok:
            state = chat_data.get("state", "?")
            if state == "discarded":
                print_error(f"{name} — чат отклонён.")
            else:
                print_error(f"{name} — таймаут (собеседник не онлайн?).")
            await mgr.discard(chat_id)
            return False

        print_success(f"{name} — секретный чат создан!")

        if ttl_seconds > 0:
            print_timer(f"{name} — устанавливаю TTL: {ttl_seconds} сек...")
            ttl_ok = await mgr.set_ttl(chat_id, ttl_seconds)
            if ttl_ok:
                print_success(f"{name} — уведомление TTL отправлено.")
        else:
            print_info(f"{name} — TTL: без автоудаления.")

        await mgr.send_typing(chat_id)
        await asyncio.sleep(1)

        if delete_after:
            if delete_delay > 0:
                print_wait(f"Пауза {delete_delay} сек перед закрытием...")
                await asyncio.sleep(delete_delay)
            print_trash(f"{name} — закрываю секретный чат...")
            await mgr.discard(chat_id)
            await delete_dialog_for_sender(client, entity, name)

        print_success(f"{name} — готово!")
        return True

    except (EncryptionDeclinedError, EncryptionAlreadyDeclinedError):
        print_error(f"{name} — чат отклонён собеседником.")
    except UserPrivacyRestrictedError:
        print_error(f"{name} — приватность запрещает.")
    except FloodWaitError as e:
        print_warning(f"{name} — FloodWait {e.seconds} сек.")
    except PeerFloodError:
        print_warning(f"{name} — PeerFlood.")
    except Exception as e:
        print_error(f"{name} — {type(e).__name__}: {e}")
    finally:
        if mgr and chat_id:
            state = mgr.chats.get(chat_id, {}).get("state")
            if state not in ("ready", "discarded", None):
                try:
                    await mgr.discard(chat_id)
                except Exception:
                    pass
        await client.disconnect()
    return False


async def mode_secret_chat(sessions):
    # Main secret chat function
    print_header("🔐  СЕКРЕТНЫЕ ЧАТЫ")

    print_description_box(
        "• Секретный чат требует [bold]ПРИНЯТИЯ[/] собеседником\n"
        "• Собеседник [bold]ПОЛУЧИТ[/] уведомление об изменении TTL\n"
        "• Закрытие чата = С ОБЕИХ сторон (протокол Telegram)\n"
        "• Обычный диалог удаляется только у отправителя",
        title="⚠️  ВАЖНО",
        style="yellow",
    )

    target_info = ask_target()
    if target_info["type"] == "invalid":
        print_error("Некорректный ввод.")
        return

    if target_info["type"] == "phone":
        print_info(f"Получатель: телефон {target_info['display']}")
        print_info("Проверяю доступность номера...")
        ss = await find_working_session(sessions)
        if ss:
            uid, display = await resolve_target_with_session(ss, target_info)
            if uid:
                print_success(f"Найден: {display} (ID: {uid})")
            else:
                print_warning(f"Предупреждение: {display}")
                if not ask_confirm("Продолжить всё равно?"):
                    return
    else:
        print_info(f"Получатель: {target_info['display']}")

    items = [(k, label) for k, (label, _) in TTL_OPTIONS.items()]
    print_choices(items, "Время автоудаления (TTL):")
    ttl_choice = ask_input("Выбор")
    if ttl_choice not in TTL_OPTIONS:
        print_error("Неверный выбор.")
        return
    ttl_label, ttl_seconds = TTL_OPTIONS[ttl_choice]

    ws = ask_input("Таймаут ожидания принятия, сек", "60")
    wait_timeout = float(ws) if ws else 60.0

    delete_after = ask_input(
        "Закрывать секретный чат после? (да/нет)", "да"
    ).lower() in ("да", "yes", "y", "д")
    delete_delay = 0.0
    if delete_after:
        dd = ask_input("Пауза перед закрытием, сек", "3")
        delete_delay = float(dd) if dd else 3.0

    min_d, max_d = ask_delay()

    print_choices([("1", "Один круг"), ("2", "Цикл (Ctrl+C)")], "Режим:")
    send_mode = ask_input("Выбор", "1")

    print_config_box({
        "Получатель": target_info["display"],
        "Тип": target_info["type"],
        "TTL": ttl_label,
        "Таймаут": f"{wait_timeout} сек",
        "Аккаунтов": str(len(sessions)),
        "Закрытие": "Да" if delete_after else "Нет",
    })

    if not ask_confirm("Начать?"):
        return

    total_ok = total_fail = round_num = 0
    try:
        while True:
            round_num += 1
            print_round(round_num)
            for i, sess in enumerate(sessions):
                ok = await create_secret_chat_session(
                    sess, target_info, ttl_seconds,
                    delete_after, delete_delay, wait_timeout,
                )
                total_ok += ok
                total_fail += not ok
                if i < len(sessions) - 1:
                    await get_delay(min_d, max_d)
            if send_mode != "2":
                break
            await get_delay(min_d, max_d)
    except KeyboardInterrupt:
        print_interrupted()

    print_stats_box({
        "✅ Секретных чатов": total_ok,
        "❌ Ошибок": total_fail,
    }, "РЕЗУЛЬТАТЫ СЕКРЕТНЫХ ЧАТОВ")