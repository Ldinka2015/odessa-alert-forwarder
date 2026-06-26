import os
import time
import json
import re
import requests
from bs4 import BeautifulSoup
import telebot

BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL", "@twq_b")
SOURCE_URL = "https://t.me/s/raketna_neb"
STATE_FILE = "processed_ids.json"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан")

bot = telebot.TeleBot(BOT_TOKEN)


def load_processed_ids():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_processed_ids(ids):
    ids = list(ids)[-1000:]
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(ids, f, ensure_ascii=False)


processed_ids = load_processed_ids()


def is_useful_alert(text):
    t = text.lower()

    keywords = [
        "шахед", "шахеди", "бпла",
        "ракета", "ракети", "ракеты",
        "баліст", "балліст", "баллист",
        "міг", "миг", "мiг",
        "пуск", "пуски",
        "летить", "летять", "курс", "напрям", "направлен",
        "ціль", "цілі", "цель", "цели",
        "укриття", "укрытие", "укрит", "укрыт",
        "тривога", "тревога",
        "відбій", "отбой", "чисто",
    ]

    return any(word in t for word in keywords)


def make_alert(text):
    t = text.lower()

    if "відбій" in t or "отбой" in t or "чисто" in t:
        return f"✅ ОТБОЙ\n{text}"

    if "укрит" in t or "укрыт" in t:
        return f"🚨 В УКРЫТИЕ\n{text}"

    if "шахед" in t or "бпла" in t:
        return f"🚨 ШАХЕДЫ / БПЛА\n{text}"

    if "баліст" in t or "балліст" in t or "баллист" in t:
        return f"🚨 БАЛЛИСТИКА\n{text}"

    if "міг" in t or "миг" in t or "мiг" in t:
        return f"🚨 МИГ\n{text}"

    if "ракета" in t or "ракети" in t or "ракеты" in t:
        return f"🚨 РАКЕТЫ\n{text}"

    if "ціль" in t or "цілі" in t or "цель" in t or "цели" in t:
        return f"🚨 ЦЕЛЬ\n{text}"

    if "летить" in t or "летять" in t or "курс" in t or "напрям" in t or "направлен" in t:
        return f"🚨 НАПРАВЛЕНИЕ / КУРС\n{text}"

    if "тривога" in t or "тревога" in t:
        return f"🚨 ТРЕВОГА\n{text}"

    return None


def get_posts():
    response = requests.get(
        SOURCE_URL,
        timeout=20,
        headers={"User-Agent": "Mozilla/5.0"}
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
            text = re.sub(r"\s+", " ", text).strip()
            posts.append((post_id, text))

    return posts


print("Alert forwarder LIVE")

# ВАЖНО:
# Первый запуск: бот только запоминает старые публикации и ничего не отправляет.
if not processed_ids:
    try:
        posts = get_posts()
        for post_id, _ in posts:
            processed_ids.add(post_id)

        save_processed_ids(processed_ids)
        print(f"Initial sync complete. Saved {len(posts)} old posts. Nothing sent.")
    except Exception as e:
        print(f"Initial sync error: {e}")


while True:
    try:
        posts = get_posts()

        new_posts = [
            (post_id, text)
            for post_id, text in posts
            if post_id not in processed_ids
        ]

        for post_id, text in new_posts:
            processed_ids.add(post_id)

            if not is_useful_alert(text):
                print(f"Skipped non-alert: {post_id}")
                continue

            alert = make_alert(text)

            if alert:
                bot.send_message(TARGET_CHANNEL, alert)
                print(f"✅ Sent: {post_id}")
            else:
                print(f"Skipped: {post_id}")

        if new_posts:
            save_processed_ids(processed_ids)

        time.sleep(2)

    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        time.sleep(10)

    except Exception as e:
        print(f"General error: {e}")
        time.sleep(5)
