"""
routing.py — WebSocket URL patterns.

Аналог urls.py але для WebSocket-з'єднань.
Цей файл використовується в asgi.py → ProtocolTypeRouter → URLRouter.

Чому re_path а не path?
────────────────────────
Django Channels URLRouter підтримує іменовані групи через regex.
re_path + (?P<group_pk>\\d+) → передається у scope['url_route']['kwargs']['group_pk'].
path() з <int:pk> теж працює в сучасних версіях Channels, але re_path —
класичний підхід, явно показує що WS routing відрізняється від HTTP routing.

URL схема:
    HTTP: /groups/<pk>/chat/         → group_chat view (рендерить HTML + JS)
    WS:   /ws/groups/<pk>/chat/      → GroupChatConsumer (реальний чат)

Префікс /ws/ візуально відокремлює WebSocket URLs від HTTP URLs.
"""
from django.urls import re_path
from notes_app import consumers

websocket_urlpatterns = [
    # ws://127.0.0.1:8001/ws/groups/7/chat/
    # group_pk → scope['url_route']['kwargs']['group_pk'] у consumer
    re_path(r'^ws/groups/(?P<group_pk>\d+)/chat/$', consumers.GroupChatConsumer.as_asgi()),
]
