"""
Mode 2: Comments in channel
"""

import os
import random
import asyncio

from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.errors import (
    FloodWaitError, UserAlreadyParticipantError, ChannelPrivateError,
    MsgIdInvalidError, ChatWriteForbiddenError, SlowModeWaitError,
    PeerFloodError, InviteHashExpiredError, InviteHashInvalidError,
)

from config import COMMENT_MESSAGES, MESSAGE_MODE
from utils.client import create_client, get_session_name
from ui import (
    print_header, print_info, print_success, print_error,
    print_warning, print_action, print_dim, print_stats_box,
    print_round, ask_confirm, ask_input, print_choices,
    print_interrupted, print_fire,
)
from utils.parsers import parse_post_link
from utils.sessions import find_working_session
from utils.delays import get_delay, ask_delay


async def join_channel(client, channel, name):
    # Subscribes on channel
    try:
        await client(JoinChannelRequest(channel))
        print_success(f"{name} — подписался.")
        return True
    except UserAlreadyParticipantError:
        print_dim(f"{name} — уже подписан.")
        return True
    except ChannelPrivateError:
        print_error(f"{name} — канал приватный.")
        return False
    except FloodWaitError as e:
        print_warning(f"{name} — FloodWait {e.seconds} сек.")
        await asyncio.sleep(e.seconds)
        return await join_channel(client, channel, name)
    except Exception as e:
        print_error(f"{name} — {type(e).__name__}: {e}")
        return False


async def join_channel_by_hash(client, invite_hash, name):
    # Subscribes by invite hash
    try:
        await client(ImportChatInviteRequest(invite_hash))
        print_success(f"{name} — подписался по инвайту.")
        return True
    except UserAlreadyParticipantError:
        print_dim(f"{name} — уже подписан.")
        return True
    except InviteHashExpiredError:
        print_error(f"{name} — инвайт истёк.")
        return False
    except InviteHashInvalidError:
        print_error(f"{name} — инвайт недействителен.")
        return False
    except FloodWaitError as e:
        await asyncio.sleep(e.seconds)
        return await join_channel_by_hash(client, invite_hash, name)
    except PeerFloodError:
        print_warning(f"{name} — PeerFlood.")
        return False
    except Exception as e:
        print_error(f"{name} — {type(e).__name__}: {e}")
        return False


async def comment_on_post(session_path, channel_entity, post_id, message, do_join=True):
    # Leaves a comment from a single account
    client = create_client(session_path)
    name = get_session_name(session_path)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print_error(f"{name} — не авторизован.")
            return False
        me = await client.get_me()
        info = me.username or me.phone or f"id:{me.id}"
        try:
            channel = await client.get_entity(channel_entity)
        except Exception as e:
            print_error(f"{name} — канал не найден: {e}")
            return False
        if do_join and not await join_channel(client, channel, name):
            return False
        print_action(f"{name} ({info}) → #{post_id}")
        await client.send_message(entity=channel, message=message, comment_to=post_id)
        print_success(f"{name} — комментарий оставлен!")
        return True
    except MsgIdInvalidError:
        print_error(f"{name} — пост не существует.")
    except ChatWriteForbiddenError:
        print_error(f"{name} — комментарии закрыты.")
    except SlowModeWaitError as e:
        print_warning(f"{name} — слоумод {e.seconds} сек.")
    except FloodWaitError as e:
        print_warning(f"{name} — FloodWait {e.seconds} сек.")
    except Exception as e:
        print_error(f"{name} — {type(e).__name__}: {e}")
    finally:
        await client.disconnect()
    return False


async def get_post_ids_with_comments(session_path, channel_entity, limit=100):
    # Scans posts with comments allowed
    client = create_client(session_path, receive_updates=False)
    post_ids = []
    try:
        await client.connect()
        if not await client.is_user_authorized():
            return []
        channel = await client.get_entity(channel_entity)
        print_info(f"Сканирую посты (до {limit})...")
        async for msg in client.iter_messages(channel, limit=limit):
            if msg.replies and msg.replies.comments:
                post_ids.append(msg.id)
                if msg.text and len(msg.text) > 50:
                    preview = msg.text[:50].replace("\n", " ") + "..."
                elif msg.text:
                    preview = msg.text[:50].replace("\n", " ")
                elif msg.media:
                    preview = "[медиа]"
                else:
                    preview = ""
                print_dim(f"#{msg.id} — {preview} (💬 {msg.replies.replies})")
        print_info(f"Постов с комментариями: {len(post_ids)}")
    except Exception as e:
        print_error(f"Ошибка: {type(e).__name__}: {e}")
    finally:
        await client.disconnect()
    return post_ids


async def mode_comments(sessions):
    # Main function of comment mode
    print_header("📝  КОММЕНТАРИИ В КАНАЛЕ")

    print_choices([("1", "Все посты канала"), ("2", "Конкретный пост")], "Режим:")
    variant = ask_input("Выбор", "1")

    channel_entity = None
    target_post_ids = []

    if variant == "2":
        link = ask_input("Ссылка на пост")
        ch, pid = parse_post_link(link)
        if not ch or not pid:
            print_error("Некорректная ссылка.")
            return
        channel_entity = ch
        target_post_ids = [pid]
    else:
        ci = ask_input("Username канала (без @)")
        ci = ci.lstrip("@")
        if not ci:
            print_error("Пусто.")
            return
        channel_entity = ci
        mp = ask_input("Макс. постов", "100")
        max_posts = int(mp) if mp else 100

        ss = await find_working_session(sessions)
        if not ss:
            print_error("Нет рабочих сессий.")
            return
        target_post_ids = await get_post_ids_with_comments(ss, channel_entity, max_posts)
        if not target_post_ids:
            print_error("Нет постов с комментариями.")
            return

    do_join = ask_input("Подписать аккаунты? (да/нет)", "да").lower() in ("да", "yes", "y", "д")
    min_d, max_d = ask_delay()

    post_delay = 0.0
    if len(target_post_ids) > 1:
        pd = ask_input("Пауза между постами, сек", "5")
        post_delay = float(pd) if pd else 5.0

    print_choices([("1", "Все аккаунты на каждый пост"), ("2", "Round-robin")], "Распределение:")
    dist_mode = ask_input("Выбор", "1")

    if not ask_confirm("Начать?"):
        return

    msg_idx = total_ok = total_fail = account_idx = 0
    try:
        for post_num, post_id in enumerate(target_post_ids, 1):
            print_fire(f"Пост #{post_id} ({post_num}/{len(target_post_ids)})")

            if dist_mode == "1":
                for i, sess in enumerate(sessions):
                    msg = (
                        random.choice(COMMENT_MESSAGES) if MESSAGE_MODE == "random"
                        else COMMENT_MESSAGES[msg_idx % len(COMMENT_MESSAGES)]
                    )
                    msg_idx += 1
                    ok = await comment_on_post(
                        sess, channel_entity, post_id, msg,
                        do_join=(do_join and post_num == 1),
                    )
                    total_ok += ok
                    total_fail += not ok
                    if i < len(sessions) - 1:
                        await get_delay(min_d, max_d)
            else:
                sess = sessions[account_idx % len(sessions)]
                msg = (
                    random.choice(COMMENT_MESSAGES) if MESSAGE_MODE == "random"
                    else COMMENT_MESSAGES[msg_idx % len(COMMENT_MESSAGES)]
                )
                msg_idx += 1
                account_idx += 1
                ok = await comment_on_post(sess, channel_entity, post_id, msg, do_join=do_join)
                total_ok += ok
                total_fail += not ok

            if post_num < len(target_post_ids) and post_delay > 0:
                await asyncio.sleep(post_delay)
    except KeyboardInterrupt:
        print_interrupted()

    print_stats_box({
        "✅ Комментариев": total_ok,
        "❌ Ошибок": total_fail,
    }, "РЕЗУЛЬТАТЫ КОММЕНТИРОВАНИЯ")