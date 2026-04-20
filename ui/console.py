"""Rich Console with custom theme."""

from rich.console import Console
from rich.theme import Theme

custom_theme = Theme({
    "info":        "cyan",
    "success":     "bold green",
    "warning":     "bold yellow",
    "error":       "bold red",
    "action":      "bold blue",
    "wait":        "yellow",
    "skull":       "bold red",
    "fire":        "bold rgb(255,140,0)",
    "blade":       "rgb(80,180,255)",
    "shadow":      "dim white",
    "gold":        "bold rgb(255,200,50)",
    "menu.key":    "bold rgb(255,200,50)",
    "menu.label":  "white",
    "stat.key":    "cyan",
    "stat.val":    "bold white",
    "banner.tg":   "bold rgb(80,180,255)",
    "banner.r1":   "bold rgb(220,50,50)",
    "banner.r2":   "bold rgb(255,140,0)",
    "banner.r3":   "bold rgb(255,200,50)",
    "banner.line": "white",
    "banner.sub":  "dim white",
})

console = Console(theme=custom_theme)