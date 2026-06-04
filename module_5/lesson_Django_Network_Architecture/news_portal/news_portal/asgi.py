"""
asgi.py — Асинхронний шлюз між веб-сервером та Django.

РОЛЬ У АРХІТЕКТУРІ:
    ASGI (Asynchronous Server Gateway Interface) — сучасний стандарт,
    який підтримує як HTTP, так і WebSockets та Server-Sent Events.

    Схема:    Nginx → Uvicorn/Daphne → asgi.py → Django

РІЗНИЦЯ МІЖ WSGI ТА ASGI:
    WSGI: 1 запит = 1 Python thread (блокуючий)
    ASGI: 1 event loop = тисячі корутин (async/await)

КОЛИ ВИКОРИСТОВУВАТИ ASGI:
    - WebSockets (чат, live-оновлення)
    - Server-Sent Events (стрічка новин в реальному часі)
    - Дуже велике навантаження (high-load API)

ДЛЯ НАШОГО ПРОЄКТУ:
    Ми використовуємо wsgi.py (синхронний режим) — він простіший
    і достатній для новинного сайту без WebSockets.
    asgi.py залишається для ознайомлення з концепцією.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news_portal.settings')

application = get_asgi_application()
