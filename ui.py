"""

TG REAPER interface based on Rich library
Banner, menu, tables, pannels, progress
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.align import Align
from rich import box
from rich.prompt import Prompt, Confirm
from rich.rule import Rule
from rich.markup import escape
from rich.live import Live
from rich.spinner import Spinner
from rich.padding import Padding
from rich.theme import Theme

# -- Theme ------------------------------------------------------

custom_theme = Theme({
    "info":       "cyan",
    "success":    "bold green",
    "warning":    "bold yellow",
    "error":      "bold red",
    "action":     "bold blue",
    "wait":       "yellow",
    "skull":      "bold red",
    "fire":       "bold rgb(255,140,0)",
    "blade":      "rgb(80,180,255)",
    "shadow":     "dim white",
    "gold":       "bold rgb(255,200,50)",
    "header":     "bold white on rgb(30,30,60)",
    "menu.key":   "bold rgb(255,200,50)",
    "menu.icon":  "white",
    "menu.label": "white",
    "stat.key":   "cyan",
    "stat.val":   "bold white",
    "banner.tg":  "bold rgb(80,180,255)",
    "banner.r1":  "bold rgb(220,50,50)",
    "banner.r2":  "bold rgb(255,140,0)",
    "banner.r3":  "bold rgb(255,200,50)",
    "banner.line": "white",
    "banner.sub": "dim white",
})

console = Console(theme=custom_theme)

# ══════════════════════════════════════════════════════════════
# Main banner
# ══════════════════════════════════════════════════════════════

BANNER_TG = """[banner.tg]
 ████████╗ ██████╗
 ╚══██╔══╝██╔════╝
    ██║   ██║  ███╗
    ██║   ██║   ██║
    ██║   ╚██████╔╝
    ╚═╝    ╚═════╝[/]"""

BANNER_PLANE = "[banner.line]    ✈----------------------------------- ·  ·  ·[/]"

BANNER_REAPER = """[banner.r1]██████╗ ███████╗ █████╗ ██████╗ ███████╗██████╗[/]
[banner.r1]██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝██╔══██╗[/]
[banner.r2]██████╔╝█████╗  ███████║██████╔╝█████╗  ██████╔╝[/]
[banner.r2]██╔══██╗██╔══╝  ██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗[/]
[banner.r3]██║  ██║███████╗██║  ██║██║     ███████╗██║  ██║[/]
[banner.r3]╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝[/]"""

BANNER_SUB = "[banner.sub]⚡ Telegram Multi-Tool ⚡      [/]"


def print_banner():
    # Prints main banner
    banner_text = Text()
    lines = []
    lines.append("")
    lines.append(BANNER_TG)
    lines.append("")
    lines.append(BANNER_PLANE)
    lines.append("")
    lines.append(BANNER_REAPER)
    lines.append("")
    lines.append(BANNER_SUB)
    lines.append("")

    full = "\n".join(lines)

    panel = Panel(
        Align.center(full),
        border_style="red",
        box=box.DOUBLE_EDGE,
        padding=(1, 4),
    )
    console.print(panel)


# ══════════════════════════════════════════════════════════════
# Headers and divisors
# ══════════════════════════════════════════════════════════════

def print_separator(style: str = "blade", char: str = "-"):
    # Horizontal divisor
    console.print(Rule(style=style, characters=char))


def print_header(title: str):
    # Header in pannel section
    console.print()
    panel = Panel(
        Align.center(f"[bold white]{title}[/]"),
        border_style="blade",
        box=box.HEAVY,
        padding=(0, 2),
    )
    console.print(panel)


def print_sub_header(title: str):
    # h2
    console.print()
    console.print(
        Panel(
            Align.center(f"[bold cyan]{title}[/]"),
            border_style="cyan",
            box=box.ROUNDED,
            padding=(0, 2),
        )
    )


# ══════════════════════════════════════════════════════════════
# Messages
# ══════════════════════════════════════════════════════════════

def print_info(msg: str):
    # Info message
    console.print(f"  [info][ℹ][/] {msg}")


def print_success(msg: str):
    # Succesful action
    console.print(f"  [success][✓][/] {msg}")


def print_error(msg: str):
    # Error
    console.print(f"  [error][✗][/] {msg}")


def print_warning(msg: str):
    # Warning
    console.print(f"  [warning][⚠][/] {msg}")


def print_action(msg: str):
    # Action in process
    console.print(f"  [action][→][/] {msg}")


def print_wait(msg: str):
    # Await
    console.print(f"  [wait][⏳][/] {msg}")


def print_skull(msg: str):
    # Danger action
    console.print(f"  [skull][💀][/] {msg}")


def print_fire(msg: str):
    # Fire marker
    console.print(f"  [fire][🔥][/] {msg}")


def print_dim(msg: str):
    # Shadowed text
    console.print(f"  [shadow]{msg}[/]")


def print_call(msg: str):
    # Call
    console.print(f"  [info][📞][/] {msg}")


def print_lock(msg: str):
    # Secret chat
    console.print(f"  [info][🔐][/] {msg}")


def print_trash(msg: str):
    # Removal
    console.print(f"  [shadow][🗑][/] {msg}")


def print_timer(msg: str):
    # Timer
    console.print(f"  [gold][⏱][/] {msg}")


# ══════════════════════════════════════════════════════════════
# Input
# ══════════════════════════════════════════════════════════════

def ask_input(prompt: str, default: str = "") -> str:
    # Beautiful input via Rich
    if default:
        result = Prompt.ask(f"  [blade]▸[/] {prompt}", default=default, console=console)
    else:
        result = Prompt.ask(f"  [blade]▸[/] {prompt}", console=console, default="")
    return result.strip()


def ask_confirm(prompt: str = "Начать?") -> bool:
    # Confirmation await
    return Confirm.ask(f"  [gold]⚡ {prompt}[/]", console=console, default=False)


def ask_target_input(prompt: str = None) -> str:
    # Target input (username / телефон / ссылка)
    if prompt is None:
        console.print()
        console.print("  [cyan]Введите получателя[/]")
        console.print("  [shadow](username без @, ссылка t.me/xxx или номер телефона)[/]")
        prompt = "Цель"
    return ask_input(prompt)


# ══════════════════════════════════════════════════════════════
# Tables
# ══════════════════════════════════════════════════════════════

def create_table(
    title: str = "",
    columns: list[tuple[str, str]] = None,
    box_style=box.ROUNDED,
    border_style: str = "blade",
) -> Table:
    """
    Creates Rich table
    columns: [(name, style), ...]
    """
    table = Table(
        title=title if title else None,
        box=box_style,
        border_style=border_style,
        show_header=True,
        header_style="bold cyan",
        padding=(0, 1),
        expand=False,
    )
    if columns:
        for col_name, col_style in columns:
            table.add_column(col_name, style=col_style)
    return table


def print_table(table: Table):
    # Prints out the table
    console.print()
    console.print(Padding(table, (0, 2)))


# ══════════════════════════════════════════════════════════════
# Stats
# ══════════════════════════════════════════════════════════════

def print_stats_box(stats: dict, title: str = "РЕЗУЛЬТАТЫ"):
    # Stat block in pannel
    lines = []
    for key, value in stats.items():
        lines.append(f"[stat.key]{key}[/]  [stat.val]{value}[/]")

    content = "\n".join(lines)
    panel = Panel(
        content,
        title=f"[gold]{title}[/]",
        border_style="gold",
        box=box.DOUBLE_EDGE,
        padding=(1, 3),
        expand=False,
    )
    console.print()
    console.print(Padding(panel, (0, 2)))


# ══════════════════════════════════════════════════════════════
# Rounds
# ══════════════════════════════════════════════════════════════

def print_round(num: int):
    # Round header
    console.print()
    console.print(Rule(f"[fire]⚔  Раунд #{num}[/]", style="fire", characters="━"))


# ══════════════════════════════════════════════════════════════
# Sessions
# ══════════════════════════════════════════════════════════════

def print_sessions_table(sessions: list[str]):
    # Prints session list
    import os

    table = Table(
        title=f"[bold cyan]СЕССИИ: {len(sessions)} шт.[/]",
        box=box.ROUNDED,
        border_style="cyan",
        show_header=True,
        header_style="bold cyan",
        padding=(0, 1),
    )
    table.add_column("#", style="dim", width=5, justify="right")
    table.add_column("Файл сессии", style="white")

    for i, s in enumerate(sessions, 1):
        name = os.path.basename(s)
        table.add_row(str(i), f"{name}[dim].session[/]")

    console.print()
    console.print(Padding(table, (0, 2)))


# ══════════════════════════════════════════════════════════════
# Settings (prewiev before starting)
# ══════════════════════════════════════════════════════════════

def print_config_box(config: dict, title: str = "НАСТРОЙКИ"):
    # Settings block before starting
    lines = []
    for key, value in config.items():
        lines.append(f"[cyan]{key:<16}[/] : [white]{value}[/]")

    content = "\n".join(lines)
    panel = Panel(
        content,
        title=f"[blade]{title}[/]",
        border_style="blade",
        box=box.ROUNDED,
        padding=(1, 3),
        expand=False,
    )
    console.print()
    console.print(Padding(panel, (0, 2)))


# ══════════════════════════════════════════════════════════════
# Main menu
# ══════════════════════════════════════════════════════════════

def print_main_menu():
    # Main menu list
    menu_items = [
        ("1", "💬", "Отправка личных сообщений"),
        ("2", "📝", "Комментарии в канале"),
        ("3", "🔍", "Проверка сессий"),
        ("4", "📢", "Подписка на канал"),
        ("5", "🚨", "Отправка жалоб"),
        ("6", "📞", "Звонки / комбо"),
        ("7", "🔐", "Секретные чаты (TTL)"),
        ("8", "🤖", "Проверка @SpamBot"),
        ("9", "⌛ ", "TTL-спам (обычный чат)"),
    ]

    table = Table(
        box=box.ROUNDED,
        border_style="blade",
        show_header=False,
        padding=(0, 2),
        expand=False,
    )
    table.add_column("Клавиша", style="menu.key", width=5, justify="center")
    table.add_column("", width=3)
    table.add_column("Действие", style="menu.label")

    for key, icon, label in menu_items:
        table.add_row(key, icon, label)

    table.add_row("", "", "")
    table.add_row("[red]0[/]", "❌", "[red]Выход[/]")

    console.print()
    console.print(
        Panel(
            Align.center("[bold white]ГЛАВНОЕ МЕНЮ[/]"),
            border_style="blade",
            box=box.HEAVY,
            padding=(0, 2),
        )
    )
    console.print()
    console.print(Padding(table, (0, 4)))
    console.print()
    console.print("  [shadow]💡 Поиск: username ИЛИ номер телефона[/]")
    console.print()


# ══════════════════════════════════════════════════════════════
# Selection from list
# ══════════════════════════════════════════════════════════════

def print_choices(items: list[tuple[str, str]], title: str = ""):
    """
    Prints enumerate list
    items: [(key, label), ...]
    """
    if title:
        console.print(f"\n  [cyan]{title}[/]")
    for key, label in items:
        console.print(f"  [shadow]  {key:>3}[/] — {label}")


def print_description_box(text: str, title: str = "", style: str = "yellow"):
    # Description / Warning block
    panel = Panel(
        text,
        title=f"[{style}]{title}[/]" if title else None,
        border_style=style,
        box=box.ROUNDED,
        padding=(1, 3),
        expand=False,
    )
    console.print()
    console.print(Padding(panel, (0, 2)))


# ══════════════════════════════════════════════════════════════
# Farewell
# ══════════════════════════════════════════════════════════════

def print_goodbye():
    # Farewell message
    console.print()
    console.print(Rule(style="red"))
    console.print(
        Align.center("[bold magenta]✦ До свидания! REAPER. 👋 ✦[/]")
    )
    console.print(Rule(style="red"))


def print_interrupted():
    # Ctrl+C interruption
    console.print(f"\n  [warning][!] Остановлено пользователем.[/]")


def print_forced_exit():
    # Forced exit
    console.print(f"\n  [error][!] Принудительный выход.[/]")


def press_enter():
    # Enter await
    console.print()
    Prompt.ask("  [shadow]Enter для возврата в меню...[/]", console=console, default="")
