import os
import time
import requests
from bs4 import BeautifulSoup
import telebot

BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL", "twq_b")
SOURCE_URL = "https://t.me/s/raketna_neb"

bot = telebot.TeleBot(BOT_TOKEN)
last_message_id = None

ALERTS = {
    "чисто": "✅ ОТБОЙ",
    "у нас чисто": "✅ ОТБОЙ",
    "видихаємо": "✅ ОТБОЙ",
    "отбой": "✅ ОТБОЙ",
}

THREATS = {
    "баллістики": "🚨 БАЛЛИСТИКА",
    "балістики": "🚨 БАЛЛИСТИКА",
    "шахеди": "🚨 ШАХЕДИ",
    "міг": "🚨 МИГ",
    "ракета": "🚨 РАКЕТА",
    "цель": "🚨 ЦЕЛЬ",
}

def extract_direction(text):
    text_lower = text.lower()
    words = text_lower.split()
    directions = ["запад", "схід", "север", "юг", "затока", "курсом", "море"]
    
    for i, word in enumerate(words):
        if any(d in word for d in directions):
            return " ".join(words[i:min(i+3, len(words))])
    return None

def parse_message(text):
    if not text:
        return None
    
    text_lower = text.lower()
    
    for alert_key, alert_msg in ALERTS.items():
        if alert_key in text_lower:
            return alert_msg
    
    for threat_key, threat_msg in THREATS.items():
        if threat_key in text_lower:
            direction = extract_direction(text)
            if direction:
                return f"{threat_msg} | {direction}"
            return threat_msg
    
    if "укри" in text_lower:
        words = text.split()
        location = words[0] if words else ""
        return f"🚨 {location} в укрытие!"
    
    return None

def get_latest_posts():
    try:
        response = requests.get(SOURCE_URL, timeout=20)
        soup = BeautifulSoup(response.text, "html.parser")
        posts = []
        
        for message in soup.select(".tgme_widget_message"):
            post_id = message.get("data-post")
            text_block = message.select_one(".tgme_widget_message_text")
            text = text_block.get_text(" ", strip=True) if text_block else ""
            
            # Проверяем есть ли фото (без видео)
            has_photo = message.select_one(".tgme_widget_message_photo") is not None
            has_video = message.select_one(".tgme_widget_message_video") is not None
            
            if post_id:
                posts.append((post_id, text, has_photo and not has_video))
        
        return posts
    except Exception as e:
        print(f"Error getting posts: {e}")
        return []

print("Alert forwarder started. Listening to @raketna_neb...")

while True:
    try:
        posts = get_latest_posts()
        
        if posts:
            latest_id, latest_text, has_photo = posts[-1]
            
            if last_message_id is None:
                last_message_id = latest_id
                print(f"Initial message: {latest_id}")
            elif latest_id != last_message_id:
                last_message_id = latest_id
                
                alert_text = None
                
                if latest_text:
                    alert_text = parse_message(latest_text)
                
                if has_photo and not alert_text:
                    alert_text = "🚨 ВОЗДУШНАЯ ТРЕВОГА"
                
                if alert_text:
                    try:
                        bot.send_message(TARGET_CHANNEL, alert_text)
                        print(f"Sent: {alert_text}")
                    except Exception as e:
                        print(f"Error sending: {e}")
                else:
                    print(f"Skipped: {latest_text[:50] if latest_text else 'photo'}")
        
        time.sleep(3)
    
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
