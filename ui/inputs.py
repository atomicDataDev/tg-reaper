"""Input functions."""

from rich.prompt import Prompt, Confirm
from ui.console import console


def ask_input(prompt: str, default: str = "") -> str:
    if default:
        result = Prompt.ask(
            f"  [blade]▸[/] {prompt}",
            default=default, console=console,
        )
    else:
        result = Prompt.ask(
            f"  [blade]▸[/] {prompt}",
            console=console, default="",
        )
    return result.strip()


def ask_confirm(prompt: str = "Начать?") -> bool:
    return Confirm.ask(
        f"  [gold]⚡ {prompt}[/]",
        console=console, default=False,
    )


def ask_target_input(prompt: str = None) -> str:
    if prompt is None:
        console.print()
        console.print("  [cyan]Введите получателя[/]")
        console.print(
            "  [shadow](username без @, ссылка t.me/xxx "
            "или номер телефона)[/]"
        )
        prompt = "Цель"
    return ask_input(prompt)


def press_enter():
    console.print()
    Prompt.ask(
        "  [shadow]Enter для продолжения...[/]",
        console=console, default="",
    )