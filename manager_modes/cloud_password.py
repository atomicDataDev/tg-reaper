"""Manager: Cloud Password Management (2FA)."""

import asyncio
import os

from telethon import errors, functions

from config import SESSIONS_DIR
from core.client_factory import create_client
from ui.console import console
from ui.panels import print_header
from ui.inputs import press_enter
from utils.parsers import parse_selection
from utils.sessions import get_session_names

from rich.table import Table
from rich.rule import Rule
from rich.prompt import Prompt
from rich import box


async def _process_single_2fa(session_name):
    session_path = os.path.join(SESSIONS_DIR, session_name)
    client = create_client(session_path)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            console.print(f"  [red]❌ {session_name} не авторизован[/]")
            return
        me = await client.get_me()

        console.print(Rule(
            f"[bold]{me.first_name}[/] [dim]({session_name})[/]",
            style="cyan",
        ))

        pwd_info = await client(functions.account.GetPasswordRequest())
        if pwd_info.has_password:
            console.print("  2FA: [green]УСТАНОВЛЕН[/]")
            console.print()
            console.print("  [yellow][1][/] Изменить   [yellow][2][/] Удалить   [dim][0] Пропуск[/]")
            action = Prompt.ask("  [cyan]Действие[/]", choices=["0", "1", "2"], default="0", console=console)

            if action == "1":
                old = Prompt.ask("  [cyan]Текущий пароль[/]", password=True, console=console).strip()
                new = Prompt.ask("  [cyan]Новый пароль[/]", password=True, console=console).strip()
                conf = Prompt.ask("  [cyan]Подтвердите[/]", password=True, console=console).strip()
                if new != conf:
                    console.print("  [red]❌ Пароли не совпадают[/]")
                else:
                    try:
                        await client.edit_2fa(current_password=old, new_password=new, hint="")
                        console.print("  [green]✅ Пароль изменён[/]")
                    except errors.PasswordHashInvalidError:
                        console.print("  [red]❌ Неверный текущий пароль[/]")
                    except Exception as e:
                        console.print(f"  [red]❌ {e}[/]")

            elif action == "2":
                old = Prompt.ask("  [cyan]Текущий пароль[/]", password=True, console=console).strip()
                try:
                    await client.edit_2fa(current_password=old, new_password=None)
                    console.print("  [green]✅ 2FA удалён[/]")
                except errors.PasswordHashInvalidError:
                    console.print("  [red]❌ Неверный пароль[/]")
                except Exception as e:
                    console.print(f"  [red]❌ {e}[/]")
        else:
            console.print("  2FA: [red]НЕ УСТАНОВЛЕН[/]")
            new = Prompt.ask("  [cyan]Новый пароль[/]", password=True, console=console).strip()
            conf = Prompt.ask("  [cyan]Подтвердите[/]", password=True, console=console).strip()
            if new != conf:
                console.print("  [red]❌ Не совпадают[/]")
            elif not new:
                console.print("  [red]❌ Пустой пароль[/]")
            else:
                try:
                    await client.edit_2fa(current_password=None, new_password=new, hint="")
                    console.print("  [green]✅ 2FA установлен[/]")
                except Exception as e:
                    console.print(f"  [red]❌ {e}[/]")
    except Exception as e:
        console.print(f"  [red]❌ {e}[/]")
    finally:
        await client.disconnect()


async def manager_cloud_password(sessions):
    print_header("🔑  УПРАВЛЕНИЕ ОБЛАЧНЫМ ПАРОЛЕМ (2FA)")

    names = get_session_names()
    if not names:
        console.print("  [red]❌ Нет сессий[/]")
        press_enter()
        return

    table = Table(box=box.ROUNDED, border_style="blue", show_header=False, padding=(0, 2))
    table.add_column("#", style="yellow bold", width=5, justify="center")
    table.add_column("Сессия", style="white")
    for i, s in enumerate(names, 1):
        table.add_row(str(i), s)
    console.print(table)
    console.print("  [dim]Номера через запятую или пусто = все[/]")
    console.print()

    choice = Prompt.ask("  [cyan]Выбор[/]", default="", console=console).strip()
    selected = parse_selection(choice, len(names))
    if selected is None:
        console.print("  [red]❌ Неверный ввод[/]")
        press_enter()
        return

    sel = [names[i] for i in selected]
    console.print(f"  [green]Выбрано: {len(sel)}[/]")
    console.print()
    console.print("  [yellow][1][/] Индивидуально   [yellow][2][/] Массово")
    mode = Prompt.ask("  [cyan]Режим[/]", choices=["1", "2"], console=console)

    if mode == "1":
        for s in sel:
            await _process_single_2fa(s)
    elif mode == "2":
        console.print()
        console.print("  [yellow][1][/] Установить/изменить   [yellow][2][/] Удалить")
        action = Prompt.ask("  [cyan]Действие[/]", choices=["1", "2"], console=console)

        if action == "1":
            old = Prompt.ask(
                "  [cyan]Текущий пароль (пусто если нет 2FA)[/]",
                default="", password=True, console=console,
            ).strip()
            new = Prompt.ask("  [cyan]Новый пароль[/]", password=True, console=console).strip()
            conf = Prompt.ask("  [cyan]Подтвердите[/]", password=True, console=console).strip()
            if new != conf:
                console.print("  [red]❌ Не совпадают[/]")
            elif not new:
                console.print("  [red]❌ Пустой пароль[/]")
            else:
                for s in sel:
                    session_path = os.path.join(SESSIONS_DIR, s)
                    client = create_client(session_path)
                    try:
                        await client.connect()
                        if not await client.is_user_authorized():
                            console.print(f"  [yellow]⚠️  {s} — не авторизован[/]")
                            continue
                        me = await client.get_me()
                        d = f"{s} ({me.first_name})"
                        pwd = await client(functions.account.GetPasswordRequest())
                        if pwd.has_password:
                            if not old:
                                console.print(f"  [yellow]⚠️  {d} — нужен старый пароль[/]")
                                continue
                            try:
                                await client.edit_2fa(current_password=old, new_password=new, hint="")
                                console.print(f"  [green]✅ {d} — изменён[/]")
                            except errors.PasswordHashInvalidError:
                                console.print(f"  [red]❌ {d} — неверный пароль[/]")
                        else:
                            try:
                                await client.edit_2fa(current_password=None, new_password=new, hint="")
                                console.print(f"  [green]✅ {d} — установлен[/]")
                            except Exception as e:
                                console.print(f"  [red]❌ {d} — {e}[/]")
                    except Exception as e:
                        console.print(f"  [red]❌ {s} — {e}[/]")
                    finally:
                        await client.disconnect()
                    await asyncio.sleep(0.5)

        elif action == "2":
            pwd = Prompt.ask("  [cyan]Текущий пароль[/]", password=True, console=console).strip()
            if not pwd:
                console.print("  [red]❌ Пароль обязателен[/]")
            else:
                for s in sel:
                    session_path = os.path.join(SESSIONS_DIR, s)
                    client = create_client(session_path)
                    try:
                        await client.connect()
                        if not await client.is_user_authorized():
                            console.print(f"  [yellow]⚠️  {s} — не авторизован[/]")
                            continue
                        me = await client.get_me()
                        d = f"{s} ({me.first_name})"
                        p = await client(functions.account.GetPasswordRequest())
                        if not p.has_password:
                            console.print(f"  [dim]ℹ️  {d} — нет 2FA[/]")
                            continue
                        try:
                            await client.edit_2fa(current_password=pwd, new_password=None)
                            console.print(f"  [green]✅ {d} — удалён[/]")
                        except errors.PasswordHashInvalidError:
                            console.print(f"  [red]❌ {d} — неверный пароль[/]")
                    except Exception as e:
                        console.print(f"  [red]❌ {s} — {e}[/]")
                    finally:
                        await client.disconnect()
                    await asyncio.sleep(0.5)

    press_enter()