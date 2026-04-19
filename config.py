"""
All TG REAPER settings.
Loaded from environment variables for security.
"""

import os
from dotenv import load_dotenv
from telethon.tl.types import (
    InputReportReasonSpam, InputReportReasonViolence,
    InputReportReasonPornography, InputReportReasonChildAbuse,
    InputReportReasonOther, InputReportReasonCopyright,
    InputReportReasonFake, InputReportReasonGeoIrrelevant,
    InputReportReasonIllegalDrugs, InputReportReasonPersonalDetails,
)

# Load variables from .env file
load_dotenv()

# -- Telegram API ----------------------------------------------
# Cast to int for API_ID as env variables are always strings
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")

# -- Paths -----------------------------------------------------
SESSIONS_DIR = os.getenv("SESSIONS_DIR", "sessions")

# -- Messaging -------------------------------------------------
DM_MESSAGES = [
    "Привет! Как дела?",
    "Здравствуй! Хотел написать тебе.",
    "Привет, давно не общались!",
]

COMMENT_MESSAGES = [
    "Отличный пост! 🔥",
    "Очень интересно, спасибо!",
    "Полезная информация 👍",
    "Круто, продолжай в том же духе!",
    "Согласен, хорошая тема!",
    "Топ контент как всегда!",
    "Спасибо за материал!",
    "Интересная точка зрения 🤔",
]

SECRET_CHAT_MESSAGES = [
    "Привет! Это секретный чат 🔐",
    "Здравствуй! Пишу в секретном чате.",
    "Приватное сообщение для тебя!",
]

# Mode: "sequential" or "random"
MESSAGE_MODE = os.getenv("MESSAGE_MODE", "sequential")

# -- Report Reasons ---------------------------------------------
REPORT_REASONS = {
    "1":  ("Спам",                           InputReportReasonSpam),
    "2":  ("Насилие",                        InputReportReasonViolence),
    "3":  ("Порнография",                    InputReportReasonPornography),
    "4":  ("Жестокое обращение с детьми",    InputReportReasonChildAbuse),
    "5":  ("Нарушение авторских прав",       InputReportReasonCopyright),
    "6":  ("Фейковый аккаунт / канал",      InputReportReasonFake),
    "7":  ("Наркотики",                      InputReportReasonIllegalDrugs),
    "8":  ("Публикация личных данных",       InputReportReasonPersonalDetails),
    "9":  ("Нерелевантная геолокация",       InputReportReasonGeoIrrelevant),
    "10": ("Другое (свой текст)",            InputReportReasonOther),
}

# -- TTL secret chats ----------------------------------------
TTL_OPTIONS = {
    "1": ("Без автоудаления", 0),
    "2": ("1 секунда",        1),
    "3": ("5 секунд",         5),
    "4": ("10 секунд",        10),
    "5": ("30 секунд",        30),
    "6": ("1 минута",         60),
    "7": ("1 час",            3600),
    "8": ("1 день",           86400),
    "9": ("1 неделя",         604800),
}

# -- TTL normal chats ------------------------------------------
CHAT_TTL_OPTIONS = {
    "1": ("Выключить автоудаление", 0),
    "2": ("1 день",                 86400),
    "3": ("7 дней",                 604800),
    "4": ("31 день",                2678400),
}

# -- TTL cycle for maximum effect ------------------------
CHAT_TTL_CYCLE = [
    (86400,   "1 день"),
    (604800,  "7 дней"),
    (2678400, "31 день"),
    (0,       "выкл"),
    (86400,   "1 день"),
    (0,       "выкл"),
    (604800,  "7 дней"),
    (0,       "выкл"),
]

# -- SpamBot ---------------------------------------------------
SPAMBOT_USERNAME = "SpamBot"
