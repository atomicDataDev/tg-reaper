"""Manager: Detailed list of all sessions.
Now shows proxy."""

import os

from telethon import functions

from config import SESSIONS_DIR
from core.client_factory import create_client
from core.account_store import get_device_for_session
from ui.console import console
from ui.panels import print_header
from ui.inputs import press_enter
from utils.parsers import format_phone
from utils.sessions import get_session_names

from rich.table import Table
from rich import box


async def manager_list_sessions(sessions):
    print_header("📋  СПИСОК ВСЕХ СЕССИЙ")

    names = get_session_names()
    if not names:
        console.print("  [red]❌ Нет сессий[/]")
        press_enter()
        return

    table = Table(
        title=f"[bold]Всего: {len(names)}[/]",
        box=box.ROUNDED, border_style="bright_blue",
        header_style="bold cyan", padding=(0, 1),
        show_lines=True,
    )
    table.add_column("#", style="yellow bold", width=4, justify="center")
    table.add_column("Файл", style="white", min_width=14)
    table.add_column("Телефон", style="bright_white", min_width=16)
    table.add_column("Имя", style="white", min_width=12)
    table.add_column("Username", style="bright_cyan", min_width=13)
    table.add_column("ID", style="dim", min_width=11)
    table.add_column("2FA", justify="center", width=4)
    table.add_column("Устр.", style="cyan", justify="center", width=5)
    table.add_column("Email", style="magenta", max_width=24)
    table.add_column("Device", style="dim", max_width=20)

    with console.status("[cyan]Загрузка...[/]", spinner="dots"):
        for i, session_name in enumerate(names, 1):
            session_path = os.path.join(SESSIONS_DIR, session_name)
            client = create_client(session_path, receive_updates=False)
            device = get_device_for_session(session_path)
            device_short = device["device_model"][:18]

            try:
                await client.connect()
                if await client.is_user_authorized():
                    me = await client.get_me()
                    name = (
                        (me.first_name or "") + " " +
                        (me.last_name or "")
                    ).strip()[:14]
                    username = f"@{me.username}" if me.username else "—"
                    phone = format_phone(me.phone)

                    try:
                        result = await client(
                            functions.account.GetAuthorizationsRequest()
                        )
                        devices = str(len(result.authorizations))
                    except Exception:
                        devices = "?"

                    try:
                        pwd_info = await client(
                            functions.account.GetPasswordRequest()
                        )
                        has_2fa = (
                            "[green]✅[/]"
                            if pwd_info.has_password
                            else "[red]❌[/]"
                        )
                        login_email = (
                            getattr(pwd_info, 'login_email_pattern', '') or ""
                        )
                        has_recovery = getattr(pwd_info, 'has_recovery', False)
                        pending = pwd_info.email_unconfirmed_pattern or ""
                        parts = []
                        if login_email:
                            parts.append(f"login:{login_email}")
                        if has_recovery:
                            parts.append("rcv:✅")
                        elif pending:
                            parts.append(f"rcv:⏳{pending}")
                        email_status = (
                            " | ".join(parts) if parts else "[dim]—[/]"
                        )
                    except Exception:
                        has_2fa = "?"
                        email_status = "?"

                    table.add_row(
                        str(i), session_name, phone, name, username,
                        str(me.id), has_2fa, devices,
                        email_status,
                        f"[dim]{device_short}[/]",
                    )
                else:
                    table.add_row(
                        str(i), session_name,
                        "[red]НЕ АВТОРИЗОВАН[/]",
                        "", "", "", "", "",
                        "",
                        f"[dim]{device_short}[/]",
                    )
            except Exception as e:
                table.add_row(
                    str(i), session_name, f"[red]ERR[/]",
                    f"[dim]{str(e)[:20]}[/]", "", "", "", "",
                        "",
                    f"[dim]{device_short}[/]",
                )
            finally:
                await client.disconnect()

    console.print(table)
    press_enter()