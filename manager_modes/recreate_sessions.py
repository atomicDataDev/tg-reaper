"""Manager: Recreating sessions.

Works only with LIVE sessions.
Dead ones cannot be recreated - they require step 1.

Order:
1. Creates a NEW session and logs in
2. After success -- log out from OLD
3. Removes old .session file
4. File: DDMMYY_<phone>_session.session"""

import os
import asyncio
from datetime import datetime

from telethon import errors

from config import SESSIONS_DIR
from core.client_factory import create_client, get_session_name
from core.account_store import (
    get_all_accounts, get_device_for_session,
    update_account_info, remove_account,
)
from ui.console import console
from ui.panels import print_header
from ui.messages import (
    print_info, print_success, print_error,
    print_warning, print_action, print_dim,
)
from ui.inputs import ask_input, ask_confirm, press_enter
from ui.tables import print_stats_box
from utils.parsers import parse_selection, format_phone

from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box


def _generate_session_name(phone_clean: str) -> str:
    """DDMMYY_<phone>_session"""
    date_str = datetime.now().strftime("%d%m%y")
    return f"{date_str}_{phone_clean}_session"


# -- Collection of live sessions ----------------------------------------

async def _collect_alive_sessions(
    names_with_phones: list[tuple[str, str]],
) -> list[tuple[str, str, str]]:
    """Checks sessions, returns only live ones.
    Returns: [(name, phone, display_info), ...]"""
    alive = []

    for name, phone in names_with_phones:
        session_path = os.path.join(SESSIONS_DIR, name)
        if not os.path.exists(session_path + ".session"):
            continue

        client = create_client(session_path, receive_updates=False)
        try:
            await client.connect()
            if await client.is_user_authorized():
                me = await client.get_me()
                real_phone = phone or str(me.phone or "")
                if real_phone and not real_phone.startswith("+"):
                    real_phone = "+" + real_phone
                display = me.first_name or ""
                if me.username:
                    display += f" @{me.username}"
                alive.append((name, real_phone, display.strip()))
        except Exception:
            pass
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass

    return alive


# -- Log out --------------------------------------------------

async def _logout_session(session_path: str) -> bool:
    client = create_client(session_path, receive_updates=False)
    try:
        await client.connect()
        if await client.is_user_authorized():
            await client.log_out()
            print_dim("    Log out выполнен")
            return True
        else:
            print_dim("    Сессия уже не авторизована")
            return True
    except Exception as e:
        print_warning(f"    Log out не удался: {e}")
        return False
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


# -- Deleting files -----------------------------------------

def _remove_files(session_path: str):
    for ext in (".session", ".session-journal"):
        fpath = session_path + ext
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
                print_dim(
                    f"    Удален: {os.path.basename(fpath)}"
                )
            except OSError as e:
                print_warning(f"    Ошибка удаления: {e}")


# -- Creating a new session --------------------------------------------------

async def _create_session(
    old_name: str,
    phone: str,
    phone_clean: str,
) -> str | None:
    """Creates a new session and logs in.
    DO NOT touch the old one.
    Returns the path of the new session or None."""
    new_name = _generate_session_name(phone_clean)
    new_path = os.path.join(SESSIONS_DIR, new_name)

    # Unique name
    counter = 1
    while os.path.exists(new_path + ".session"):
        new_name = (
            f"{datetime.now().strftime('%d%m%y')}_"
            f"{phone_clean}_session_{counter}"
        )
        new_path = os.path.join(SESSIONS_DIR, new_name)
        counter += 1

    old_path = os.path.join(SESSIONS_DIR, old_name)
    device = get_device_for_session(old_path)

    client = create_client(new_path)

    print_action(f"  Файл: {new_name}.session")
    print_dim(
        f"    Device: {device['device_model']} | "
        f"{device['system_version']}"
    )

    try:
        await client.connect()

        # Submitting a code
        with console.status(
            f"[cyan]Отправка кода на {phone}...[/]",
            spinner="dots",
        ):
            try:
                await client.send_code_request(phone)
            except errors.FloodWaitError as e:
                from utils.parsers import format_seconds
                print_error(
                    f"  Flood wait: {format_seconds(e.seconds)}"
                )
                _remove_files(new_path)
                return None
            except errors.PhoneNumberInvalidError:
                print_error(f"  Неверный номер: {phone}")
                _remove_files(new_path)
                return None
            except errors.PhoneNumberBannedError:
                print_error(f"  Номер забанен: {phone}")
                _remove_files(new_path)
                return None
            except Exception as e:
                print_error(f"  Ошибка: {e}")
                _remove_files(new_path)
                return None

        print_success(f"  Код отправлен на {phone}")

        code = Prompt.ask(
            "  [cyan]Код из Telegram (пусто = пропуск)[/]",
            default="",
            console=console,
        ).strip()

        if not code:
            print_dim("  Пропущено")
            _remove_files(new_path)
            return None

        try:
            await client.sign_in(phone, code)
        except errors.SessionPasswordNeededError:
            print_warning("  Нужен 2FA пароль")
            password = Prompt.ask(
                "  [cyan]Облачный пароль[/]",
                password=True,
                console=console,
            ).strip()
            if not password:
                _remove_files(new_path)
                return None
            try:
                await client.sign_in(password=password)
            except errors.PasswordHashInvalidError:
                print_error("  Неверный пароль")
                _remove_files(new_path)
                return None
        except errors.PhoneCodeInvalidError:
            print_error("  Неверный код")
            _remove_files(new_path)
            return None
        except errors.PhoneCodeExpiredError:
            print_error("  Код истек")
            _remove_files(new_path)
            return None

        me = await client.get_me()
        print_success(
            f"  Вход OK: {me.first_name} "
            f"(@{me.username or '-'}) ID:{me.id}"
        )

        update_account_info(
            new_path,
            user_id=me.id,
            phone=me.phone,
            username=me.username,
            first_name=me.first_name,
            last_name=me.last_name,
            status="alive",
        )

        # Deleting a message with a code
        try:
            await asyncio.sleep(2)
            async for dialog in client.iter_dialogs():
                if dialog.entity.id == 777000:
                    async for msg in client.iter_messages(
                        777000, limit=5
                    ):
                        if code in (msg.text or ""):
                            await msg.delete()
                            print_dim("    Код удален из чата")
                            break
                    break
        except Exception:
            pass

        return new_path

    except Exception as e:
        print_error(f"  Ошибка: {type(e).__name__}: {e}")
        _remove_files(new_path)
        return None
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


# -- Replacing one session ----------------------------------------

async def _replace_session(name: str, phone: str) -> dict:
    """1. New session + authorization
    2. Log out old
    3. Removing old"""
    old_path = os.path.join(SESSIONS_DIR, name)
    phone_clean = (
        phone.replace("+", "")
        .replace(" ", "")
        .replace("-", "")
    )

    result = {
        "success": False,
        "old_name": name,
        "new_name": None,
    }

    # Number
    if not phone:
        print_warning(f"  Нет номера для {name}")
        phone = Prompt.ask(
            "  [cyan]Номер (с +, пусто = пропуск)[/]",
            default="",
            console=console,
        ).strip()
        if not phone:
            print_dim("  Пропущено")
            return result
        if not phone.startswith("+"):
            phone = "+" + phone
        phone_clean = (
            phone.replace("+", "")
            .replace(" ", "")
            .replace("-", "")
        )

    # Step 1
    console.print()
    print_action("  [1/3] Создание новой сессии...")

    new_path = await _create_session(name, phone, phone_clean)

    if not new_path:
        print_error(
            f"  Новая сессия не создана. "
            f"Старая [{name}] не тронута."
        )
        return result

    new_name = os.path.basename(new_path).replace(".session", "")

    # Step 2
    print_action("  [2/3] Выход из старой сессии...")
    await _logout_session(old_path)

    # Step 3
    print_action("  [3/3] Удаление старого файла...")
    _remove_files(old_path)

    try:
        remove_account(old_path, delete_session_file=False)
        print_dim("    Старая запись удалена из accounts.json")
    except Exception:
        pass

    result["new_name"] = new_name
    result["success"] = True
    print_success(f"  Готово: {name} -> {new_name}.session")

    return result


# -- Main function -----------------------------------------

async def manager_recreate_sessions(sessions):
    print_header("ПЕРЕСОЗДАНИЕ СЕССИЙ")

    # Description
    desc = Table(
        show_header=False,
        box=box.SIMPLE,
        padding=(0, 1),
        show_edge=False,
    )
    desc.add_column(style="dim")
    desc.add_row("Работает только с ЖИВЫМИ сессиями.")
    desc.add_row("Мертвые пересоздать нельзя (пункт 1).")
    desc.add_row("")
    desc.add_row("Порядок:")
    desc.add_row("  1. Создает новую сессию + авторизация")
    desc.add_row("  2. Log out из старой сессии")
    desc.add_row("  3. Удаляет старый файл")
    desc.add_row("  4. Device переносится")
    desc.add_row("  5. Файл: DDMMYY_phone_session.session")
    desc.add_row("")
    desc.add_row(
        "[green]Старая удаляется только после "
        "успешной авторизации в новой.[/]"
    )
    desc.add_row("[yellow]Для каждого аккаунта нужен код.[/]")

    console.print(
        Panel(desc, border_style="cyan", title="Описание")
    )
    console.print()

    # Collection of accounts
    accounts = get_all_accounts()

    if not accounts:
        print_error("Нет аккаунтов в accounts.json")
        print_info("Выполните проверку сессий (пункт 2)")
        press_enter()
        return

    names_with_phones = []
    for key, acc in accounts.items():
        phone = acc.get("phone") or ""
        if phone and not phone.startswith("+"):
            phone = "+" + phone
        names_with_phones.append((key, phone))

    console.print(
        f"  Всего в базе: [bold]{len(names_with_phones)}[/]"
    )
    console.print()

    # Examination
    with console.status(
        "[cyan]Проверяю сессии...[/]", spinner="dots"
    ):
        alive = await _collect_alive_sessions(names_with_phones)

    dead_count = len(names_with_phones) - len(alive)

    if not alive:
        print_error("Нет живых сессий для пересоздания.")
        if dead_count > 0:
            print_info(
                f"Мертвых сессий: {dead_count}. "
                f"Создайте новые через пункт 1."
            )
        press_enter()
        return

    # Table of the living
    table = Table(
        title="[bold cyan]Живые сессии[/]",
        box=box.ROUNDED,
        border_style="cyan",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column(
        "#", style="yellow bold", width=4, justify="center"
    )
    table.add_column("Сессия", style="white", min_width=22)
    table.add_column("Телефон", style="bright_white", min_width=16)
    table.add_column("Имя", style="dim", min_width=16)

    for i, (name, phone, display) in enumerate(alive, 1):
        table.add_row(str(i), name, format_phone(phone), display)

    console.print(table)
    console.print()
    console.print(
        f"  Живых: [bold green]{len(alive)}[/]"
    )
    if dead_count > 0:
        console.print(
            f"  Мертвых (скрыты): [dim red]{dead_count}[/]"
        )
    console.print()

    # Choice
    menu = Table(
        show_header=False,
        box=box.SIMPLE,
        padding=(0, 2),
        show_edge=False,
    )
    menu.add_column("key", style="yellow bold", width=4)
    menu.add_column("desc", style="white")
    menu.add_row("A", "Пересоздать ВСЕ живые")
    menu.add_row("N", "Выбрать по номерам (через запятую)")
    menu.add_row("0", "Отмена")
    console.print(menu)
    console.print()

    choice = Prompt.ask(
        "  [cyan]Выбор[/]",
        default="0",
        console=console,
    ).strip().upper()

    if choice == "0":
        press_enter()
        return

    selected_indices = []

    if choice == "A":
        selected_indices = list(range(len(alive)))
    else:
        parsed = parse_selection(choice, len(alive))
        if parsed is None:
            print_error("Неверный ввод")
            press_enter()
            return
        selected_indices = parsed

    if not selected_indices:
        print_error("Ничего не выбрано")
        press_enter()
        return

    selected = [alive[i] for i in selected_indices]

    # Confirmation
    console.print()
    console.print(
        f"  Выбрано: [bold]{len(selected)}[/]"
    )

    confirm_table = Table(
        show_header=False,
        box=box.SIMPLE,
        padding=(0, 1),
        show_edge=False,
    )
    confirm_table.add_column(style="green", width=3)
    confirm_table.add_column(style="white")
    confirm_table.add_column(style="dim")

    for name, phone, display in selected:
        confirm_table.add_row(
            ">", name, format_phone(phone)
        )
    console.print(confirm_table)

    console.print()
    console.print(
        "  [dim]Порядок: новая сессия -> авторизация -> "
        "log out старой -> удаление[/]"
    )
    console.print()

    if not ask_confirm(
        f"Пересоздать {len(selected)} сессий?"
    ):
        press_enter()
        return

    # -- Processing --
    console.print()
    ok = fail = skip = 0

    for i, (name, phone, display) in enumerate(selected, 1):
        console.print()

        header = Table(
            show_header=False,
            box=box.HEAVY,
            border_style="cyan",
            padding=(0, 2),
            min_width=50,
        )
        header.add_column(style="bold white")
        header.add_row(
            f"[{i}/{len(selected)}] {name}"
        )
        console.print(header)

        if phone:
            console.print(f"  Телефон: {format_phone(phone)}")
        if display:
            console.print(f"  Аккаунт: {display}")

        console.print()

        action = Prompt.ask(
            "  [cyan]Пересоздать?[/] "
            "[dim](y/n/s=пропустить остальные)[/]",
            choices=["y", "n", "s"],
            default="y",
            console=console,
        )

        if action == "s":
            remaining = len(selected) - i
            skip += remaining
            print_dim("  Пропуск оставшихся")
            break
        elif action == "n":
            skip += 1
            print_dim("  Пропущено")
            continue

        try:
            result = await _replace_session(name, phone)
            if result["success"]:
                ok += 1
            else:
                fail += 1
        except KeyboardInterrupt:
            console.print("\n  [yellow]Прервано[/]")
            remaining = len(selected) - i
            skip += remaining
            break
        except Exception as e:
            print_error(f"  Ошибка: {e}")
            fail += 1

        if i < len(selected):
            await asyncio.sleep(1)

    # Results
    console.print()

    stats_table = Table(
        title="[bold cyan]РЕЗУЛЬТАТЫ[/]",
        box=box.ROUNDED,
        border_style="cyan",
        show_header=False,
        padding=(0, 2),
    )
    stats_table.add_column(style="bold", min_width=20)
    stats_table.add_column(style="white", justify="right", width=6)
    stats_table.add_row("[green]Пересоздано[/]", str(ok))
    stats_table.add_row("[red]Ошибок[/]", str(fail))
    stats_table.add_row("[yellow]Пропущено[/]", str(skip))
    stats_table.add_row("[cyan]Всего выбрано[/]", str(len(selected)))

    console.print(stats_table)

    press_enter()