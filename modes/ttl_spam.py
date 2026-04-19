"""
Mode 9: TTL spam in normal chat
"""

import os
import random
import asyncio

from telethon.tl.functions.messages import SetHistoryTTLRequest
from telethon.errors import FloodWaitError, UserPrivacyRestrictedError, PeerFloodError

from config import CHAT_TTL_OPTIONS, CHAT_TTL_CYCLE
from utils.client import create_client, get_session_name
from ui import (
    print_header, print_info, print_success, print_error,
    print_warning, print_action, print_stats_box, print_round,
    print_choices, print_config_box, print_description_box,
    ask_confirm, ask_input, print_interrupted, print_fire,
)
from utils.target import ask_target, resolve_target, resolve_target_with_session
from utils.sessions import find_working_session
from utils.delays import get_delay, ask_delay
from utils.dialog import delete_dialog_for_sender


async def set_chat_ttl_single(
    session_path, target_info, ttl_seconds, ttl_label,
    delete_after=False, delete_delay=0,
) -> bool:
    # Sets TTL in normal mode
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

        peer = await client.get_input_entity(entity)
        print_action(f"{name} ({info}) → {display}: TTL = {ttl_label}")

        await client(SetHistoryTTLRequest(peer=peer, period=ttl_seconds))
        print_success(f"{name} — TTL установлен: {ttl_label}")

        if delete_after:
            if delete_delay > 0:
                await asyncio.sleep(delete_delay)
            await delete_dialog_for_sender(client, entity, name)
        return True

    except FloodWaitError as e:
        print_warning(f"{name} — FloodWait {e.seconds} сек.")
    except UserPrivacyRestrictedError:
        print_warning(f"{name} — приватность запрещает.")
    except PeerFloodError:
        print_warning(f"{name} — PeerFlood.")
    except Exception as e:
        print_error(f"{name} — {type(e).__name__}: {e}")
    finally:
        await client.disconnect()
    return False


async def mode_ttl_spam(sessions):
    #The main function of TTL spam
    print_header("⏱️  TTL-СПАМ (ОБЫЧНЫЙ ЧАТ)")

    print_description_box(
        "• Каждый аккаунт меняет время автоудаления в диалоге\n"
        "• Получатель видит системное сообщение:\n"
        "  [italic]«User установил таймер автоудаления сообщений: X»[/]\n"
        "• При циклической смене — [bold]много уведомлений[/] подряд\n\n"
        "[cyan]Доступные значения TTL (ограничение Telegram):[/]\n"
        "  • Выкл  • 1 день  • 7 дней  • 31 день",
        title="⚠️  КАК ЭТО РАБОТАЕТ",
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

    print_choices([
        ("1", "Фиксированное значение (один TTL)"),
        ("2", "Циклическая смена (макс. эффект! 🔥)"),
        ("3", "Случайное значение каждый раз"),
    ], "Режим TTL:")
    ttl_mode = ask_input("Выбор", "2")

    fixed_ttl = None
    fixed_label = ""

    if ttl_mode == "1":
        items = [(k, label) for k, (label, _) in CHAT_TTL_OPTIONS.items()]
        print_choices(items, "Выберите TTL:")
        choice = ask_input("Выбор")
        if choice not in CHAT_TTL_OPTIONS:
            print_error("Неверный выбор.")
            return
        fixed_label, fixed_ttl = CHAT_TTL_OPTIONS[choice]
    elif ttl_mode == "2":
        print_info("Будет циклически меняться:")
        for ttl, label in CHAT_TTL_CYCLE:
            print_fire(f"→ {label}")
    elif ttl_mode == "3":
        print_info("Каждый раз случайное значение из доступных.")
    else:
        ttl_mode = "1"
        fixed_label, fixed_ttl = CHAT_TTL_OPTIONS["1"]

    delete_after = ask_input("Удалять диалог у себя? (да/нет)", "нет").lower() in ("да", "yes", "y", "д")
    delete_delay = 0.0
    if delete_after:
        dd = ask_input("Пауза перед удалением, сек", "1")
        delete_delay = float(dd) if dd else 1.0

    min_d, max_d = ask_delay()

    print_choices([("1", "Один круг"), ("2", "Цикл (Ctrl+C)")], "Режим:")
    send_mode = ask_input("Выбор", "1")

    ttl_display = fixed_label if ttl_mode == "1" else ("Циклическая" if ttl_mode == "2" else "Случайный")
    print_config_box({
        "Получатель": target_info["display"],
        "Тип": target_info["type"],
        "TTL": ttl_display,
        "Аккаунтов": str(len(sessions)),
        "Удаление": "Да" if delete_after else "Нет",
    })

    if not ask_confirm("Начать TTL-спам?"):
        return

    total_ok = total_fail = round_num = cycle_idx = 0
    try:
        while True:
            round_num += 1
            print_round(round_num)
            for i, sess in enumerate(sessions):
                if ttl_mode == "1":
                    ttl = fixed_ttl
                    label = fixed_label
                elif ttl_mode == "2":
                    ttl, label = CHAT_TTL_CYCLE[cycle_idx % len(CHAT_TTL_CYCLE)]
                    cycle_idx += 1
                else:
                    choice = random.choice(list(CHAT_TTL_OPTIONS.values()))
                    label, ttl = choice

                ok = await set_chat_ttl_single(
                    sess, target_info, ttl, label,
                    delete_after, delete_delay,
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
        "✅ TTL изменений": total_ok,
        "❌ Ошибок": total_fail,
    }, "РЕЗУЛЬТАТЫ TTL-СПАМА")