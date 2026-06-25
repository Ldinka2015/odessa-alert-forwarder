import os
from pyrogram import Client, filters
from pyrogram.types import Message

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

# Ключевые слова для парсинга
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

DIRECTIONS = [
    "запад", "схід", "север", "юг", "затока", "курсом",
    "море", "сторону", "на", "курс"
]

def extract_direction(text):
    """Парсит направление из текста"""
    text_lower = text.lower()
    words = text_lower.split()
    
    for i, word in enumerate(words):
        if any(d in word for d in DIRECTIONS):
            # Собираем следующие 1-2 слова как направление
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
        # Пытаемся найти локацию
        words = text.split()
        location = words[0] if words else ""
        return f"🚨 {location} в укрытие!"
    
    return None

def has_alarm_image(message: Message):
    """Проверяет наличие изображения сирены в сообщении"""
    # Если есть фото без видео - это сирена
    if message.photo and not message.video:
        return True
    return False

@app.on_message(filters.channel & filters.incoming)
async def forward_alerts(client: Client, message: Message):
    """Основной обработчик сообщений"""
    # Проверяем что сообщение из исходного канала
    if message.chat.username != SOURCE_CHANNEL:
        return
    
    alert_text = None
    
    # Проверяем текст
    if message.text:
        alert_text = parse_message(message.text)
    
    # Проверяем картинки (сирены)
    if message.photo and not alert_text:
        alert_text = "🚨 ВОЗДУШНАЯ ТРЕВОГА"
    
    # Если нашли что-то - отправляем
    if alert_text:
        try:
            await client.send_message(TARGET_CHANNEL, alert_text)
            print(f"Sent: {alert_text}")
        except Exception as e:
            print(f"Error sending message: {e}")

if __name__ == "__main__":
    print("Alert forwarder started. Listening to @raketna_neb...")
    app.run()
