"""Mode 3 (main): Subscribe to a channel."""

from core.client_factory import create_client, get_session_name
from ui import (
    print_header, print_error, print_action,
    print_stats_box, ask_confirm, ask_input, print_interrupted,
)
from utils.parsers import parse_channel_link
from utils.delays import get_delay, ask_delay
from modes.comments import join_channel, join_channel_by_hash


async def subscribe_account(session_path, link_type, link_value):
    client = create_client(session_path)
    name = get_session_name(session_path)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print_error(f"{name} — не авторизован.")
            return False
        me = await client.get_me()
        info = me.username or me.phone or f"id:{me.id}"
        print_action(f"{name} ({info}) подписывается...")
        if link_type == "hash":
            return await join_channel_by_hash(
                client, link_value, name
            )
        entity = await client.get_entity(link_value)
        return await join_channel(client, entity, name)
    except Exception as e:
        print_error(f"{name} — {type(e).__name__}: {e}")
        return False
    finally:
        await client.disconnect()


async def mode_subscribe(sessions):
    print_header("📢  ПОДПИСКА НА КАНАЛ")

    raw_link = ask_input("Канал (username / ссылка)")
    if not raw_link:
        print_error("Пусто.")
        return
    lt, lv = parse_channel_link(raw_link)
    if not lv:
        print_error("Некорректно.")
        return

    min_d, max_d = ask_delay()
    if not ask_confirm("Начать подписку?"):
        return

    total_ok = total_fail = 0
    try:
        for i, sess in enumerate(sessions):
            ok = await subscribe_account(sess, lt, lv)
            total_ok += ok
            total_fail += not ok
            if i < len(sessions) - 1:
                await get_delay(min_d, max_d)
    except KeyboardInterrupt:
        print_interrupted()

    print_stats_box({
        "✅ Подписалось": total_ok,
        "❌ Ошибок": total_fail,
    }, "РЕЗУЛЬТАТЫ ПОДПИСКИ")