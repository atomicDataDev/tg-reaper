"""Tables, statistics, rounds."""

import os
from rich.table import Table
from rich.panel import Panel
from rich.padding import Padding
from rich.rule import Rule
from rich import box

from ui.console import console


def create_table(
    title: str = "",
    columns: list[tuple[str, str]] = None,
    box_style=box.ROUNDED,
    border_style: str = "blade",
) -> Table:
    table = Table(
        title=title if title else None,
        box=box_style, border_style=border_style,
        show_header=True, header_style="bold cyan",
        padding=(0, 1), expand=False,
    )
    if columns:
        for col_name, col_style in columns:
            table.add_column(col_name, style=col_style)
    return table


def print_table(table: Table):
    console.print()
    console.print(Padding(table, (0, 2)))


def print_stats_box(stats: dict, title: str = "РЕЗУЛЬТАТЫ"):
    lines = []
    for key, value in stats.items():
        lines.append(f"[stat.key]{key}[/]  [stat.val]{value}[/]")
    panel = Panel(
        "\n".join(lines),
        title=f"[gold]{title}[/]",
        border_style="gold",
        box=box.DOUBLE_EDGE,
        padding=(1, 3), expand=False,
    )
    console.print()
    console.print(Padding(panel, (0, 2)))


def print_round(num: int):
    console.print()
    console.print(Rule(
        f"[fire]⚔  Раунд #{num}[/]",
        style="fire", characters="━",
    ))


def print_sessions_table(sessions: list[str]):
    table = Table(
        title=f"[bold cyan]СЕССИИ: {len(sessions)} шт.[/]",
        box=box.ROUNDED, border_style="cyan",
        show_header=True, header_style="bold cyan",
        padding=(0, 1),
    )
    table.add_column("#", style="dim", width=5, justify="right")
    table.add_column("Файл сессии", style="white")

    for i, s in enumerate(sessions, 1):
        name = os.path.basename(s)
        table.add_row(str(i), f"{name}[dim].session[/]")

    console.print()
    console.print(Padding(table, (0, 2)))