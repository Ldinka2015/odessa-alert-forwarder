import os
import re
import sqlite3
import hashlib
from telethon import TelegramClient, events
from telethon.sessions import StringSession

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL")

SOURCE_CHANNELS = [
    "odessa_inform",
]

THREAT_WORDS = [
    "шахед", "shahed", "бпла", "бпілот", "розвід",
    "ракета", "ракети", "крилат", "баліст", "баллист",
    "тривога", "тревога", "відбій", "отбой",
    "пво", "ппо", "чисто", "загроза", "угроза",
    "курс", "напрям", "пуск", "міг", "миг",
    "х-69", "калібр"
]

BLOCK_WORDS = [
    "реклама", "підписатись", "підписатися",
    "донат", "збір", "чат", "підтримати"
]

conn = sqlite3.connect("forwarded.db")
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS forwarded (
    hash TEXT PRIMARY KEY
)
""")
conn.commit()


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_relevant(text: str) -> bool:
    if not text:
        return False

    clean = normalize_text(text)

    if any(word in clean for word in BLOCK_WORDS):
        return False

    return any(word in clean for word in THREAT_WORDS)


def already_forwarded(text: str) -> bool:
    h = hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()

    cur.execute("SELECT 1 FROM forwarded WHERE hash = ?", (h,))
    if cur.fetchone():
        return True

    cur.execute("INSERT INTO forwarded(hash) VALUES (?)", (h,))
    conn.commit()
    return False


user_client = TelegramClient(
    StringSession(SESSION_STRING),
    API_ID,
    API_HASH
)

bot_client = TelegramClient(
    "bot_session",
    API_ID,
    API_HASH
)


@user_client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    text = event.message.message or ""

    if not text.strip():
        return

    if not is_relevant(text):
        return

    if already_forwarded(text):
        return

    source = event.chat.username or event.chat.title

    message = (
        f"{text.strip()}\n\n"
        f"Джерело: @{source}"
    )

    await bot_client.send_message(TARGET_CHANNEL, message)


async def main():
    print("Forwarder started")
    await user_client.connect()

    if not await user_client.is_user_authorized():
        raise RuntimeError("SESSION_STRING is invalid or missing")

    await user_client.run_until_disconnected()


user_client.loop.run_until_complete(main())
