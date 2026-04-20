"""Manager: Deleting all authorizations."""

import re
import asyncio
import os

from telethon import errors, functions

from config import SESSIONS_DIR
from core.client_factory import create_client
from ui.console import console
from ui.panels import print_header
from ui.inputs import press_enter
from utils.parsers import format_seconds
from utils.sessions import get_session_names

from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box


async def manager_terminate_auths(sessions):
    while True:
        print_header("🗑️  УДАЛЕНИЕ ВСЕХ АВТОРИЗАЦИЙ")

        names = get_session_names()
        if not names:
            console.print("  [red]❌ Нет сессий[/]")
            press_enter()
            return

        table = Table(
            title="[bold]Обзор авторизаций[/]",
            box=box.ROUNDED, border_style="blue",
            header_style="bold cyan", padding=(0, 1),
        )
        table.add_column("#", style="yellow bold", width=4, justify="center")
        table.add_column("Сессия", style="white", min_width=16)
        table.add_column("Имя", style="bright_white", min_width=14)
        table.add_column("Всего", style="cyan", justify="center", width=7)
        table.add_column("Других", justify="center", width=8)

        session_data = []

        with console.status("[cyan]Загрузка данных...[/]", spinner="dots"):
            for i, s in enumerate(names, 1):
                session_path = os.path.join(SESSIONS_DIR, s)
                client = create_client(session_path)
                try:
                    await client.connect()
                    if await client.is_user_authorized():
                        me = await client.get_me()
                        result = await client(functions.account.GetAuthorizationsRequest())
                        total = len(result.authorizations)
                        others = [a for a in result.authorizations if not a.current]
                        name = ((me.first_name or "") + " " + (me.last_name or "")).strip()[:16]
                        style = "green" if len(others) == 0 else "red bold"
                        table.add_row(str(i), s, name, str(total), f"[{style}]{len(others)}[/]")
                        session_data.append((s, me, others))
                    else:
                        table.add_row(str(i), s, "[red]НЕ АВТОРИЗОВАН[/]", "—", "—")
                        session_data.append((s, None, []))
                except Exception:
                    table.add_row(str(i), s, "[red]ОШИБКА[/]", "—", "—")
                    session_data.append((s, None, []))
                finally:
                    await client.disconnect()

        console.print(table)
        console.print()

        total_others = sum(len(d[2]) for d in session_data)
        if total_others == 0:
            console.print(Panel(
                "[green]✅ Нет чужих авторизаций[/]",
                border_style="green",
            ))
            press_enter()
            return

        console.print(f"  Всего чужих: [bold red]{total_others}[/]")
        confirm = Prompt.ask(
            "  [cyan]Удалить ВСЕ другие авторизации?[/]",
            choices=["да", "нет"], default="нет", console=console,
        )
        if confirm != "да":
            return

        console.print()
        total_removed = total_failed = 0

        for s, me, others in session_data:
            if me is None or not others:
                continue
            session_path = os.path.join(SESSIONS_DIR, s)
            client = create_client(session_path)
            try:
                await client.connect()
                if not await client.is_user_authorized():
                    continue
                display = f"{s} ({me.first_name})"
                removed = failed = 0

                for auth in others:
                    try:
                        await client(functions.account.ResetAuthorizationRequest(hash=auth.hash))
                        removed += 1
                        await asyncio.sleep(0.3)
                    except errors.FloodWaitError as e:
                        console.print(f"  [yellow]⚠️  {display} — flood wait {format_seconds(e.seconds)}[/]")
                        failed += 1
                    except Exception as e:
                        failed += 1

                total_removed += removed
                total_failed += failed

                if removed > 0:
                    console.print(f"  [green]✅ {display}[/] — удалено {removed}/{len(others)}")
                if failed > 0:
                    console.print(f"  [red]❌ {display}[/] — ошибок {failed}")

            except Exception as e:
                console.print(f"  [red]❌ {s} — {e}[/]")
            finally:
                await client.disconnect()

        console.print()
        summary = Table(show_header=False, box=box.ROUNDED, border_style="cyan", padding=(0, 2))
        summary.add_column("", style="bold")
        summary.add_column("")
        summary.add_row("[green]✅ Удалено[/]", str(total_removed))
        summary.add_row("[red]❌ Ошибок[/]", str(total_failed))
        console.print(summary)

        console.print("  [dim]Обновляю список...[/]")
        await asyncio.sleep(2)