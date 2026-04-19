"""
Mode 6: Calls / Calls+messages
"""

import os
import random
import hashlib
import asyncio

from telethon import events
from telethon.tl.functions.messages import GetDhConfigRequest
from telethon.tl.functions.phone import RequestCallRequest, DiscardCallRequest
from telethon.tl.types import (
    PhoneCallProtocol, PhoneCallAccepted, PhoneCallDiscarded,
    PhoneCallDiscardReasonHangup, InputPhoneCall, UpdatePhoneCall,
)
from telethon.errors import FloodWaitError, UserPrivacyRestrictedError, PeerFloodError

from config import DM_MESSAGES, MESSAGE_MODE
from utils.client import create_client, get_session_name
from ui import (
    print_header, print_info, print_success, print_error,
    print_warning, print_action, print_dim, print_call,
    print_stats_box, print_round, print_choices,
    print_config_box, ask_confirm, ask_input, print_interrupted,
)
from utils.target import ask_target, resolve_target, resolve_target_with_session
from utils.sessions import find_working_session
from utils.delays import get_delay, ask_delay
from utils.dialog import delete_dialog_for_sender


async def make_single_call(client, target_user, ring_seconds, name) -> bool:
    # Makes one call
    try:
        dh_config = await client(GetDhConfigRequest(version=0, random_length=256))
        if not hasattr(dh_config, "p"):
            print_error(f"{name} — нет DH конфигурации.")
            return False

        p = int.from_bytes(dh_config.p, "big")
        g = dh_config.g
        a = int.from_bytes(os.urandom(256), "big")
        g_a_int = pow(g, a, p)
        g_a_len = (p.bit_length() + 7) // 8
        g_a_bytes = g_a_int.to_bytes(g_a_len, "big")
        g_a_hash = hashlib.sha256(g_a_bytes).digest()

        try:
            protocol = PhoneCallProtocol(
                min_layer=92, max_layer=92,
                udp_p2p=True, udp_reflector=True,
                library_versions=["5.0.0"],
            )
        except TypeError:
            protocol = PhoneCallProtocol(
                min_layer=92, max_layer=92,
                udp_p2p=True, udp_reflector=True,
            )

        user_entity = await client.get_input_entity(target_user)
        try:
            result = await client(RequestCallRequest(
                user_id=user_entity,
                random_id=random.randint(0, 0x7FFFFFFF),
                g_a_hash=g_a_hash,
                protocol=protocol,
                video=False,
            ))
        except TypeError:
            result = await client(RequestCallRequest(
                user_id=user_entity,
                random_id=random.randint(0, 0x7FFFFFFF),
                g_a_hash=g_a_hash,
                protocol=protocol,
            ))

        call = result.phone_call
        call_id = call.id
        call_peer = InputPhoneCall(id=call.id, access_hash=call.access_hash)

        print_call(f"{name} — звонок идёт (макс. {ring_seconds} сек)...")

        call_accepted = asyncio.Event()
        call_ended = asyncio.Event()

        async def _on_call(update):
            if isinstance(update, UpdatePhoneCall):
                pc = update.phone_call
                if hasattr(pc, "id") and pc.id == call_id:
                    if isinstance(pc, PhoneCallAccepted):
                        call_accepted.set()
                    elif isinstance(pc, PhoneCallDiscarded):
                        call_ended.set()

        client.add_event_handler(_on_call, events.Raw)
        try:
            elapsed = 0.0
            step = 0.25
            while elapsed < ring_seconds:
                await asyncio.sleep(step)
                elapsed += step
                if call_accepted.is_set():
                    print_call(f"{name} — поднял трубку → сброс!")
                    break
                if call_ended.is_set():
                    print_dim(f"{name} — отклонён собеседником.")
                    return True
            else:
                print_dim(f"{name} — таймаут {ring_seconds}с → сброс.")

            try:
                await client(DiscardCallRequest(
                    peer=call_peer, duration=0,
                    reason=PhoneCallDiscardReasonHangup(),
                    connection_id=0,
                ))
            except Exception:
                pass

            print_success(f"{name} — звонок сброшен.")
            return True
        finally:
            client.remove_event_handler(_on_call)

    except FloodWaitError as e:
        print_warning(f"{name} — FloodWait {e.seconds} сек.")
    except UserPrivacyRestrictedError:
        print_warning(f"{name} — звонки запрещены.")
    except PeerFloodError:
        print_warning(f"{name} — PeerFlood.")
    except Exception as e:
        print_error(f"{name} — ошибка звонка: {type(e).__name__}: {e}")
    return False


async def do_call_session(session_path, target_info, ring_seconds, delete_after, delete_delay) -> bool:
    # Call from a single session
    client = create_client(session_path)
    name = get_session_name(session_path)
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

        ok = await make_single_call(client, entity, ring_seconds, name)
        if ok and delete_after:
            if delete_delay > 0:
                await asyncio.sleep(delete_delay)
            await delete_dialog_for_sender(client, entity, name)
        return ok
    except Exception as e:
        print_error(f"{name} — {type(e).__name__}: {e}")
        return False
    finally:
        await client.disconnect()


async def do_combo_session(
    session_path, target_info, message, ring_seconds,
    combo_order, delete_after, delete_delay,
) -> bool:
    # Call + message mode
    client = create_client(session_path)
    name = get_session_name(session_path)
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

        ok_call = ok_msg = False

        async def _send():
            nonlocal ok_msg
            try:
                print_dim(f'{name} — 💬 "{message[:50]}"')
                await client.send_message(entity, message)
                print_success(f"{name} — сообщение отправлено!")
                ok_msg = True
            except Exception as e:
                print_error(f"{name} — ошибка: {type(e).__name__}: {e}")

        if combo_order == "call_first":
            ok_call = await make_single_call(client, entity, ring_seconds, name)
            await asyncio.sleep(0.5)
            await _send()
        else:
            await _send()
            await asyncio.sleep(0.5)
            ok_call = await make_single_call(client, entity, ring_seconds, name)

        success = ok_call or ok_msg
        if success and delete_after:
            if delete_delay > 0:
                await asyncio.sleep(delete_delay)
            await delete_dialog_for_sender(client, entity, name)
        return success
    except Exception as e:
        print_error(f"{name} — {type(e).__name__}: {e}")
        return False
    finally:
        await client.disconnect()


async def mode_calls_combo(sessions):
    # Main function of Calls / combo mode
    print_header("📞  ЗВОНКИ / КОМБО")

    print_choices([
        ("1", "📞 Только звонки"),
        ("2", "📞💬 Звонок → сообщение"),
        ("3", "💬📞 Сообщение → звонок"),
    ], "Действие:")
    action = ask_input("Выбор", "1")
    if action not in ("1", "2", "3"):
        print_error("Неверный выбор.")
        return

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

    rs = ask_input("Время дозвона, сек", "5")
    ring_seconds = float(rs) if rs else 5.0

    delete_after = ask_input("Удалять диалог после? (да/нет)", "нет").lower() in ("да", "yes", "y", "д")
    delete_delay = 0.0
    if delete_after:
        dd = ask_input("Пауза перед удалением, сек", "1")
        delete_delay = float(dd) if dd else 1.0

    min_d, max_d = ask_delay()

    print_choices([("1", "Один круг"), ("2", "Цикл (Ctrl+C)")], "Режим:")
    send_mode = ask_input("Выбор", "1")

    if not ask_confirm("Начать?"):
        return

    msg_idx = total_ok = total_fail = round_num = 0
    try:
        while True:
            round_num += 1
            print_round(round_num)
            for i, sess in enumerate(sessions):
                if action == "1":
                    ok = await do_call_session(sess, target_info, ring_seconds, delete_after, delete_delay)
                else:
                    msg = (
                        random.choice(DM_MESSAGES) if MESSAGE_MODE == "random"
                        else DM_MESSAGES[msg_idx % len(DM_MESSAGES)]
                    )
                    msg_idx += 1
                    order = "call_first" if action == "2" else "msg_first"
                    ok = await do_combo_session(
                        sess, target_info, msg, ring_seconds,
                        order, delete_after, delete_delay,
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
        "✅ Успешных": total_ok,
        "❌ Ошибок": total_fail,
    }, "РЕЗУЛЬТАТЫ ЗВОНКОВ")