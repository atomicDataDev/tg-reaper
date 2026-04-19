"""
Mode 8: @SpamBot check
"""

import os
import re
import asyncio
import time

from rich.table import Table
from rich import box

from telethon.errors import FloodWaitError

from config import SPAMBOT_USERNAME
from utils.client import create_client, get_session_name
from ui import (
    console, print_header, print_info, print_success, print_error,
    print_warning, print_action, print_dim, print_stats_box,
    print_table, print_description_box, ask_confirm, ask_input,
    print_interrupted,
)
from utils.delays import get_delay, ask_delay
from utils.dialog import delete_dialog_for_sender


def parse_spambot_response(text: str) -> dict:
    #Parses spambot answer
    result = {"status": "unknown", "limit_date": "", "limit_reason": ""}
    text_lower = text.lower()

    free_indicators = [
        "good news", "no limits", "хорошие новости",
        "свободен", "not limited", "нет ограничений",
        "free as a bird", "никаких ограничений",
    ]
    limited_indicators = [
        "unfortunately", "к сожалению", "ограничен",
        "limited", "restrict", "can't send",
        "cannot send", "unable to send", "не можете отправлять",
    ]

    is_free = any(ind in text_lower for ind in free_indicators)
    is_limited = any(ind in text_lower for ind in limited_indicators)

    if is_free and not is_limited:
        result["status"] = "free"
    elif is_limited:
        result["status"] = "limited"
        for pattern in [
            r"until\s+(\d{1,2}\s+\w+\s+\d{4})",
            r"до\s+(\d{1,2}\s+\w+\s+\d{4})",
            r"(\d+\s*(?:hours?|час(?:а|ов)?))",
            r"(\d+\s*(?:days?|дн(?:я|ей)?))",
            r"(permanent|навсегда|бессрочно)",
        ]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["limit_date"] = match.group(1).strip()
                break

        if "spam" in text_lower or "спам" in text_lower:
            result["limit_reason"] = "Спам"
        elif "mass" in text_lower or "массов" in text_lower:
            result["limit_reason"] = "Массовая рассылка"
        elif "flood" in text_lower or "флуд" in text_lower:
            result["limit_reason"] = "Флуд"
        else:
            result["limit_reason"] = "Не указана"
    return result


async def check_spambot_single(session_path, delete_bot_dialog=False) -> dict:
    # Checks single account in @SpamBot
    client = create_client(session_path)
    name = get_session_name(session_path)
    result = {
        "session": name, "authorized": False, "status": "error",
        "response": "", "user_id": None,
        "first_name": "", "last_name": "",
        "username": "", "phone": "", "info": "",
        "limit_date": "", "limit_reason": "",
    }

    try:
        await client.connect()
        if not await client.is_user_authorized():
            print_error(f"{name} — не авторизован.")
            result["status"] = "unauthorized"
            return result

        result["authorized"] = True
        me = await client.get_me()
        result.update({
            "user_id": me.id,
            "first_name": me.first_name or "",
            "last_name": me.last_name or "",
            "username": me.username or "",
            "phone": me.phone or "",
        })

        full_name = f"{me.first_name or ''} {me.last_name or ''}".strip() or "Без имени"
        info_parts = [full_name]
        if me.username:
            info_parts.append(f"@{me.username}")
        info_parts.append(f"+{me.phone}" if me.phone else f"ID:{me.id}")
        result["info"] = " | ".join(info_parts)

        print_action(name)
        print_dim(f"Аккаунт: {result['info']}")
        print_dim("Отправляю /start @SpamBot...")

        try:
            await client.send_message(SPAMBOT_USERNAME, "/start")
        except Exception as e:
            print_error(f"{name} — не удалось написать SpamBot: {type(e).__name__}: {e}")
            return result

        response_text = ""
        for _ in range(30):
            await asyncio.sleep(0.5)
            messages = await client.get_messages(SPAMBOT_USERNAME, limit=3)
            if messages:
                for msg in messages:
                    if msg.text and msg.text != "/start" and not msg.out:
                        response_text = msg.text
                        break
                if response_text:
                    break

        if not response_text:
            print_warning(f"{name} — SpamBot не ответил (таймаут).")
            result["status"] = "timeout"
            if delete_bot_dialog:
                await delete_dialog_for_sender(client, SPAMBOT_USERNAME, name)
            return result

        result["response"] = response_text
        parsed = parse_spambot_response(response_text)
        result.update(parsed)

        if result["status"] == "free":
            print_success(f"{name} — ✅ СВОБОДЕН")
        elif result["status"] == "limited":
            print_error(f"{name} — 🚫 ОГРАНИЧЕН")
            if result["limit_reason"]:
                print_dim(f"  Причина: {result['limit_reason']}")
            if result["limit_date"]:
                print_dim(f"  До: {result['limit_date']}")
        else:
            print_warning(f"{name} — Неизвестный ответ")

        preview = response_text[:150].replace("\n", " ")
        if len(response_text) > 150:
            preview += "..."
        print_dim(f"  Ответ: {preview}")

        if delete_bot_dialog:
            await delete_dialog_for_sender(client, SPAMBOT_USERNAME, name)

    except FloodWaitError as e:
        print_warning(f"{name} — FloodWait {e.seconds} сек.")
        result["status"] = "flood"
    except Exception as e:
        print_error(f"{name} — {type(e).__name__}: {e}")
    finally:
        await client.disconnect()
    return result


async def mode_check_spambot(sessions):
    #Main @SpamBot check function
    print_header("🤖  ПРОВЕРКА @SpamBot")

    print_description_box(
        "Каждый аккаунт отправит /start боту @SpamBot\n"
        "и получит ответ о наличии ограничений.\n\n"
        "[green]✅ СВОБОДЕН[/]   — ограничений нет\n"
        "[red]🚫 ОГРАНИЧЕН[/]  — спам-ограничения\n"
        "[yellow]⏳ ТАЙМАУТ[/]    — бот не ответил\n"
        "[red]❌ ОШИБКА[/]     — не удалось проверить",
        title="Как это работает",
        style="cyan",
    )

    min_d, max_d = ask_delay()
    delete_bot = ask_input("Удалять переписку с @SpamBot после? (да/нет)", "нет").lower() in ("да", "yes", "y", "д")

    if not ask_confirm("Начать проверку?"):
        return

    results = []
    free_count = limited_count = error_count = 0

    try:
        for i, sess in enumerate(sessions):
            res = await check_spambot_single(sess, delete_bot)
            results.append(res)
            if res["status"] == "free":
                free_count += 1
            elif res["status"] == "limited":
                limited_count += 1
            else:
                error_count += 1
            if i < len(sessions) - 1:
                await get_delay(min_d, max_d)
    except KeyboardInterrupt:
        print_interrupted()

    print_stats_box({
        "✅ Свободных": free_count,
        "🚫 Ограниченных": limited_count,
        "❌ Ошибок": error_count,
        "📊 Всего": len(results),
    }, "ИТОГИ ПРОВЕРКИ @SpamBot")

    # Free
    free_accounts = [r for r in results if r["status"] == "free"]
    if free_accounts:
        table = Table(
            title="[green]✅ Свободные аккаунты[/]",
            box=box.ROUNDED, border_style="green",
            header_style="bold green",
        )
        table.add_column("Сессия", style="white")
        table.add_column("Имя", style="dim")
        table.add_column("Username", style="dim")
        for res in free_accounts:
            full_name = f"{res['first_name']} {res['last_name']}".strip() or "—"
            username = f"@{res['username']}" if res["username"] else "—"
            table.add_row(res["session"], full_name, username)
        print_table(table)

    # Limited
    limited_accounts = [r for r in results if r["status"] == "limited"]
    if limited_accounts:
        table = Table(
            title="[red]🚫 Ограниченные аккаунты[/]",
            box=box.ROUNDED, border_style="red",
            header_style="bold red",
        )
        table.add_column("Сессия", style="white")
        table.add_column("Имя", style="dim")
        table.add_column("Причина", style="yellow")
        table.add_column("До", style="dim")
        for res in limited_accounts:
            full_name = f"{res['first_name']} {res['last_name']}".strip() or "—"
            table.add_row(
                res["session"], full_name,
                res["limit_reason"] or "—",
                res["limit_date"] or "—",
            )
        print_table(table)

    # Save
    save = ask_input("Сохранить результаты в файл? (да/нет)", "нет")
    if save.lower() in ("да", "yes", "y", "д"):
        filename = f"spambot_check_{int(time.time())}.txt"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"{'=' * 60}\nРЕЗУЛЬТАТЫ ПРОВЕРКИ @SpamBot\n{'=' * 60}\n\n")
                f.write(f"Свободных: {free_count}\nОграниченных: {limited_count}\n")
                f.write(f"Ошибок: {error_count}\nВсего: {len(results)}\n\n")
                for res in results:
                    f.write(f"Сессия: {res['session']}\n  Статус: {res['status']}\n")
                    if res["first_name"]:
                        f.write(f"  Имя: {res['first_name']} {res['last_name']}\n")
                    if res["username"]:
                        f.write(f"  Username: @{res['username']}\n")
                    if res["limit_reason"]:
                        f.write(f"  Причина: {res['limit_reason']}\n")
                    if res["limit_date"]:
                        f.write(f"  До: {res['limit_date']}\n")
                    f.write("\n")
            print_success(f"Сохранено в {filename}")
        except Exception as e:
            print_error(f"Ошибка сохранения: {e}")