"""
Mode 3: Session Check
"""

import os
from rich.table import Table
from rich.prompt import Confirm
from rich import box

from utils.client import create_client, get_session_name
from ui import console, print_header, print_stats_box, print_table


async def mode_check_sessions(sessions):
    # Checks all sessions
    print_header("🔍  ПРОВЕРКА СЕССИЙ")

    table = Table(
        title="[bold cyan]Статус аккаунтов[/]",
        box=box.ROUNDED,
        border_style="cyan",
        show_header=True,
        header_style="bold cyan",
        padding=(0, 1),
    )
    table.add_column("Статус", width=8, justify="center")
    table.add_column("Сессия", style="white", min_width=20)
    table.add_column("Информация", style="dim", min_width=30)

    alive = dead = 0
    dead_sessions = []

    for sess in sessions:
        name = get_session_name(sess)
        client = create_client(sess, receive_updates=False)
        try:
            await client.connect()
            if await client.is_user_authorized():
                me = await client.get_me()
                info = f"{me.first_name or ''}"
                if me.username:
                    info += f" @{me.username}"
                info += f" | {me.phone or 'no phone'}"
                table.add_row("[green]✅[/]", name, info)
                alive += 1
            else:
                table.add_row("[red]❌[/]", name, "[red]не авторизован[/]")
                dead += 1
                dead_sessions.append(sess)
        except Exception as e:
            table.add_row("[red]❌[/]", name, f"[red]{str(e)[:40]}[/]")
            dead += 1
            dead_sessions.append(sess)
        finally:
            await client.disconnect()

    print_table(table)

    print_stats_box({
        "✅ Рабочих": alive,
        "❌ Мёртвых": dead,
        "📊 Всего": alive + dead,
    }, "ИТОГИ ПРОВЕРКИ")

    # Request to delete dead sessions
    if dead_sessions:
        console.print()
        console.print(
            f"[bold yellow]⚠  Найдено мёртвых сессий: {len(dead_sessions)}[/]"
        )
        for ds in dead_sessions:
            console.print(f"   [dim red]• {os.path.basename(ds)}[/]")
        console.print()

        if Confirm.ask(
            "[bold yellow]Удалить мёртвые сессии?[/]", default=False
        ):
            deleted = 0
            errors = 0
            for sess_path in dead_sessions:
                session_file = (
                    sess_path if sess_path.endswith(".session") else sess_path + ".session"
                )
                journal_file = session_file + "-journal"

                for fpath in (session_file, journal_file):
                    if os.path.exists(fpath):
                        try:
                            os.remove(fpath)
                            console.print(
                                f"   [green]🗑  Удалён:[/] {os.path.basename(fpath)}"
                            )
                            deleted += 1
                        except OSError as e:
                            console.print(
                                f"   [red]✖  Ошибка удаления {os.path.basename(fpath)}: {e}[/]"
                            )
                            errors += 1

            console.print()
            console.print(
                f"[bold green]✅ Удалено файлов: {deleted}[/]"
                + (f"  [bold red]| Ошибок: {errors}[/]" if errors else "")
            )
        else:
            console.print("[dim]Удаление отменено.[/]")