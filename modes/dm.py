"""
Mode 1: Private message send
"""

import os
import random
import asyncio

from telethon.errors import FloodWaitError, PeerFloodError, UserPrivacyRestrictedError

from config import DM_MESSAGES, MESSAGE_MODE
from utils.client import create_client, get_session_name
from ui import (
    print_header, print_info, print_success, print_error,
    print_warning, print_action, print_dim, print_stats_box,
    print_round, print_config_box, ask_confirm, ask_input,
    print_choices, print_interrupted,
)
from utils.target import ask_target, resolve_target, resolve_target_with_session
from utils.sessions import find_working_session
from utils.delays import get_delay, ask_delay
from utils.dialog import delete_dialog_for_sender


async def send_dm(session_path, target_info, message, delete_after=False, delete_delay=0):
    # Sends a message from a single account
    client = create_client(session_path)
    name = get_session_name(session_path)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print_error(f"{name} — не авторизован.")
            return False
        me = await client.get_me()
        info = me.username or me.phone or f"id:{me.id}"

        entity, display = await resolve_target(client, target_info, name)
        if not entity:
            print_error(f"{name} — получатель не найден: {display}")
            return False

        print_action(f"{name} ({info}) → {display}")
        await client.send_message(entity, message)
        print_success(f"{name} — отправлено!")

        if delete_after:
            if delete_delay > 0:
                await asyncio.sleep(delete_delay)
            await delete_dialog_for_sender(client, entity, name)
        return True
    except FloodWaitError as e:
        print_warning(f"{name} — FloodWait {e.seconds} сек.")
    except PeerFloodError:
        print_warning(f"{name} — PeerFlood, лимит.")
    except UserPrivacyRestrictedError:
        print_warning(f"{name} — приватность пользователя.")
    except Exception as e:
        print_error(f"{name} — {type(e).__name__}: {e}")
    finally:
        await client.disconnect()
    return False


async def mode_dm(sessions):
    # Main function of private message mode
    print_header("💬  ЛИЧНЫЕ СООБЩЕНИЯ")

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

    min_d, max_d = ask_delay()

    delete_after = ask_input("Удалять диалог после? (да/нет)", "нет").lower() in ("да", "yes", "y", "д")
    delete_delay = 0.0
    if delete_after:
        dd = ask_input("Пауза перед удалением, сек", "2")
        delete_delay = float(dd) if dd else 2.0

    print_choices([("1", "Один круг"), ("2", "Цикл (Ctrl+C)")], "Режим отправки:")
    send_mode = ask_input("Выбор", "1")

    print_config_box({
        "Получатель": target_info["display"],
        "Тип": target_info["type"],
        "Аккаунтов": str(len(sessions)),
        "Удаление": "Да" if delete_after else "Нет",
    })

    if not ask_confirm("Начать рассылку?"):
        return

    msg_idx = total_ok = total_fail = round_num = 0
    try:
        while True:
            round_num += 1
            print_round(round_num)
            for i, sess in enumerate(sessions):
                msg = (
                    random.choice(DM_MESSAGES) if MESSAGE_MODE == "random"
                    else DM_MESSAGES[msg_idx % len(DM_MESSAGES)]
                )
                msg_idx += 1
                print_dim(f'Сообщение: "{msg[:60]}"')
                ok = await send_dm(sess, target_info, msg, delete_after, delete_delay)
                total_ok += ok
                total_fail += not ok
                if not (i == len(sessions) - 1 and send_mode != "2"):
                    await get_delay(min_d, max_d)
            if send_mode != "2":
                break
    except KeyboardInterrupt:
        print_interrupted()

    print_stats_box({
        "✅ Отправлено": total_ok,
        "❌ Ошибок": total_fail,
    }, "РЕЗУЛЬТАТЫ РАССЫЛКИ")