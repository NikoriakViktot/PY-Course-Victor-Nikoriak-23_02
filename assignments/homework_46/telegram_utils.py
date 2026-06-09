import httpx
from django.conf import settings
async def send_telegram_message(text: str):
    """Надсилає текстове повідомлення у вказаний Telegram-канал."""
    token = settings.TELEGRAM_BOT_TOKEN
    channel_id = settings.TELEGRAM_CHANNEL_ID
    url = f"https://telegram.org{token}/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": text,
        "parse_mode": "HTML"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            return response.status_code == 200
        except httpx.HTTPError:
            return False