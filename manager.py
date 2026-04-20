"""TG REAPER -- Session manager.
Run: python manager.py"""

import asyncio

from ui import (
    console, print_manager_banner, print_manager_menu,
    print_goodbye, print_forced_exit, print_error, print_info,
    print_success, press_enter, ask_input,
)
from ui.panels import print_header
from config import SESSIONS_DIR
from core.account_store import sync_sessions_with_store
from utils.sessions import get_session_files, print_sessions

from manager_modes.create_session import manager_create_session
from manager_modes.check_sessions import check_sessions
from manager_modes.list_sessions import manager_list_sessions
from manager_modes.cloud_password import manager_cloud_password
from manager_modes.terminate_auths import manager_terminate_auths
from manager_modes.login_email import (
    manager_login_email_all,
    manager_login_email_selected,
)
from manager_modes.login_code import manager_get_login_code
from manager_modes.intercept_code import manager_intercept_code
from manager_modes.recreate_sessions import manager_recreate_sessions
from manager_modes.export_info import manager_export_info


async def manager_sync(sessions):
    print_header("СИНХРОНИЗАЦИЯ")
    files_count, total = sync_sessions_with_store()
    print_success(
        f"Файлов сессий: {files_count}, "
        f"записей в accounts.json: {total}"
    )
    press_enter()


async def main():
    print_manager_banner()
    console.print("  [bold cyan]РЕЖИМ: МЕНЕДЖЕР СЕССИЙ[/]\n")

    while True:
        print_manager_menu()
        choice = ask_input("Выбери действие", "0")

        if choice == "0":
            print_goodbye()
            break

        sessions = get_session_files(SESSIONS_DIR)
        no_sessions_ok = {"1", "13"}

        if not sessions and choice not in no_sessions_ok:
            print_error(f"Нет .session файлов в '{SESSIONS_DIR}/'")
            print_info("Используйте пункт 1 для создания сессий.")
            press_enter()
            continue

        if sessions and choice not in ("1",):
            print_sessions(sessions)

        handlers = {
            "1":  lambda s: manager_create_session(),
            "2":  lambda s: check_sessions(s, allow_delete=True),
            "3":  manager_list_sessions,
            "4":  manager_cloud_password,
            "5":  manager_terminate_auths,
            "6":  manager_login_email_all,
            "7":  manager_login_email_selected,
            "8":  manager_get_login_code,
            "9":  manager_intercept_code,
            "11": manager_recreate_sessions,
            "12": manager_export_info,
            "13": manager_sync,
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