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

def parse_alert(text):
    if not text:
        return None

    t = text.lower()

    is_alarm = any(x in t for x in [
        "тревога",
        "воздушная тревога",
        "повітряна тривога",
        "тривога"
    ])

    is_clear = any(x in t for x in [
        "отбой",
        "відбій",
        "відбій тривоги"
    ])

    threats = []

    if any(x in t for x in ["бпла", "шахед", "shahed", "дрон", "дрони"]):
        threats.append("БПЛА")

    if any(x in t for x in ["ракета", "ракеты", "крилата", "крылатая"]):
        threats.append("ракета")

    if any(x in t for x in ["баллистика", "балістика", "балл"]):
        threats.append("баллистика")

    if "каб" in t:
        threats.append("КАБ")

    if is_alarm:
        status = "🚨 ТРЕВОГА"
    elif is_clear:
        status = "✅ ОТБОЙ"
    elif threats:
        status = "⚠️ УГРОЗА"
    else:
        return None

    result = status

    if threats:
        result += " | " + ", ".join(threats)

    return result

@client.on(events.NewMessage(chats=SOURCE_CHANNEL))
async def handler(event):
    text = event.raw_text

    if not text:
        return

    parsed = parse_alert(text)

    if parsed:
        bot.send_message(
            TARGET_CHANNEL,
            parsed,
            disable_web_page_preview=True
        )

async def main():
    print("Alerts forwarder started")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
