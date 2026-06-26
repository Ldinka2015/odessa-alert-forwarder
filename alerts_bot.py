import os
import time
import json
import requests
from bs4 import BeautifulSoup
import telebot

BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL", "@twq_b")
SOURCE_URL = "https://t.me/s/raketna_neb"
PROCESSED_FILE = "processed_ids.json"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан")

bot = telebot.TeleBot(BOT_TOKEN)


def load_processed_ids():
    try:
        with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()
    except Exception:
        return set()


def save_processed_ids(ids):
    with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
        json.dump(list(ids)[-1000:], f, ensure_ascii=False)


processed_ids = load_processed_ids()


def parse_alerts(text):
    if not text:
        return []

    t = text.lower()
    alerts = []

    if "шахед" in t:
        alerts.append(f"🚨 ШАХЕДИ\n{text}")

    if "баллістик" in t or "балістик" in t or "баллистик" in t:
        alerts.append(f"🚨 БАЛЛИСТИКА\n{text}")

    if "міг" in t or "миг" in t or "мiг" in t:
        alerts.append(f"🚨 МИГ\n{text}")

    if "ракета" in t or "ракети" in t or "ракеты" in t:
        alerts.append(f"🚨 РАКЕТА\n{text}")

    if "цель" in t or "цели" in t or "ціль" in t or "цілі" in t:
        alerts.append(f"🚨 ЦЕЛЬ\n{text}")

    if "укри" in t or "укрыт" in t or "укрит" in t:
        alerts.append(f"🚨 В УКРЫТИЕ!!!\n{text}")

    if not alerts and ("чисто" in t or "отбой" in t or "відбій" in t):
        alerts.append("✅ ОТБОЙ")

    return alerts


def get_posts():
    response = requests.get(
        SOURCE_URL,
        timeout=20,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    posts = []

    for widget in soup.select(".tgme_widget_message_wrap"):
        message = widget.select_one(".tgme_widget_message")
        if not message:
            continue

        post_id = message.get("data-post")
        text_block = message.select_one(".tgme_widget_message_text")
        text = text_block.get_text(" ", strip=True) if text_block else ""

        if post_id and text:
            posts.append((post_id, text))

    return posts


print("Alert forwarder LIVE")

while True:
    try:
        posts = get_posts()

        new_posts = [
            (post_id, text)
            for post_id, text in posts
            if post_id not in processed_ids
        ]

        for post_id, text in new_posts:
            alerts = parse_alerts(text)

            for alert in alerts:
                try:
                    bot.send_message(TARGET_CHANNEL, alert)
                    print(f"✅ Sent: {post_id}")
                except Exception as e:
                    print(f"❌ Telegram error: {e}")

            processed_ids.add(post_id)

        if new_posts:
            save_processed_ids(processed_ids)

        time.sleep(2)

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        time.sleep(10)

    except Exception as e:
        print(f"❌ General error: {e}")
        time.sleep(5)
