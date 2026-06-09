"""
asgi.py — точка входу для ASGI-серверів (Uvicorn, Daphne, Hypercorn).

Що таке ASGI?
─────────────
ASGI (Asynchronous Server Gateway Interface) — стандарт для async Python веб-додатків.
На відміну від WSGI (один потік на запит), ASGI-сервер використовує event loop:
один потік може обслуговувати тисячі одночасних з'єднань.

Як запустити цей проєкт через ASGI:
─────────────────────────────────────
    pip install -r requirements.txt   ← встановить uvicorn + wsproto (WS-підтримка!)
    uvicorn notes_project.asgi:application --reload --port 8001

    ↑ Розбір команди:
    uvicorn                         → ASGI-сервер (аналог gunicorn для async)
    notes_project.asgi:application  → модуль:об'єкт (Django ASGI callable)
    --reload                        → автоперезапуск при зміні файлів (тільки для dev)
    --port 8001                     → порт (8000 зайнятий runserver)

Очікуване попередження при старті (НЕ є помилкою):
────────────────────────────────────────────────────
    WARNING: ASGI 'lifespan' protocol appears unsupported.

    ASGI lifespan — механізм startup/shutdown хуків для ASGI-сервера.
    Django не реалізує lifespan protocol (Django використовує свій AppRegistry).
    Uvicorn пробує lifespan → Django мовчить → uvicorn логує WARNING → продовжує роботу.
    Чат, async views, WebSocket — все працює нормально попри це повідомлення.

Різниця від wsgi.py:
─────────────────────
    wsgi.py → python manage.py runserver → синхронний режим
    asgi.py → uvicorn ...               → асинхронний режим

Async views (/async/notes/) отримують реальну перевагу тільки через ASGI.
Під runserver (WSGI) async views також працюють, але без concurrency-переваг.
"""
import os
from django.core.asgi import get_asgi_application
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notes_project.settings')

# ── КРИТИЧНО: порядок імпортів ────────────────────────────────────────────────
# get_asgi_application() ПОВИНЕН бути викликаний ДО будь-якого імпорту з
# notes_app (consumers, models тощо).
#
# ЧОМУ?
# get_asgi_application() → django.setup() → реєструє всі моделі в AppRegistry.
# consumers.py імпортує ChatMessage (модель) → потребує готового AppRegistry.
# Якщо поміняти порядок → AppRegistryNotReady: Apps aren't loaded yet.
#
# Правило: спочатку django_asgi_app = get_asgi_application()
#          потім  from notes_project.routing import websocket_urlpatterns
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from notes_project.routing import websocket_urlpatterns

# ── ProtocolTypeRouter ────────────────────────────────────────────────────────
# Розподіляє вхідні з'єднання за протоколом:
#
#   "http"      → стандартний Django (views, middleware, templates)
#   "websocket" → Django Channels consumers
#
# Один uvicorn процес, один event loop — обробляє і HTTP і WebSocket.
#
# AuthMiddlewareStack:
#   Читає session cookie з WebSocket handshake HTTP-заголовків.
#   Завантажує User об'єкт → scope['user'].
#   Без нього scope['user'] = AnonymousUser навіть для залогіненого юзера!
#
# URLRouter:
#   Аналог Django urlpatterns але для WebSocket.
#   Маршрутизує ws://host/ws/groups/7/chat/ → GroupChatConsumer
#   (routing.py у цьому ж пакеті).
application = ProtocolTypeRouter({
    # ASGIStaticFilesHandler: обслуговує /static/ файли при DEBUG=True.
    # Еквівалент runserver для статики — тільки для розробки.
    "http": ASGIStaticFilesHandler(django_asgi_app),
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
