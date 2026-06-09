"""
consumers.py — WebSocket Consumer для групового чату.

ЩО ТАКЕ CONSUMER?
──────────────────
Consumer — це аналог view, але для WebSocket-з'єднань.

View:     обробляє ОДИН HTTP запит → повертає відповідь → завершується.
Consumer: живе ВЕСЬ ЧАС поки відкрито WebSocket-з'єднання.

    HTTP flow:
    Browser ──── GET /groups/7/chat/ ────► view() → HttpResponse → з'єднання закрито

    WebSocket flow:
    Browser ══ ws://host/ws/groups/7/chat/ ════► consumer.connect()    ← відкрито
    Browser ══════ {content: "Привіт!"} ══════► consumer.receive()    ← повідомлення
    Browser ══════ {content: "Як справи?"} ═══► consumer.receive()    ← повідомлення
    Browser ══════════════════════════════════► consumer.disconnect()  ← закрито

Async event loop обслуговує ТИСЯЧІ таких з'єднань одночасно.
Кожне з'єднання — це окремий Consumer об'єкт в пам'яті.

ЯК CHANNEL LAYER ДОСТАВЛЯЄ ПОВІДОМЛЕННЯ?
─────────────────────────────────────────
  Consumer Viktor:              Consumer Оля:
    scope['user'] = Viktor       scope['user'] = Оля

    connect():                   connect():
      group_add(                   group_add(
        "chat_group_7",              "chat_group_7",
        self.channel_name            self.channel_name
      )   ↓                        )   ↓
          └──── Channel Layer: підписники групи "chat_group_7" ────┘

    receive("Привіт"):
      group_send(
        "chat_group_7",
        {"type": "chat_message", "content": "Привіт"}
      )
          │
          ▼ Channel Layer доставляє всім підписникам
      chat_message()    chat_message()
          │                 │
      send("Привіт")   send("Привіт")
          │                 │
      Browser Viktor   Browser Оля

ЧОМУ database_sync_to_async?
─────────────────────────────
AsyncWebsocketConsumer працює в asyncio event loop.
Django ORM — синхронний (не може виконуватись в event loop напряму).
database_sync_to_async запускає ORM в окремому потоці Django thread pool.
Це аналог sync_to_async, але оптимізований для Django ORM.
"""
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import Group

from .models import ChatMessage


class GroupChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket Consumer для групового чату.

    Lifecycle:
        1. connect()    — браузер відкрив з'єднання
        2. receive()    — браузер надіслав повідомлення (викликається багато разів)
        3. disconnect() — браузер закрив з'єднання

    Channel layer handler:
        4. chat_message() — channel layer доставив повідомлення від іншого consumer
    """

    # ── CONNECT ───────────────────────────────────────────────────────────────

    async def connect(self):
        """
        Викликається коли браузер відкриває WebSocket-з'єднання.

        scope — dict з метаданими з'єднання (аналог request у view):
          scope['user']                    — User (заповнений AuthMiddlewareStack)
          scope['url_route']['kwargs']     — URL параметри (group_pk з routing.py)
          scope['headers']                 — HTTP заголовки WebSocket handshake
        """
        # 1. Читаємо user з ASGI scope.
        #    AuthMiddlewareStack (asgi.py) вже прочитав session cookie і
        #    завантажив User об'єкт ДО того як нас викликали.
        #    Не потрібно request.auser() — тут немає request, є scope.
        self.user = self.scope['user']

        # 2. Відхиляємо незалогінених.
        #    await self.close() надсилає WebSocket close frame браузеру.
        if not self.user.is_authenticated:
            await self.close()
            return

        # 3. Читаємо group_pk з URL (аналог pk з kwargs у view).
        #    routing.py: re_path(r'^ws/groups/(?P<group_pk>\\d+)/chat/$', ...)
        self.group_pk = int(self.scope['url_route']['kwargs']['group_pk'])

        # 4. Перевіряємо що група існує І user є її членом.
        #    database_sync_to_async — ORM в окремому потоці (не блокує event loop).
        is_member = await self.check_membership(self.group_pk, self.user)
        if not is_member:
            await self.close()
            return

        # 5. Ім'я "broadcasting group" у channel layer.
        #    Всі consumers активного чату групи 7 підписані на "chat_group_7".
        #    group_send("chat_group_7", ...) → доставить повідомлення всім їм.
        self.room_group_name = f"chat_group_{self.group_pk}"

        # 6. Підписуємось на broadcasting group.
        #    self.channel_name — унікальний ID цього конкретного з'єднання
        #    (генерується Django Channels автоматично).
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        # 7. Приймаємо WebSocket-з'єднання.
        #    Без accept() браузер отримає HTTP 403 і з'єднання не відкриється.
        await self.accept()

        # 8. Завантажуємо і надсилаємо останні 50 повідомлень.
        #    Кожне повідомлення надсилається як окремий WS frame.
        #    JS клієнт відрізняє history від нових повідомлень за полем type.
        history = await self.load_history(self.group_pk)
        for msg in history:
            await self.send(text_data=json.dumps({
                'type': 'history',
                'message_id': msg['id'],
                'author': msg['author__username'],
                'content': msg['content'],
                'timestamp': msg['timestamp'].isoformat(),
            }))

    # ── DISCONNECT ────────────────────────────────────────────────────────────

    async def disconnect(self, close_code):
        """
        Викликається коли WebSocket-з'єднання закривається.

        close_code — код закриття:
          1000 — нормальне закриття (браузер закрив вкладку)
          1006 — аварійне (інтернет обірвався)

        ВАЖЛИВО: обов'язково відписатись від group.
        Якщо не відписатись — channel layer спробує доставити наступне
        повідомлення вже закритому з'єднанню → помилка.
        """
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    # ── RECEIVE ───────────────────────────────────────────────────────────────

    async def receive(self, text_data):
        """
        Викликається коли браузер надсилає WebSocket-повідомлення.

        text_data — рядок (зазвичай JSON) від JS клієнта.
        JS надсилає: socket.send(JSON.stringify({content: "Привіт!"}))
        """
        try:
            data = json.loads(text_data)
            content = data.get('content', '').strip()
        except (json.JSONDecodeError, AttributeError):
            return

        # Базова валідація
        if not content or len(content) > 2000:
            return

        # Зберігаємо в БД (database_sync_to_async — ORM у worker thread)
        msg = await self.save_message(self.group_pk, self.user, content)

        # Broadcast всім у channel layer group.
        # type='chat_message' → Django Channels викличе метод chat_message()
        # у КОЖНОГО consumer підписаного на цю групу (включно з нами).
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message_id': msg.id,
                'author': self.user.username,
                'content': content,
                'timestamp': msg.timestamp.isoformat(),
            }
        )

    # ── CHANNEL LAYER HANDLER ─────────────────────────────────────────────────

    async def chat_message(self, event):
        """
        Обробник повідомлень від channel layer.

        Викликається коли group_send() доставив повідомлення цьому consumer.
        Ім'я методу відповідає type у group_send:
          'type': 'chat_message' → метод chat_message()
          'type': 'chat.message' → метод chat_message() (крапка → підкреслення)

        Задача: переслати JSON нашому конкретному браузеру.
        """
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message_id': event['message_id'],
            'author': event['author'],
            'content': event['content'],
            'timestamp': event['timestamp'],
        }))

    # ── DB HELPERS ────────────────────────────────────────────────────────────

    @database_sync_to_async
    def check_membership(self, group_pk, user):
        """
        Перевіряє існування групи і членство user.

        @database_sync_to_async запускає цю функцію у Django thread pool.
        Без цього: SynchronousOnlyOperation — sync ORM у async event loop!

        Повертає False якщо група не існує або user не є членом.
        """
        try:
            group = Group.objects.get(pk=group_pk)
            return group.user_set.filter(pk=user.pk).exists()
        except Group.DoesNotExist:
            return False

    @database_sync_to_async
    def load_history(self, group_pk):
        """
        Завантажує останні 50 повідомлень для групи.

        КРИТИЧНО: повертаємо list of dict, НЕ QuerySet!
        ─────────────────────────────────────────────
        QuerySet — lazy, прив'язаний до DB-з'єднання потоку в якому створений.
        Якщо повернути QuerySet і ітерувати його в async context —
        або SynchronousOnlyOperation, або неправильне з'єднання.

        Рішення: .values() + list() виконує SQL ТУТ, в цьому потоці,
        і повертає звичайний Python список dict — безпечно передавати.

        Логіка:
          - filter(group_id=group_pk) — тільки ця група
          - order_by('-timestamp')[:50] — останні 50 (DESC щоб взяти 50 від кінця)
          - .values() — dict замість Model об'єктів
          - list() — виконати SQL (матеріалізувати)
          - .reverse() — повернути в хронологічному порядку (старі → нові)
        """
        qs = (
            ChatMessage.objects
            .filter(group_id=group_pk)
            .select_related('author')
            .order_by('-timestamp')[:50]
        )
        messages = list(qs.values('id', 'author__username', 'content', 'timestamp'))
        messages.reverse()
        return messages

    @database_sync_to_async
    def save_message(self, group_pk, user, content):
        """
        Зберігає нове повідомлення в БД.

        Повертає ChatMessage об'єкт (з заповненим id та timestamp).
        Цей об'єкт використовується для broadcast у receive().
        """
        return ChatMessage.objects.create(
            group_id=group_pk,
            author=user,
            content=content,
        )
