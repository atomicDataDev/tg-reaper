"""Manager: Get the entry code by number."""

import os
import re
import asyncio

from telethon import errors

from config import SESSIONS_DIR
from core.client_factory import create_client
from ui.console import console
from ui.panels import print_header
from ui.inputs import press_enter
from utils.parsers import format_seconds
from utils.sessions import get_session_names

from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box


async def manager_get_login_code(sessions):
    print_header("📲  ПОЛУЧИТЬ КОД ВХОДА ПО НОМЕРУ")

    phone = Prompt.ask("  [cyan]Номер телефона (с +)[/]", console=console).strip()
    if not phone.startswith("+"):
        phone = "+" + phone
    phone_clean = phone.replace("+", "").replace(" ", "").replace("-", "")

    names = get_session_names()
    has_session = phone_clean in names

    temp_session = os.path.join(SESSIONS_DIR, f"_temp_{phone_clean}")
    client = create_client(temp_session)
    catcher_client = None

    try:
        await client.connect()

        with console.status(f"[cyan]Запрос кода на {phone}...[/]", spinner="dots"):
            try:
                sent = await client.send_code_request(phone)
            except errors.FloodWaitError as e:
                console.print(f"  [red]❌ Flood wait — {format_seconds(e.seconds)}[/]")
                press_enter()
                return
            except errors.PhoneNumberInvalidError:
                console.print("  [red]❌ Неверный номер[/]")
                press_enter()
                return
            except Exception as e:
                console.print(f"  [red]❌ {e}[/]")
                press_enter()
                return

        console.print(f"  [green]✅ Код отправлен![/] Тип: [dim]{sent.type.__class__.__name__}[/]")

        if has_session:
            console.print(f"  [cyan]🔍 Сессия {phone_clean} найдена — перехват...[/]")
            catcher_path = os.path.join(SESSIONS_DIR, phone_clean)
            catcher_client = create_client(catcher_path)
            try:
                await catcher_client.connect()
                if await catcher_client.is_user_authorized():
                    code_found = None
                    with Progress(
                        SpinnerColumn(), TextColumn("[cyan]Ожидаю...[/]"),
                        BarColumn(bar_width=30),
                        TextColumn("[dim]{task.completed}с / 30с[/]"),
                        console=console,
                    ) as progress:
                        task = progress.add_task("wait", total=30)
                        for attempt in range(15):
                            await asyncio.sleep(2)
                            progress.update(task, completed=(attempt + 1) * 2)
                            try:
                                async for message in catcher_client.iter_messages(777000, limit=3):
                                    codes = re.findall(r'\b(\d{5,6})\b', message.text or "")
                                    if codes:
                                        code_found = codes[0]
                                        try:
                                            await message.delete()
                                        except Exception:
                                            pass
                                        break
                            except Exception:
                                pass
                            if code_found:
                                break

                    if code_found:
                        console.print()
                        console.print(Panel(
                            Align.center(Text(f"🔑  КОД: {code_found}", style="bold green on black")),
                            border_style="green", box=box.DOUBLE, padding=(1, 6),
                        ))
                    else:
                        console.print("  [yellow]⚠️  Код не перехвачен автоматически[/]")
            except Exception as e:
                console.print(f"  [yellow]⚠️  Ошибка перехвата: {e}[/]")
            finally:
                await catcher_client.disconnect()
                catcher_client = None
        else:
            console.print("  [dim]ℹ️  Сессия не найдена — код придёт на устройство[/]")

        console.print()
        action = Prompt.ask("  Ввести код и создать сессию?", choices=["да", "нет"], default="нет", console=console)
        if action == "да":
            code = Prompt.ask("  [cyan]Код[/]", console=console).strip()
            if code:
                try:
                    try:
                        await client.sign_in(phone, code)
                    except errors.SessionPasswordNeededError:
                        pwd = Prompt.ask("  [cyan]Облачный пароль[/]", password=True, console=console).strip()
                        await client.sign_in(password=pwd)
                    me = await client.get_me()
                    console.print(f"  [green]✅ Вход: {me.first_name} (@{me.username}) ID:{me.id}[/]")

                    from core.account_store import update_account_info
                    final_path = os.path.join(SESSIONS_DIR, phone_clean)
                    update_account_info(
                        final_path, user_id=me.id, phone=me.phone,
                        username=me.username, first_name=me.first_name,
                        last_name=me.last_name, status="alive",
                    )

                    # Removing the code
                    try:
                        await asyncio.sleep(1)
                        async for dialog in client.iter_dialogs():
                            if dialog.entity.id == 777000:
                                async for message in client.iter_messages(777000, limit=5):
                                    if code in (message.text or ""):
                                        await message.delete()
                                        break
                                break
                    except Exception:
                        pass

                    await client.disconnect()

                    temp_file = temp_session + ".session"
                    final_file = os.path.join(SESSIONS_DIR, phone_clean + ".session")
                    if os.path.exists(final_file):
                        os.remove(final_file)
                    if os.path.exists(temp_file):
                        os.rename(temp_file, final_file)
                    console.print(f"  [green]📁 {SESSIONS_DIR}/{phone_clean}.session[/]")
                    press_enter()
                    return
                except errors.PhoneCodeInvalidError:
                    console.print("  [red]❌ Неверный код[/]")
                except Exception as e:
                    console.print(f"  [red]❌ {e}[/]")

    except Exception as e:
        console.print(f"  [red]❌ {e}[/]")
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass
        if catcher_client:
            try:
                await catcher_client.disconnect()
            except Exception:
                pass
        temp_file = temp_session + ".session"
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass

    press_enter()