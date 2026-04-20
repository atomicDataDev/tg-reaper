"""Manager: Create a new session.
Name format: DDMMYY_<phone>_session.session
The proxy is requested upon creation and saved in accounts.json."""

import os
import asyncio
from datetime import datetime

from telethon import errors

from config import SESSIONS_DIR
from core.client_factory import create_client
from core.account_store import (
    get_device_for_session, update_account_info,
)
from ui.console import console
from ui.inputs import press_enter
from ui.panels import print_header

from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich import box



def _generate_new_session_name(phone_clean: str) -> str:
    """Generates name: DDMMYY_<phone>_session
    Example: 250701_79001234567_session"""
    date_str = datetime.now().strftime("%d%m%y")
    return f"{date_str}_{phone_clean}_session"


async def manager_create_session():
    print_header("➕  СОЗДАНИЕ НОВОЙ СЕССИИ")

    phone = Prompt.ask(
        "  [cyan]Номер телефона (с +)[/]", console=console
    ).strip()
    if not phone.startswith("+"):
        phone = "+" + phone

    phone_clean = phone.replace("+", "").replace(" ", "").replace("-", "")


    # ── Selecting a name format ──
    console.print()
    new_name = _generate_new_session_name(phone_clean)
    console.print(f"  Имя файла: [bold]{new_name}.session[/]")

    session_path = os.path.join(SESSIONS_DIR, new_name)

    # Checking to see if it already exists
    if os.path.exists(session_path + ".session"):
        console.print(
            f"  [yellow]⚠️  Файл {new_name}.session уже существует![/]"
        )
        overwrite = Prompt.ask(
            "  [cyan]Перезаписать?[/]",
            choices=["да", "нет"],
            default="нет",
            console=console,
        )
        if overwrite != "да":
            press_enter()
            return

    client = create_client(session_path)
    device = get_device_for_session(session_path)

    console.print(
        f"  [dim]📱 Device: {device['device_model']} "
        f"| {device['system_version']}[/]"
    )
    console.print(f"  [dim]📦 App: {device['app_version']}[/]")
    console.print(f"  [dim]📁 Файл: {new_name}.session[/]")
    console.print()

    await client.connect()

    try:
        with console.status(
            "[cyan]Отправка кода...[/]", spinner="dots"
        ):
            await client.send_code_request(phone)

        console.print(
            f"  [green]✅ Код отправлен на[/] [bold]{phone}[/]"
        )
        console.print()

        code = Prompt.ask(
            "  [cyan]Код из Telegram[/]", console=console
        ).strip()

        try:
            await client.sign_in(phone, code)
        except errors.SessionPasswordNeededError:
            console.print("  [yellow]⚠️  Аккаунт защищён 2FA[/]")
            password = Prompt.ask(
                "  [cyan]Облачный пароль[/]",
                password=True, console=console,
            ).strip()
            await client.sign_in(password=password)

        me = await client.get_me()

        # Update accounts.json WITH PROXY
        update_account_info(
            session_path,
            user_id=me.id,
            phone=me.phone,
            username=me.username,
            first_name=me.first_name,
            last_name=me.last_name,
            status="alive",
        )

        info_table = Table(
            box=box.ROUNDED, border_style="green",
            show_header=False, padding=(0, 2),
        )
        info_table.add_column("k", style="dim")
        info_table.add_column("v", style="bold")
        info_table.add_row("Имя", me.first_name or "—")
        info_table.add_row(
            "Username",
            f"@{me.username}" if me.username else "—",
        )
        info_table.add_row("ID", str(me.id))
        info_table.add_row(
            "Файл",
            f"{SESSIONS_DIR}/{new_name}.session",
        )
        info_table.add_row("Device", device["device_model"])

        console.print()
        console.print(Panel(
            info_table,
            title="[green]✅ Вход выполнен[/]",
            border_style="green",
        ))

        # Delete the message with the code
        try:
            await asyncio.sleep(2)
            async for dialog in client.iter_dialogs():
                if dialog.entity.id == 777000:
                    async for message in client.iter_messages(
                        777000, limit=5
                    ):
                        if code in (message.text or ""):
                            await message.delete()
                            console.print(
                                "  [dim]🗑️  Сообщение с кодом "
                                "удалено[/]"
                            )
                            break
                    break
        except Exception:
            pass

    except errors.PhoneNumberInvalidError:
        console.print("  [red]❌ Неверный номер[/]")
    except errors.PhoneCodeInvalidError:
        console.print("  [red]❌ Неверный код[/]")
    except errors.FloodWaitError as e:
        from utils.parsers import format_seconds
        console.print(
            f"  [red]❌ Flood wait {format_seconds(e.seconds)}[/]"
        )
    except Exception as e:
        console.print(f"  [red]❌ Ошибка: {e}[/]")
    finally:
        await client.disconnect()

    press_enter()