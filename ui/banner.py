"""ASCII banners for main.py and manager.py."""

from rich.panel import Panel
from rich.align import Align
from rich import box

from ui.console import console

# ── Main banner (TG REAPER) ──────────────────────────────────

BANNER_TG = """[banner.tg]
 ████████╗ ██████╗
 ╚══██╔══╝██╔════╝
    ██║   ██║  ███╗
    ██║   ██║   ██║
    ██║   ╚██████╔╝
    ╚═╝    ╚═════╝[/]"""

BANNER_PLANE = "[banner.line]    ✈─────────────────────────────────── ·  ·  ·[/]"

BANNER_REAPER = """[banner.r1]██████╗ ███████╗ █████╗ ██████╗ ███████╗██████╗[/]
[banner.r1]██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝██╔══██╗[/]
[banner.r2]██████╔╝█████╗  ███████║██████╔╝█████╗  ██████╔╝[/]
[banner.r2]██╔══██╗██╔══╝  ██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗[/]
[banner.r3]██║  ██║███████╗██║  ██║██║     ███████╗██║  ██║[/]
[banner.r3]╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝[/]"""


def print_main_banner():
    lines = [
        "", BANNER_TG, "", BANNER_PLANE, "",
        BANNER_REAPER, "",
        "[banner.sub]⚡ Telegram Multi-Tool ⚡  v2.0[/]", "",
    ]
    panel = Panel(
        Align.center("\n".join(lines)),
        border_style="red",
        box=box.DOUBLE_EDGE,
        padding=(1, 4),
    )
    console.print(panel)


# ── Manager banner ────────────────────────────────────────────

BANNER_SESSION = """[bold bright_cyan]███████╗███████╗███████╗███████╗██╗ ██████╗ ███╗   ██╗[/]
[bold bright_cyan]██╔════╝██╔════╝██╔════╝██╔════╝██║██╔═══██╗████╗  ██║[/]
[bold bright_cyan]███████╗█████╗  ███████╗███████╗██║██║   ██║██╔██╗ ██║[/]
[bold bright_cyan]╚════██║██╔══╝  ╚════██║╚════██║██║██║   ██║██║╚██╗██║[/]
[bold bright_cyan]███████║███████╗███████║███████║██║╚██████╔╝██║ ╚████║[/]
[bold bright_cyan]╚══════╝╚══════╝╚══════╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝[/]"""

BANNER_MANAGER = """[bold bright_cyan]███╗   ███╗ █████╗ ███╗   ██╗ █████╗  ██████╗ ███████╗██████╗[/]
[bold bright_cyan]████╗ ████║██╔══██╗████╗  ██║██╔══██╗██╔════╝ ██╔════╝██╔══██╗[/]
[bold bright_cyan]██╔████╔██║███████║██╔██╗ ██║███████║██║  ███╗█████╗  ██████╔╝[/]
[bold bright_cyan]██║╚██╔╝██║██╔══██║██║╚██╗██║██╔══██║██║   ██║██╔══╝  ██╔══██╗[/]
[bold bright_cyan]██║ ╚═╝ ██║██║  ██║██║ ╚████║██║  ██║╚██████╔╝███████╗██║  ██║[/]
[bold bright_cyan]╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝[/]"""


def print_manager_banner():
    lines = [
        "", BANNER_SESSION, "", BANNER_MANAGER, "",
        "[white]                          __|__                         [/]",
        "[white]                   --o--o--(_)--o--o--                  [/]",
        "[bright_cyan]                  ✈  ·  ·  ·  ·  ·  ✈                  [/]",
        "",
        "[dim bright_white]           ╔══════════════════════════════════╗          [/]",
        "[dim bright_white]           ║  account session manager tool    ║          [/]",
        "[dim bright_white]           ╚══════════════════════════════════╝          [/]",
        "",
    ]
    panel = Panel(
        Align.center("\n".join(lines)),
        border_style="bright_cyan",
        box=box.DOUBLE_EDGE,
        padding=(1, 2),
    )
    console.print(panel)