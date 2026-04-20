"""Checking sessions."""

import os

from rich.table import Table
from rich.prompt import Confirm, Prompt
from rich import box

from core.client_factory import create_client, get_session_name
from core.account_store import update_account_info, remove_account
from ui.console import console
from ui.panels import print_header
from ui.tables import print_table, print_stats_box
from ui.inputs import press_enter


async def check_sessions(sessions, allow_delete: bool = True):
    print_header("ПРОВЕРКА СЕССИЙ")

    table = Table(
        title="[bold cyan]Статус аккаунтов[/]",
        box=box.ROUNDED,
        border_style="cyan",
        show_header=True,
        header_style="bold cyan",
        padding=(0, 1),
    )
    table.add_column("", width=4, justify="center")
    table.add_column("Сессия", style="white", min_width=22)
    table.add_column("Информация", style="dim", min_width=30)

    alive = dead = 0
    dead_sessions = []
    dead_names = []

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
                table.add_row("[green]OK[/]", name, info)
                alive += 1
                update_account_info(
                    sess,
                    user_id=me.id,
                    phone=me.phone,
                    username=me.username,
                    first_name=me.first_name,
                    last_name=me.last_name,
                    status="alive",
                )
            else:
                table.add_row(
                    "[red]X[/]", name, "[red]не авторизован[/]"
                )
                dead += 1
                dead_sessions.append(sess)
                dead_names.append(name)
                update_account_info(sess, status="dead")
        except Exception as e:
            table.add_row(
                "[red]X[/]", name, f"[red]{str(e)[:40]}[/]"
            )
            dead += 1
            dead_sessions.append(sess)
            dead_names.append(name)
            update_account_info(sess, status="error")
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass

    print_table(table)

    stats = Table(
        show_header=False,
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 2),
    )
    stats.add_column(style="bold", min_width=14)
    stats.add_column(justify="right", width=6)
    stats.add_row("[green]Рабочих[/]", str(alive))
    stats.add_row("[red]Мертвых[/]", str(dead))
    stats.add_row("[cyan]Всего[/]", str(alive + dead))
    console.print(stats)

    if dead_sessions and allow_delete:
        console.print()
        console.print(
            f"  [bold yellow]Мертвых сессий: "
            f"{len(dead_sessions)}[/]"
        )
        for ds in dead_names:
            console.print(f"   [dim red]- {ds}[/]")
        console.print()

        console.print("  [yellow]1[/] Удалить мертвые")
        console.print("  [yellow]0[/] Ничего не делать")
        console.print()
        console.print(
            "  [dim]Мертвые сессии нельзя пересоздать.[/]"
        )
        console.print(
            "  [dim]Для новых аккаунтов используйте пункт 1.[/]"
        )
        console.print()

        choice = Prompt.ask(
            "  [cyan]Выбор[/]",
            choices=["0", "1"],
            default="0",
            console=console,
        )

        if choice == "1":
            if Confirm.ask(
                "  [bold yellow]Удалить мертвые сессии?[/]",
                default=False,
                console=console,
            ):
                for sess_path in dead_sessions:
                    remove_account(
                        sess_path, delete_session_file=True
                    )
                    console.print(
                        f"   [green]Удален:[/] "
                        f"{get_session_name(sess_path)}"
                    )
                console.print(
                    f"\n  [bold green]Удалено: "
                    f"{len(dead_sessions)}[/]"
                )
            else:
                console.print("  [dim]Отменено.[/]")
        else:
            console.print("  [dim]Отменено.[/]")

    press_enter()
    return dead_sessions