import asyncio
from ui import (
    console, print_banner, print_main_menu, print_goodbye,
    print_forced_exit, print_error, print_info, press_enter,
    ask_input,
)
from config import SESSIONS_DIR
from utils.sessions import get_session_files, print_sessions
from modes.dm import mode_dm
from modes.comments import mode_comments
from modes.check_sessions import mode_check_sessions
from modes.subscribe import mode_subscribe
from modes.report import mode_report
from modes.calls import mode_calls_combo
from modes.secret import mode_secret_chat
from modes.spambot import mode_check_spambot
from modes.ttl_spam import mode_ttl_spam


async def main():
    print_banner()

    while True:
        print_main_menu()
        choice = ask_input("Выбери действие", "0")

        if choice == "0":
            print_goodbye()
            break

        sessions = get_session_files(SESSIONS_DIR)
        if not sessions:
            print_error(f"Нет .session файлов в '{SESSIONS_DIR}/'")
            print_info("Положи файлы сессий в папку и попробуй снова.")
            press_enter()
            continue

        print_sessions(sessions)

        handlers = {
            "1": mode_dm,
            "2": mode_comments,
            "3": mode_check_sessions,
            "4": mode_subscribe,
            "5": mode_report,
            "6": mode_calls_combo,
            "7": mode_secret_chat,
            "8": mode_check_spambot,
            "9": mode_ttl_spam,
        }

        handler = handlers.get(choice)
        if handler:
            await handler(sessions)
        else:
            print_error("Неизвестный пункт меню.")

        press_enter()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_forced_exit()