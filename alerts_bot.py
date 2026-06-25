import os
import time
import requests
from bs4 import BeautifulSoup
import telebot

BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL", "@twq_b")
SOURCE_URL = "https://t.me/s/raketna_neb"

bot = telebot.TeleBot(BOT_TOKEN)

try:
    with open('/tmp/last_message_id.txt', 'r') as f:
        last_message_id = int(f.read().strip())
except:
    last_message_id = -1

def save_last_id(msg_id):
    try:
        with open('/tmp/last_message_id.txt', 'w') as f:
            f.write(str(msg_id))
    except:
        pass

def get_location(text):
    if not text:
        return None
    t = text.lower()
    if "чорноморськ" in t:
        return "Чорноморськ"
    elif "затока" in t:
        return "Затока"
    elif "порт" in t:
        return "Порт"
    elif "одес" in t:
        return "Одеса"
    elif "море" in t:
        return "Море"
    return None

def parse_alerts(text):
    if not text:
        return []
    
    t = text.lower()
    alerts = []
    location = get_location(text)
    
    if "шахед" in t or "шахеди" in t:
        alerts.append(f"🚨 ШАХЕДИ | {location}" if location else "🚨 ШАХЕДИ")
    
    if "баллістик" in t or "балістик" in t:
        alerts.append(f"🚨 БАЛЛИСТИКА | {location}" if location else "🚨 БАЛЛИСТИКА")
    
    if "міг" in t or "міги" in t:
        if "не було" in t or "не было" in t:
            alerts.append("🚨 МИГ (без пуска)")
        elif "пуск" in t:
            alerts.append("🚨 МИГ ПУСК")
        else:
            alerts.append("🚨 МИГ")
    
    if "ракета" in t or "ракети" in t:
        alerts.append(f"🚨 РАКЕТА | {location}" if location else "🚨 РАКЕТА")
    
    if "цель" in t or "цели" in t:
        alerts.append(f"🚨 ЦЕЛЬ | {location}" if location else "🚨 ЦЕЛЬ")
    
    if "укри" in t or "укрыт" in t:
        alerts.append(f"🚨 {location.upper()} В УКРЫТИЕ!!!" if location else "🚨 В УКРЫТИЕ!!!")
    
    if not alerts:
        if "чисто" in t or "отбой" in t:
            alerts.append("✅ ОТБОЙ")
    
    return alerts

def get_posts():
    try:
        response = requests.get(SOURCE_URL, timeout=20)
        soup = BeautifulSoup(response.text, "html.parser")
        posts = []
        
        for message in soup.select(".tgme_widget_message"):
            post_id = message.get("data-post")
            text_block = message.select_one(".tgme_widget_message_text")
            text = text_block.get_text(" ", strip=True) if text_block else ""
            
            if post_id:
                try:
                    posts.append((int(post_id), text))
                except:
                    pass
        
        posts.reverse()
        return posts
    except Exception as e:
        print(f"Error: {e}")
        return []

print("Alert forwarder LIVE")

while True:
    try:
        posts = get_posts()
        
        if posts:
            msg_id, msg_text = posts[0]
            
            if msg_id > last_message_id:
                last_message_id = msg_id
                save_last_id(msg_id)
                
                alerts = parse_alerts(msg_text)
                
                for alert in alerts:
                    try:
                        bot.send_message(TARGET_CHANNEL, alert)
                        print(f"✅ {alert}")
                    except Exception as e:
                        print(f"❌ Error: {e}")
        
        time.sleep(1)
    
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
