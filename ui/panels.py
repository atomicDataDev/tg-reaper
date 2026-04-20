"""Panels, titles, descriptions."""

from rich.panel import Panel
from rich.align import Align
from rich.padding import Padding
from rich.rule import Rule
from rich import box

from ui.console import console


def print_separator(style: str = "blade", char: str = "-"):
    console.print(Rule(style=style, characters=char))


def print_header(title: str):
    console.print()
    console.print(Panel(
        Align.center(f"[bold white]{title}[/]"),
        border_style="blade", box=box.HEAVY,
        padding=(0, 2),
    ))


def print_sub_header(title: str):
    console.print()
    console.print(Panel(
        Align.center(f"[bold cyan]{title}[/]"),
        border_style="cyan", box=box.ROUNDED,
        padding=(0, 2),
    ))


def print_config_box(config: dict, title: str = "НАСТРОЙКИ"):
    lines = [
        f"[cyan]{key:<16}[/] : [white]{value}[/]"
        for key, value in config.items()
    ]
    console.print()
    console.print(Padding(Panel(
        "\n".join(lines),
        title=f"[blade]{title}[/]",
        border_style="blade", box=box.ROUNDED,
        padding=(1, 3), expand=False,
    ), (0, 2)))


def print_choices(items: list[tuple[str, str]], title: str = ""):
    if title:
        console.print(f"\n  [cyan]{title}[/]")
    for key, label in items:
        console.print(f"  [shadow]  {key:>3}[/] — {label}")


def print_description_box(
    text: str, title: str = "", style: str = "yellow",
):
    console.print()
    console.print(Padding(Panel(
        text,
        title=f"[{style}]{title}[/]" if title else None,
        border_style=style, box=box.ROUNDED,
        padding=(1, 3), expand=False,
    ), (0, 2)))


def print_goodbye():
    console.print()
    console.print(Rule(style="red"))
    console.print(Align.center(
        "[bold magenta]✦ До свидания! REAPER. 👋 ✦[/]"
    ))
    console.print(Rule(style="red"))


def print_interrupted():
    console.print("\n  [warning][!] Остановлено пользователем.[/]")


def print_forced_exit():
    console.print("\n  [error][!] Принудительный выход.[/]")