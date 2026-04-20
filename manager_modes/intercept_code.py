"""Manager: Intercepting code through a session."""

import os
import re
import asyncio

from telethon import errors

from config import SESSIONS_DIR
from core.client_factory import create_client
from ui.console import console
from ui.panels import print_header
from ui.inputs import press_enter
from utils.parsers import format_phone, format_seconds
from utils.sessions import get_session_names

from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box


async def _load_session_info(names):
    info = []
    for s in names:
        session_path = os.path.join(SESSIONS_DIR, s)
        client = create_client(session_path, receive_updates=False)
        try:
            await client.connect()
            if await client.is_user_authorized():
                me = await client.get_me()
                phone = format_phone(me.phone)
                phone_raw = str(me.phone or "")
                name = ((me.first_name or "") + " " + (me.last_name or "")).strip()
                info.append((s, me, phone, phone_raw, name, True))
            else:
                info.append((s, None, "—", "", "НЕ АВТОРИЗОВАН", False))
        except Exception as e:
            info.append((s, None, "—", "", f"ОШИБКА: {str(e)[:25]}", False))
        finally:
            await client.disconnect()
    return info


async def _intercept_from_client(client, last_msg_id, timeout=60):
    max_attempts = timeout // 2
    with Progress(
        SpinnerColumn("dots"),
        TextColumn("[cyan]Ожидаю код...[/]"),
        BarColumn(bar_width=35, style="cyan", complete_style="green"),
        TextColumn("[dim]{task.completed}с / {task.total}с[/]"),
        console=console, transient=True,
    ) as progress:
        task = progress.add_task("wait", total=timeout)
        for attempt in range(max_attempts):
            await asyncio.sleep(2)
            progress.update(task, completed=(attempt + 1) * 2)
            try:
                async for message in client.iter_messages(777000, limit=5):
                    if message.id <= last_msg_id:
                        continue
                    codes = re.findall(r'\b(\d{5,6})\b', message.text or "")
                    if codes:
                        return codes[0], message
            except Exception:
                pass
    return None, None


async def manager_intercept_code(sessions):
    print_header("🔓  ПЕРЕХВАТ КОДА ЧЕРЕЗ СЕССИЮ")

    names = get_session_names()
    if not names:
        console.print("  [red]❌ Нет сессий[/]")
        press_enter()
        return

    console.print("  [yellow][1][/] Показать все   [yellow][2][/] Найти по номеру")
    search_mode = Prompt.ask("  [cyan]Выбор[/]", choices=["1", "2"], default="1", console=console)

    with console.status("[cyan]Загрузка...[/]", spinner="dots"):
        session_info = await _load_session_info(names)

    chosen_idx = None

    if search_mode == "2":
        search = Prompt.ask("  [cyan]Номер (полный или часть)[/]", console=console).strip()
        search_clean = re.sub(r"[\+\s\-\(\)]", "", search)

        matches = []
        for idx, (s, me, phone, phone_raw, name, ok) in enumerate(session_info):
            if not ok:
                continue
            if search_clean in s or search_clean in phone_raw:
                matches.append(idx)

        if not matches:
            console.print(f"  [red]❌ Не найдено[/]")
            press_enter()
            return

        if len(matches) == 1:
            chosen_idx = matches[0]
        else:
            table = Table(box=box.ROUNDED, border_style="blue", padding=(0, 1))
            table.add_column("#", style="yellow bold", width=4, justify="center")
            table.add_column("Сессия", style="white")
            table.add_column("Телефон", style="bright_white")
            for di, ri in enumerate(matches, 1):
                s, me, phone, _, name, _ = session_info[ri]
                table.add_row(str(di), s, phone)
            console.print(table)

            num = Prompt.ask("  [cyan]Номер[/]", console=console).strip()
            try:
                n = int(num) - 1
                if 0 <= n < len(matches):
                    chosen_idx = matches[n]
                else:
                    console.print("  [red]❌ Неверный номер[/]")
                    press_enter()
                    return
            except ValueError:
                console.print("  [red]❌ Неверный ввод[/]")
                press_enter()
                return
    else:
        table = Table(box=box.ROUNDED, border_style="blue", header_style="bold cyan", padding=(0, 1))
        table.add_column("#", style="yellow bold", width=4, justify="center")
        table.add_column("Сессия", style="white", min_width=16)
        table.add_column("Телефон", style="bright_white")
        table.add_column("Имя", style="white")
        table.add_column("", justify="center", width=4)

        for i, (s, me, phone, _, name, ok) in enumerate(session_info, 1):
            status = "[green]●[/]" if ok else "[red]●[/]"
            table.add_row(str(i), s, phone, name if ok else f"[red]{name}[/]", status)
        console.print(table)

        num = Prompt.ask("  [cyan]Номер сессии[/]", console=console).strip()
        try:
            n = int(num) - 1
            if 0 <= n < len(session_info):
                chosen_idx = n
            else:
                console.print("  [red]❌ Неверный номер[/]")
                press_enter()
                return
        except ValueError:
            console.print("  [red]❌ Неверный ввод[/]")
            press_enter()
            return

    session_name, me, phone, _, name, ok = session_info[chosen_idx]
    if not ok:
        console.print("  [red]❌ Сессия не авторизована[/]")
        press_enter()
        return

    session_path = os.path.join(SESSIONS_DIR, session_name)
    client = create_client(session_path)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            console.print("  [red]❌ Не авторизована[/]")
            press_enter()
            return

        last_msg_id = 0
        try:
            async for msg in client.iter_messages(777000, limit=1):
                last_msg_id = msg.id
        except Exception:
            pass

        console.print()
        console.print("  [yellow][1][/] Ожидать код   [yellow][2][/] Запросить код")
        mode = Prompt.ask("  [cyan]Выбор[/]", choices=["1", "2"], default="1", console=console)

        if mode == "2":
            target_phone = Prompt.ask(
                f"  [cyan]Номер[/] [dim](Enter = {phone})[/]",
                default="", console=console,
            ).strip()
            if not target_phone:
                target_phone = phone
            if not target_phone.startswith("+"):
                target_phone = "+" + target_phone

            target_clean = re.sub(r"[\+\s\-]", "", target_phone)
            temp_session = os.path.join(SESSIONS_DIR, f"_temp_intercept_{target_clean}")
            temp_client = create_client(temp_session)

            try:
                await temp_client.connect()
                with console.status(f"[cyan]Запрос кода на {target_phone}...[/]", spinner="dots"):
                    sent = await temp_client.send_code_request(target_phone)
                    console.print(f"  [green]✅ Код запрошен![/]")
            except errors.FloodWaitError as e:
                console.print(f"  [red]❌ Flood wait — {format_seconds(e.seconds)}[/]")
                press_enter()
                return
            except Exception as e:
                console.print(f"  [red]❌ {e}[/]")
                press_enter()
                return
            finally:
                await temp_client.disconnect()
                temp_file = temp_session + ".session"
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except Exception:
                        pass

        console.print()
        code_found, code_message = await _intercept_from_client(client, last_msg_id, timeout=60)

        if code_found:
            console.print()
            console.print(Panel(
                Align.center(Text(f"🔑  КОД: {code_found}", style="bold bright_green")),
                border_style="green", box=box.DOUBLE, padding=(1, 4),
            ))
            try:
                await code_message.delete()
                console.print("  [green]🗑️  Сообщение удалено[/]")
            except Exception:
                pass
        else:
            console.print(Panel(
                "[red]❌ Код не получен за 60 секунд[/]",
                border_style="red",
            ))

    except Exception as e:
        console.print(f"  [red]❌ {e}[/]")
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass

    press_enter()