"""Manager: Change Login Email."""

import asyncio
import os

from config import SESSIONS_DIR
from core.client_factory import create_client
from core.raw_tl import (
    RawSendVerifyEmailCode,
    RawEmailVerifyPurposeLoginChange,
    RawEmailVerificationCode,
    RawVerifyEmail,
)
from ui.console import console
from ui.panels import print_header
from ui.inputs import press_enter
from utils.parsers import parse_selection, format_phone
from utils.sessions import get_session_names

from telethon import functions
from rich.table import Table
from rich.prompt import Prompt
from rich import box


async def _send_login_email_code(client, email):
    return await client(RawSendVerifyEmailCode(
        purpose=RawEmailVerifyPurposeLoginChange(), email=email,
    ))


async def _verify_login_email(client, code):
    return await client(RawVerifyEmail(
        purpose=RawEmailVerifyPurposeLoginChange(),
        verification=RawEmailVerificationCode(code=code),
    ))


async def _change_single(client, session_name, me, new_email):
    display = f"{session_name} ({me.first_name})"
    try:
        result = await _send_login_email_code(client, new_email)
        email_pattern = getattr(result, 'email_pattern', new_email)
        code_length = getattr(result, 'length', 0)

        console.print(f"  [cyan]📧 {display}[/]")
        console.print(f"     Код → [bold]{email_pattern}[/]", end="")
        if code_length:
            console.print(f"  [dim](длина: {code_length})[/]")
        else:
            console.print()

        email_code = Prompt.ask(
            "     [cyan]Код (пусто = пропуск)[/]",
            default="", console=console,
        ).strip()
        if not email_code:
            console.print("     [dim]⏭️  Пропуск[/]")
            return False

        vr = await _verify_login_email(client, email_code)
        verified = getattr(vr, 'email', new_email)
        console.print(f"     [green]✅ Login Email → {verified}[/]")
        return True
    except Exception as e:
        err = str(e).upper()
        if "EMAIL_INVALID" in err:
            console.print(f"  [red]❌ {display} — неверный email[/]")
        elif "FLOOD" in err:
            console.print(f"  [red]❌ {display} — flood wait[/]")
        elif "CODE_INVALID" in err or "CODE_EXPIRED" in err:
            console.print(f"     [red]❌ Неверный/просроченный код[/]")
        else:
            console.print(f"  [red]❌ {display} — {e}[/]")
        return False


async def _process_email_for_sessions(selected_names, new_email):
    success = fail = 0
    for session_name in selected_names:
        session_path = os.path.join(SESSIONS_DIR, session_name)
        client = create_client(session_path)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                console.print(f"  [yellow]⚠️  {session_name} — не авторизован[/]")
                fail += 1
                continue
            me = await client.get_me()
            if await _change_single(client, session_name, me, new_email):
                success += 1
            else:
                fail += 1
        except Exception as e:
            console.print(f"  [red]❌ {session_name} — {e}[/]")
            fail += 1
        finally:
            await client.disconnect()
        await asyncio.sleep(1)

    summary = Table(show_header=False, box=box.ROUNDED, border_style="cyan", padding=(0, 2))
    summary.add_column("", style="bold")
    summary.add_column("")
    summary.add_row("[green]✅ Успешно[/]", str(success))
    summary.add_row("[red]❌ Ошибок[/]", str(fail))
    console.print()
    console.print(summary)


async def manager_login_email_all(sessions):
    print_header("📧  СМЕНА EMAIL LOGIN — ВСЕ СЕССИИ")

    names = get_session_names()
    if not names:
        console.print("  [red]❌ Нет сессий[/]")
        press_enter()
        return

    console.print(f"  Сессий: [bold]{len(names)}[/]")
    new_email = Prompt.ask("  [cyan]Email[/]", console=console).strip()
    if not new_email or "@" not in new_email:
        console.print("  [red]❌ Неверный email[/]")
        press_enter()
        return

    confirm = Prompt.ask(
        f"  Установить [bold]{new_email}[/] для [bold]{len(names)}[/] сессий?",
        choices=["да", "нет"], default="нет", console=console,
    )
    if confirm != "да":
        press_enter()
        return

    await _process_email_for_sessions(names, new_email)
    press_enter()


async def manager_login_email_selected(sessions):
    print_header("📧  СМЕНА EMAIL LOGIN — ВЫБОР СЕССИЙ")

    names = get_session_names()
    if not names:
        console.print("  [red]❌ Нет сессий[/]")
        press_enter()
        return

    table = Table(box=box.ROUNDED, border_style="blue", header_style="bold cyan", padding=(0, 1))
    table.add_column("#", style="yellow bold", width=4, justify="center")
    table.add_column("Сессия", style="white", min_width=16)

    with console.status("[cyan]Загрузка...[/]", spinner="dots"):
        for i, s in enumerate(names, 1):
            session_path = os.path.join(SESSIONS_DIR, s)
            client = create_client(session_path, receive_updates=False)
            try:
                await client.connect()
                if await client.is_user_authorized():
                    me = await client.get_me()
                    phone = format_phone(me.phone)
                    table.add_row(str(i), f"{s} ({phone})")
                else:
                    table.add_row(str(i), f"{s} [red](НЕ АВТОРИЗОВАН)[/]")
            except Exception:
                table.add_row(str(i), f"{s} [red](ОШИБКА)[/]")
            finally:
                await client.disconnect()

    console.print(table)
    console.print("  [dim]Номера через запятую или пусто = все[/]")

    choice = Prompt.ask("  [cyan]Выбор[/]", default="", console=console).strip()
    selected = parse_selection(choice, len(names))
    if selected is None:
        console.print("  [red]❌ Неверный ввод[/]")
        press_enter()
        return

    sel = [names[i] for i in selected]
    new_email = Prompt.ask("  [cyan]Email[/]", console=console).strip()
    if not new_email or "@" not in new_email:
        console.print("  [red]❌ Неверный email[/]")
        press_enter()
        return

    await _process_email_for_sessions(sel, new_email)
    press_enter()