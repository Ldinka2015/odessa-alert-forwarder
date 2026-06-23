import os
import telebot
from telethon import TelegramClient, events
from telethon.sessions import StringSession

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL")

SOURCE_CHANNEL = "Odessa911Odessa"

bot = telebot.TeleBot(BOT_TOKEN)
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

KEYWORDS = [
    "тревога",
    "воздушная тревога",
    "повітряна тривога",
    "тривога",
    "отбой",
    "відбій",
    "бпла",
    "шахед",
    "shahed",
    "дрон",
    "дрони",
    "ракета",
    "ракеты",
    "крилата",
    "крылатая",
    "баллистика",
    "балістика",
    "каб",
]

def is_relevant(text):
    if not text:
        return False

    t = text.lower()
    return any(word in t for word in KEYWORDS)

def format_message(text):
    t = text.lower()

    if any(x in t for x in ["отбой", "відбій"]):
        prefix = "✅ ОТБОЙ"
    elif any(x in t for x in ["тревога", "воздушная тревога", "повітряна тривога", "тривога"]):
        prefix = "🚨 ТРЕВОГА"
    else:
        prefix = "⚠️ УГРОЗА"

    clean_text = text.strip()

    if clean_text.startswith(prefix):
        return clean_text

    return f"{prefix}\n\n{clean_text}"

@client.on(events.NewMessage(chats=SOURCE_CHANNEL))
async def handler(event):
    text = event.raw_text

    # Если текста нет — значит это картинка/видео/карта без текста. Игнорируем.
    if not text:
        return

    # Берём только тревоги, отбой и сообщения о том, что летит.
    if not is_relevant(text):
        return

    message = format_message(text)

    bot.send_message(
        TARGET_CHANNEL,
        message,
        disable_web_page_preview=True
    )

async def main():
    print("Alerts forwarder started")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
