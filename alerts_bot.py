import os
import asyncio
from pyrogram import Client
from datetime import datetime

# Переменные окружения
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SOURCE_CHANNEL = "raketna_neb"
TARGET_CHANNEL = "twq_b"

app = Client(
    "alert_forwarder",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Словари для парсинга
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

last_message_id = 0

def extract_direction(text):
    """Парсит направление из текста"""
    text_lower = text.lower()
    words = text_lower.split()
    
    directions = ["запад", "схід", "север", "юг", "затока", "курсом", "море", "сторону", "на"]
    
    for i, word in enumerate(words):
        if any(d in word for d in directions):
            direction_part = " ".join(words[i:min(i+3, len(words))])
            return direction_part
    return None

def parse_message(text):
    """Анализирует сообщение и возвращает форматированный вывод"""
    if not text:
        return None
    
    text_lower = text.lower()
    
    # Проверяем отбой
    for alert_key, alert_msg in ALERTS.items():
        if alert_key in text_lower:
            return alert_msg
    
    # Проверяем угрозы
    for threat_key, threat_msg in THREATS.items():
        if threat_key in text_lower:
            direction = extract_direction(text)
            if direction:
                return f"{threat_msg} | {direction}"
            return threat_msg
    
    # Проверяем "в укрытие"
    if "укри" in text_lower or "укрытие" in text_lower:
        words = text.split()
        location = words[0] if words else ""
        return f"🚨 {location} в укрытие!"
    
    return None

async def check_messages():
    """Полинг новых сообщений"""
    global last_message_id
    
    try:
        async with app:
            print(f"Alert forwarder started. Listening to @{SOURCE_CHANNEL}...")
            
            while True:
                try:
                    # Получаем последние сообщения
                    messages = []
                    async for message in app.get_chat_history(SOURCE_CHANNEL, limit=5):
                        messages.append(message)
                    
                    # Обрабатываем в обратном порядке (старые->новые)
                    for message in reversed(messages):
                        if message.id > last_message_id:
                            last_message_id = message.id
                            
                            alert_text = None
                            
                            # Проверяем текст
                            if message.text:
                                alert_text = parse_message(message.text)
                            
                            # Проверяем фото (сирены)
                            if message.photo and not alert_text:
                                alert_text = "🚨 ВОЗДУШНАЯ ТРЕВОГА"
                            
                            # Отправляем если нашли
                            if alert_text:
                                try:
                                    await app.send_message(TARGET_CHANNEL, alert_text)
                                    print(f"Sent: {alert_text}")
                                except Exception as e:
                                    print(f"Error sending: {e}")
                    
                    # Ждём 3 секунды перед следующей проверкой
                    await asyncio.sleep(3)
                    
                except Exception as e:
                    print(f"Error checking messages: {e}")
                    await asyncio.sleep(5)
    
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    app.run(check_messages())
