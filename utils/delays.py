"""
Delays between actions
"""

import random
import asyncio
from ui import print_wait, ask_input, print_choices


async def get_delay(min_d: float, max_d: float) -> float:
    """Makes delay"""
    delay = round(random.uniform(min_d, max_d), 1) if min_d != max_d else min_d
    if delay > 0:
        print_wait(f"Жду {delay} сек...")
        await asyncio.sleep(delay)
    return delay


def ask_delay() -> tuple[float, float]:
    """Interactive delay choice"""
    print_choices([
        ("1", "Фиксированная"),
        ("2", "Случайная в диапазоне"),
    ], "Режим задержки:")

    choice = ask_input("Выбор", "1")
    if choice == "2":
        mn = float(ask_input("Мин. задержка (сек)", "1") or "1")
        mx = float(ask_input("Макс. задержка (сек)", "5") or "5")
        if mn > mx:
            mn, mx = mx, mn
        return mn, mx
    d = float(ask_input("Задержка (сек)", "1") or "1")
    return d, d