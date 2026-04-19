"""
Mode 5: User Reports (compatability with various Telethon versions).
"""

import os

from telethon.tl.functions.messages import ReportRequest
from telethon.tl.functions.account import ReportPeerRequest

from config import REPORT_REASONS
from utils.client import create_client, get_session_name
from ui import (
    print_header, print_info, print_success, print_error,
    print_action, print_stats_box, print_round, print_choices,
    ask_confirm, ask_input, print_interrupted,
)
from utils.target import ask_target, resolve_target
from utils.parsers import parse_target_link
from utils.sessions import find_working_session
from utils.delays import get_delay, ask_delay


def ask_report_reason():
    # Resolves report reason
    items = [(k, label) for k, (label, _) in REPORT_REASONS.items()]
    print_choices(items, "Причина жалобы:")
    choice = ask_input("Номер")
    if choice not in REPORT_REASONS:
        return None, None, None
    rn, rc = REPORT_REASONS[choice]
    comment = ask_input("Комментарий (Enter = пропустить)")
    return rc(), rn, comment


async def _do_report_messages(client, peer, msg_ids, reason_obj, comment, name):
    # Report on message
    for kwargs in [
        dict(peer=peer, id=msg_ids, option=reason_obj, message=comment or ""),
        dict(peer=peer, id=msg_ids, reason=reason_obj, message=comment or ""),
        dict(peer=peer, id=msg_ids, reason=reason_obj),
    ]:
        try:
            await client(ReportRequest(**kwargs))
            return True
        except TypeError:
            continue

    try:
        await client(ReportRequest(peer, msg_ids, reason_obj, comment or ""))
        return True
    except TypeError:
        pass

    try:
        await client(ReportRequest(peer=peer, id=msg_ids))
        return True
    except Exception as e:
        print_error(f"{name} — ReportRequest failed: {type(e).__name__}: {e}")
        return False


async def _do_report_peer(client, peer, reason_obj, comment, name):
    # Report on profile
    for kwargs in [
        dict(peer=peer, reason=reason_obj, message=comment or ""),
        dict(peer=peer, reason=reason_obj),
    ]:
        try:
            await client(ReportPeerRequest(**kwargs))
            return True
        except TypeError:
            continue

    try:
        await client(ReportPeerRequest(peer, reason_obj, comment or ""))
        return True
    except Exception as e:
        print_error(f"{name} — ReportPeerRequest failed: {type(e).__name__}: {e}")
        return False


async def report_peer_account(session_path, target_info, reason_obj, comment, msg_ids=None):
    # Sends report from a single account
    client = create_client(session_path)
    name = get_session_name(session_path)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print_error(f"{name} — не авторизован.")
            return False
        me = await client.get_me()
        info = me.username or me.phone or f"id:{me.id}"

        if isinstance(target_info, dict) and "type" in target_info:
            entity, display = await resolve_target(client, target_info, name)
            if not entity:
                print_error(f"{name} — цель не найдена: {display}")
                return False
        else:
            entity = await client.get_entity(target_info)

        peer = await client.get_input_entity(entity)

        if msg_ids:
            print_action(f"{name} ({info}) жалоба на сообщения {msg_ids}...")
            ok = await _do_report_messages(client, peer, msg_ids, reason_obj, comment, name)
        else:
            print_action(f"{name} ({info}) жалоба на профиль...")
            ok = await _do_report_peer(client, peer, reason_obj, comment, name)

        if ok:
            print_success(f"{name} — жалоба отправлена!")
        return ok
    except Exception as e:
        print_error(f"{name} — {type(e).__name__}: {e}")
        return False
    finally:
        await client.disconnect()


async def mode_report(sessions):
    # Main function of report mode
    print_header("🚨  ЖАЛОБЫ")

    print_choices([
        ("1", "На профиль (username / телефон)"),
        ("2", "На пост"),
        ("3", "На несколько постов"),
    ], "Тип жалобы:")
    variant = ask_input("Выбор", "1")

    target_info = None
    msg_ids = None

    if variant == "1":
        target_info = ask_target("Цель жалобы")
        if target_info["type"] == "invalid":
            print_error("Некорректно.")
            return
        print_info(f"Цель: {target_info['display']}")

    elif variant == "2":
        link = ask_input("Ссылка на пост")
        p = parse_target_link(link)
        if p["type"] not in ("post", "private_post"):
            print_error("Некорректно.")
            return
        target_info = {"type": "username", "value": p["channel"], "display": str(p["channel"])}
        msg_ids = [p["post_id"]]

    elif variant == "3":
        raw = ask_input("Username канала (без @)").lstrip("@")
        if not raw:
            print_error("Пусто.")
            return
        target_info = {"type": "username", "value": raw, "display": f"@{raw}"}
        cnt = ask_input("Кол-во постов", "10")
        count = int(cnt) if cnt else 10

        ss = await find_working_session(sessions)
        if not ss:
            print_error("Нет рабочих сессий.")
            return

        client = create_client(ss, receive_updates=False)
        scanned = []
        try:
            await client.connect()
            ch = await client.get_entity(raw)
            async for msg in client.iter_messages(ch, limit=count):
                scanned.append(msg.id)
        except Exception as e:
            print_error(str(e))
            return
        finally:
            await client.disconnect()
        if not scanned:
            print_error("Постов нет.")
            return
        msg_ids = scanned
    else:
        return

    reason_obj, reason_name, comment = ask_report_reason()
    if not reason_obj:
        return

    min_d, max_d = ask_delay()

    print_choices([("1", "Один круг"), ("2", "Цикл (Ctrl+C)")], "Режим:")
    send_mode = ask_input("Выбор", "1")

    if not ask_confirm("Начать отправку жалоб?"):
        return

    total_ok = total_fail = round_num = 0
    try:
        while True:
            round_num += 1
            print_round(round_num)
            for i, sess in enumerate(sessions):
                ok = await report_peer_account(sess, target_info, reason_obj, comment, msg_ids)
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
        "✅ Жалоб": total_ok,
        "❌ Ошибок": total_fail,
    }, "РЕЗУЛЬТАТЫ ЖАЛОБ")