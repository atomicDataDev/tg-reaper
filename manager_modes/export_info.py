"""Manager: Export information.

Now also exports proxies."""

import time

from core.account_store import get_all_accounts
from ui.console import console
from ui.panels import print_header
from ui.messages import print_success, print_error
from ui.inputs import ask_input, press_enter


async def manager_export_info(sessions):
    print_header("📤  ЭКСПОРТ ИНФОРМАЦИИ")

    accounts = get_all_accounts()
    if not accounts:
        print_error("Нет данных.")
        press_enter()
        return

    filename = ask_input(
        "Имя файла",
        f"accounts_export_{int(time.time())}.txt",
    )

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(
                f"{'=' * 60}\n"
                f"ЭКСПОРТ АККАУНТОВ TG REAPER\n"
                f"{'=' * 60}\n\n"
            )
            f.write(f"Всего: {len(accounts)}\n\n")

            for key, acc in accounts.items():
                f.write(f"--- {key} ---\n")
                f.write(f"  Статус:   {acc.get('status', '?')}\n")
                if acc.get("user_id"):
                    f.write(f"  User ID:  {acc['user_id']}\n")
                if acc.get("phone"):
                    f.write(f"  Телефон:  {acc['phone']}\n")
                if acc.get("username"):
                    f.write(f"  Username: @{acc['username']}\n")
                names = []
                if acc.get("first_name"):
                    names.append(acc["first_name"])
                if acc.get("last_name"):
                    names.append(acc["last_name"])
                if names:
                    f.write(f"  Имя:      {' '.join(names)}\n")
                device = acc.get("device") or {}
                if device:
                    f.write(
                        f"  Device:   {device.get('device_model', '?')} | "
                        f"{device.get('system_version', '?')} | "
                        f"{device.get('app_version', '?')}\n"
                    )

                if acc.get("last_checked"):
                    f.write(f"  Проверен: {acc['last_checked']}\n")
                f.write("\n")

        print_success(f"Сохранено в {filename}")
    except Exception as e:
        print_error(f"Ошибка: {e}")

    press_enter()