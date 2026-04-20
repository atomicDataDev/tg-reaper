"""Message output functions."""

from ui.console import console


def print_info(msg: str):
    console.print(f"  [info][ℹ][/] {msg}")

def print_success(msg: str):
    console.print(f"  [success][✓][/] {msg}")

def print_error(msg: str):
    console.print(f"  [error][✗][/] {msg}")

def print_warning(msg: str):
    console.print(f"  [warning][⚠][/] {msg}")

def print_action(msg: str):
    console.print(f"  [action][→][/] {msg}")

def print_wait(msg: str):
    console.print(f"  [wait][⏳][/] {msg}")

def print_skull(msg: str):
    console.print(f"  [skull][💀][/] {msg}")

def print_fire(msg: str):
    console.print(f"  [fire][🔥][/] {msg}")

def print_dim(msg: str):
    console.print(f"  [shadow]{msg}[/]")

def print_call(msg: str):
    console.print(f"  [info][📞][/] {msg}")

def print_lock(msg: str):
    console.print(f"  [info][🔐][/] {msg}")

def print_trash(msg: str):
    console.print(f"  [shadow][🗑][/] {msg}")

def print_timer(msg: str):
    console.print(f"  [gold][⏱][/] {msg}")