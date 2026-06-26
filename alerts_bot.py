import os
import time
import json
import re
import html
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from PIL import Image
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


def get_image_url(widget):
    photo = widget.select_one(".tgme_widget_message_photo_wrap")
    if not photo:
        return None

    style = photo.get("style", "")
    match = re.search(r"url\(['\"]?(.*?)['\"]?\)", style)

    if not match:
        return None

    return html.unescape(match.group(1))


def classify_image_by_color(image_url):
    try:
        response = requests.get(
            image_url,
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()

        img = Image.open(BytesIO(response.content)).convert("RGB")
        img = img.resize((80, 80))

        red_score = 0
        green_score = 0

        for r, g, b in img.getdata():
            if r > 150 and g < 120 and b < 120:
                red_score += 1
            if g > 120 and r < 120 and b < 120:
                green_score += 1

        if red_score > 80 and red_score > green_score * 1.5:
            return "alarm"

        if green_score > 80 and green_score > red_score * 1.5:
            return "clear"

        return None

    except Exception as e:
        print(f"Image error: {e}")
        return None


def make_text_alert(text):
    if not text:
        return None

    t = text.lower()

    if "відбій" in t or "отбой" in t or "чисто" in t:
        return f"✅ ОТБОЙ\n{text}"

    if "повітряна тривога" in t or "тривога" in t or "тревога" in t:
        return f"🚨 ПОВІТРЯНА ТРИВОГА\n{text}"

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

    if (
        "летить" in t
        or "летять" in t
        or "курс" in t
        or "напрям" in t
        or "направлен" in t
        or "пуск" in t
        or "пуски" in t
    ):
        return f"🚨 НАПРАВЛЕНИЕ / КУРС\n{text}"

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
        if not post_id:
            continue

        text_block = message.select_one(".tgme_widget_message_text")
        text = text_block.get_text(" ", strip=True) if text_block else ""
        text = re.sub(r"\s+", " ", text).strip()

        image_url = get_image_url(widget)

        posts.append({
            "id": post_id,
            "text": text,
            "image_url": image_url
        })

    return posts


print("Alert forwarder LIVE")

if not processed_ids:
    try:
        posts = get_posts()
        for post in posts:
            processed_ids.add(post["id"])

        save_processed_ids(processed_ids)
        print(f"Initial sync complete. Saved {len(posts)} old posts. Nothing sent.")

    except Exception as e:
        print(f"Initial sync error: {e}")


while True:
    try:
        posts = get_posts()

        new_posts = [
            post for post in posts
            if post["id"] not in processed_ids
        ]

        for post in new_posts:
            post_id = post["id"]
            text = post["text"]
            image_url = post["image_url"]

            processed_ids.add(post_id)

            alert = make_text_alert(text)

            if not alert and image_url:
                image_type = classify_image_by_color(image_url)

                if image_type == "alarm":
                    alert = "🚨 ПОВІТРЯНА ТРИВОГА"
                    if text:
                        alert += f"\n{text}"

                elif image_type == "clear":
                    alert = "✅ ОТБОЙ"
                    if text:
                        alert += f"\n{text}"

            if alert:
                bot.send_message(TARGET_CHANNEL, alert)
                print(f"✅ Sent: {post_id}")
            else:
                print(f"Skipped non-alert: {post_id}")

        if new_posts:
            save_processed_ids(processed_ids)

        time.sleep(2)

    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        time.sleep(10)

    except Exception as e:
        print(f"General error: {e}")
        time.sleep(5)
