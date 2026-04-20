"""TG REAPER - Main program (attack / spam).
Run: python main.py"""

import asyncio

from ui import (
    console, print_main_banner, print_main_menu, print_goodbye,
    print_forced_exit, print_error, print_info, press_enter,
    ask_input,
)
from config import SESSIONS_DIR
from core.account_store import sync_sessions_with_store
from utils.sessions import get_session_files, print_sessions
from modes.dm import mode_dm
from modes.comments import mode_comments
from modes.subscribe import mode_subscribe
from modes.report import mode_report
from modes.calls import mode_calls_combo
from modes.secret import mode_secret_chat
from modes.ttl_spam import mode_ttl_spam
from manager_modes.check_sessions import check_sessions


async def main():
    print_main_banner()
    sync_sessions_with_store()

    while True:
        print_main_menu()
        choice = ask_input("Выбери действие", "0")

        if choice == "0":
            print_goodbye()
            break

        sessions = get_session_files(SESSIONS_DIR)
        if not sessions:
            print_error(f"Нет .session файлов в '{SESSIONS_DIR}/'")
            print_info("Используй manager.py для создания/импорта сессий.")
            press_enter()
            continue

        print_sessions(sessions)

        handlers = {
            "1": mode_dm,
            "2": mode_comments,
            "3": mode_subscribe,
            "4": mode_report,
            "5": mode_calls_combo,
            "6": mode_secret_chat,
            "7": mode_ttl_spam,
        }

        if choice == "8":
            # Checking sessions (without deleting)
            await check_sessions(sessions, allow_delete=False)
        elif choice in handlers:
            await handlers[choice](sessions)
        else:
            print_error("Неизвестный пункт меню.")

        press_enter()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_forced_exit()