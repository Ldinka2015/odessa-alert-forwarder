import os
import telebot

BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL")

bot = telebot.TeleBot(BOT_TOKEN)

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

@bot.message_handler(content_types=["text"])
def handle_message(message):
    parsed = parse_alert(message.text)

    if parsed:
        bot.send_message(
            TARGET_CHANNEL,
            parsed,
            disable_web_page_preview=True
        )

print("Bot started")
bot.infinity_polling()
