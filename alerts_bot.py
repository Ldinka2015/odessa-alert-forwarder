import os
import time
import requests
import telebot
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL")

SOURCE_URL = "https://t.me/s/Odessa911Odessa"

bot = telebot.TeleBot(BOT_TOKEN)

last_message_id = None

def parse_alert(text):
    if not text:
        return None

    if "🚨" in text:
        return "🚨 ТРЕВОГА"

    t = text.lower()

    if "відбій" in t or "отбой" in t:
        return "✅ ОТБОЙ"

    if "тривога" in t or "тревога" in t:
        return "🚨 ТРЕВОГА"

    return None

def get_latest_posts():
    response = requests.get(SOURCE_URL, timeout=20)
    soup = BeautifulSoup(response.text, "html.parser")

    posts = []

    for message in soup.select(".tgme_widget_message"):
        post_id = message.get("data-post")
        text_block = message.select_one(".tgme_widget_message_text")
        text = text_block.get_text(" ", strip=True) if text_block else ""

        if post_id:
            posts.append((post_id, text))

    return posts

print("Bot started. Watching public Telegram page.")

while True:
    try:
        posts = get_latest_posts()

        if posts:
            latest_id, latest_text = posts[-1]

            if last_message_id is None:
                last_message_id = latest_id
                print("Initial message:", latest_id)

            elif latest_id != last_message_id:
                last_message_id = latest_id
                parsed = parse_alert(latest_text)

                if parsed:
                    bot.send_message(
                        TARGET_CHANNEL,
                        parsed,
                        disable_web_page_preview=True
                    )
                    print("Sent:", parsed)
                else:
                    print("Skipped:", latest_text[:80])

        time.sleep(20)

    except Exception as e:
        print("Error:", e)
        time.sleep(20)
