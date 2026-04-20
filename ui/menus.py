"""Menu for main.py and manager.py."""

from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich.padding import Padding
from rich import box

from ui.console import console


def print_main_menu():
    """Main program menu (attack)."""
    items = [
        ("1", "💬", "Отправка личных сообщений"),
        ("2", "📝", "Комментарии в канале"),
        ("3", "📢", "Подписка на канал"),
        ("4", "🚨", "Отправка жалоб"),
        ("5", "📞", "Звонки / комбо"),
        ("6", "🔐", "Секретные чаты (TTL)"),
        ("7", "⌛", "TTL-спам (обычный чат)"),
        ("", "", ""),
        ("8", "🔍", "Проверка сессий"),
    ]

    table = Table(
        box=box.ROUNDED, border_style="blade",
        show_header=False, padding=(0, 2), expand=False,
    )
    table.add_column("K", style="menu.key", width=5, justify="center")
    table.add_column("", width=3)
    table.add_column("Действие", style="menu.label")

    for key, icon, label in items:
        table.add_row(key, icon, label)
    table.add_row("", "", "")
    table.add_row("[red]0[/]", "❌", "[red]Выход[/]")

    console.print()
    console.print(Panel(
        Align.center("[bold white]ГЛАВНОЕ МЕНЮ — REAPER[/]"),
        border_style="blade", box=box.HEAVY, padding=(0, 2),
    ))
    console.print()
    console.print(Padding(table, (0, 4)))
    console.print()


def print_manager_menu():
    """Session manager menu."""
    items = [
        ("1", "➕", "Создать новую сессию"),
        ("2", "🔍", "Проверка сессий"),
        ("3", "📋", "Список всех сессий (подробно)"),
        ("4", "🔑", "Управление облачным паролем (2FA)"),
        ("5", "🗑️", "Удалить все авторизации"),
        ("6", "📧", "Сменить Login Email — все сессии"),
        ("7", "📧", "Сменить Login Email — выбор сессий"),
        ("8", "📲", "Получить код входа по номеру"),
        ("9", "🔓", "Перехватить код через сессию"),
        ("11", "♻", "Пересоздание сессий"),
        ("12", "📤", "Экспорт информации"),
        ("13", "🔄", "Синхронизация sessions ↔ accounts.json"),
    ]

    table = Table(
        box=box.ROUNDED, border_style="bright_cyan",
        show_header=False, padding=(0, 2), expand=False,
    )
    table.add_column("K", style="bold yellow", width=5, justify="center")
    table.add_column("", width=3)
    table.add_column("Действие", style="white")

    for key, icon, label in items:
        table.add_row(key, icon, label)
    table.add_row("", "", "")
    table.add_row("[red]0[/]", "❌", "[red]Выход[/]")

    console.print()
    console.print(Panel(
        Align.center("[bold white]МЕНЕДЖЕР СЕССИЙ[/]"),
        border_style="bright_cyan", box=box.HEAVY, padding=(0, 2),
    ))
    console.print()
    console.print(Padding(table, (0, 4)))
    console.print()