"""
test_consumers.py — unit тести WebSocket Consumer (GroupChatConsumer)

РІВЕНЬ ТЕСТУВАННЯ:
  Unit (цей файл) → Django Channels WebsocketCommunicator, без реального браузера
  E2E             → Selenium (test_selenium.py, SeleniumGroupChatPageTest)

ЧИМ ВІДРІЗНЯЄТЬСЯ ВІД SELENIUM ТЕСТІВ:
  Selenium:             реальний браузер → HTTP → WSGI (StaticLiveServerTestCase)
  WebsocketCommunicator: імітує WebSocket з'єднання напряму до consumer
                          без HTTP сервера і без браузера
                          повна підтримка ASGI і channel layers

КОЛИ ВИКОРИСТОВУВАТИ WebsocketCommunicator:
  - Тестуємо логіку connect/receive/disconnect
  - Перевіряємо broadcast між кількома учасниками
  - Тестуємо збереження повідомлень у БД
  - Перевіряємо авторизацію (member vs non-member)

ЯК ЗАПУСТИТИ:
  python manage.py test notes_app.tests.test_consumers -v 2

ЧОМУ TransactionTestCase А НЕ TestCase?
  TestCase загортає кожен тест у транзакцію і робить rollback.
  Django Channels відкриває async DB-з'єднання в окремому потоці/task.
  Транзакція TestCase не видима цьому потоку → дані "зникають" між тестами.
  TransactionTestCase не загортає в транзакцію → дані видимі всім потокам.
  Ціна: повне очищення БД між тестами (повільніше), але коректно.
"""

from django.contrib.auth.models import User, Group as DjangoGroup
from django.test import TransactionTestCase

from channels.testing import WebsocketCommunicator

from notes_app.consumers import GroupChatConsumer
from notes_app.models import ChatMessage

# setUp() у TransactionTestCase — завжди sync (навіть для async тестів).
# Тому ORM викликаємо синхронно тут, хоча тести самі async.
# asyncSetUp() не підтримується в TransactionTestCase до Django 5.1.


def _make_communicator(group_pk, user):
    """
    Створює WebsocketCommunicator з правильним scope для GroupChatConsumer.

    WebsocketCommunicator(app, path):
      - app   → ASGI callable (consumer)
      - path  → URL шлях (використовується для логів, не для маршрутизації тут)

    scope — dict з метаданими з'єднання, аналог request у view.
    Ми встановлюємо вручну те, що у prod встановлює AuthMiddlewareStack + URLRouter:
      scope['user']       ← AuthMiddlewareStack читає з session cookie
      scope['url_route']  ← URLRouter парсить з re_path regex
    """
    communicator = WebsocketCommunicator(
        GroupChatConsumer.as_asgi(),
        f'/ws/groups/{group_pk}/chat/',
    )
    communicator.scope['user'] = user
    communicator.scope['url_route'] = {'kwargs': {'group_pk': str(group_pk)}}
    return communicator


class GroupChatConsumerConnectTest(TransactionTestCase):
    """
    Тести WebSocket connect/disconnect для GroupChatConsumer.

    Перевіряємо:
      - Авторизований член групи → connected = True
      - Не-авторизований (AnonymousUser) → відхилено (close)
      - Авторизований але НЕ член групи → відхилено (close)
      - Правильна відписка від channel group при disconnect
    """

    def setUp(self):
        self.user = User.objects.create_user(username='member', password='pass')
        self.group = DjangoGroup.objects.create(name='ChatGroup')
        self.group.user_set.add(self.user)

    async def test_member_can_connect(self):
        """
        Авторизований член групи успішно підключається.
        connect() → (True, None) означає accept().
        """
        communicator = _make_communicator(self.group.pk, self.user)
        connected, subprotocol = await communicator.connect()

        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_anonymous_user_rejected(self):
        """
        Незалогінений юзер (AnonymousUser) → close(), не accept().
        Consumer викликає self.close() при is_authenticated = False.
        """
        from django.contrib.auth.models import AnonymousUser
        communicator = _make_communicator(self.group.pk, AnonymousUser())
        connected, _ = await communicator.connect()

        self.assertFalse(connected)

    async def test_non_member_rejected(self):
        """
        Авторизований юзер що НЕ є членом групи → відхилено.
        check_membership() повертає False → consumer закриває з'єднання.
        """
        outsider = await User.objects.acreate_user(
            username='outsider', password='pass'
        )
        communicator = _make_communicator(self.group.pk, outsider)
        connected, _ = await communicator.connect()

        self.assertFalse(connected)


class GroupChatConsumerMessagesTest(TransactionTestCase):
    """
    Тести відправки повідомлень і broadcast між учасниками.

    Перевіряємо:
      - Повідомлення одного учасника отримує інший (broadcast)
      - Повідомлення зберігається в БД (ChatMessage)
      - History надсилається при connect() (тип 'history')
      - Порожнє повідомлення не broadcast-иться
    """

    def setUp(self):
        self.user1 = User.objects.create_user(username='alice', password='pass')
        self.user2 = User.objects.create_user(username='bob', password='pass')
        self.group = DjangoGroup.objects.create(name='BroadcastGroup')
        self.group.user_set.add(self.user1, self.user2)

    async def test_message_broadcast_to_other_member(self):
        """
        Alice надсилає повідомлення → Bob отримує його.

        Перевіряє повний шлях:
          alice receive('Привіт') → group_send → channel layer → bob chat_message → bob send
        """
        comm_alice = _make_communicator(self.group.pk, self.user1)
        comm_bob   = _make_communicator(self.group.pk, self.user2)

        await comm_alice.connect()
        await comm_bob.connect()

        # Alice надсилає повідомлення
        await comm_alice.send_json_to({'content': 'Привіт від Alice!'})

        # Alice також отримує власне повідомлення (broadcast включає відправника)
        msg_alice = await comm_alice.receive_json_from()
        self.assertEqual(msg_alice['type'], 'message')
        self.assertEqual(msg_alice['content'], 'Привіт від Alice!')
        self.assertEqual(msg_alice['author'], 'alice')

        # Bob отримує повідомлення від Alice
        msg_bob = await comm_bob.receive_json_from()
        self.assertEqual(msg_bob['type'], 'message')
        self.assertEqual(msg_bob['content'], 'Привіт від Alice!')
        self.assertEqual(msg_bob['author'], 'alice')

        await comm_alice.disconnect()
        await comm_bob.disconnect()

    async def test_message_saved_to_database(self):
        """
        Надіслане повідомлення зберігається в ChatMessage.

        Перевіряємо збереження після broadcast (broadcast = сигнал що save відбувся).
        """
        communicator = _make_communicator(self.group.pk, self.user1)
        await communicator.connect()

        await communicator.send_json_to({'content': 'DB Test Message'})
        await communicator.receive_json_from()  # чекаємо broadcast = save завершено

        count = await ChatMessage.objects.filter(
            group=self.group,
            author=self.user1,
            content='DB Test Message',
        ).acount()
        self.assertEqual(count, 1)

        await communicator.disconnect()

    async def test_message_contains_timestamp(self):
        """
        Broadcast повідомлення містить timestamp (ISO-формат).
        JS клієнт використовує його для відображення часу.
        """
        communicator = _make_communicator(self.group.pk, self.user1)
        await communicator.connect()

        await communicator.send_json_to({'content': 'Timestamp test'})
        response = await communicator.receive_json_from()

        self.assertIn('timestamp', response)
        self.assertIn('message_id', response)

        await communicator.disconnect()

    async def test_empty_message_not_broadcast(self):
        """
        Порожнє або пробільне повідомлення ігнорується (не broadcast).

        Consumer: if not content or len(content) > 2000: return
        """
        communicator = _make_communicator(self.group.pk, self.user1)
        await communicator.connect()

        await communicator.send_json_to({'content': '   '})

        # Після порожнього — жодного broadcast не буде
        # receive з timeout перевіряє що нема повідомлення
        timed_out = await communicator.receive_nothing(timeout=0.5)
        self.assertTrue(timed_out, "Порожнє повідомлення не повинне broadcast-итись")

        await communicator.disconnect()

    async def test_history_sent_on_connect(self):
        """
        При connect() consumer надсилає останні 50 повідомлень з БД (type='history').

        Якщо БД порожня → жодного history повідомлення не надсилається,
        і перше received є тільки після disconnect.
        Якщо є повідомлення → перші received будуть type='history'.
        """
        # Створюємо кілька повідомлень напряму в БД (без WebSocket)
        await ChatMessage.objects.acreate(
            group=self.group, author=self.user1, content='Стара нотатка 1'
        )
        await ChatMessage.objects.acreate(
            group=self.group, author=self.user2, content='Стара нотатка 2'
        )

        communicator = _make_communicator(self.group.pk, self.user1)
        await communicator.connect()

        # Перші 2 повідомлення мають бути history
        msg1 = await communicator.receive_json_from()
        msg2 = await communicator.receive_json_from()

        self.assertEqual(msg1['type'], 'history')
        self.assertEqual(msg2['type'], 'history')
        self.assertEqual(msg1['content'], 'Стара нотатка 1')
        self.assertEqual(msg2['content'], 'Стара нотатка 2')

        await communicator.disconnect()


class GroupChatMultipleGroupsTest(TransactionTestCase):
    """
    Тести ізоляції між групами.

    Повідомлення у групі A не мають потрапляти до учасників групи B.
    """

    def setUp(self):
        self.alice = User.objects.create_user(username='alice2', password='pass')
        self.bob   = User.objects.create_user(username='bob2',   password='pass')
        self.carol = User.objects.create_user(username='carol',  password='pass')

        self.group_a = DjangoGroup.objects.create(name='GroupA')
        self.group_b = DjangoGroup.objects.create(name='GroupB')

        self.group_a.user_set.add(self.alice, self.bob)
        self.group_b.user_set.add(self.carol)

    async def test_message_stays_within_group(self):
        """
        Alice (GroupA) надсилає повідомлення → Carol (GroupB) не отримує.

        Channel layer групи: 'chat_group_<pk>' — кожна група ізольована.
        """
        comm_alice = _make_communicator(self.group_a.pk, self.alice)
        comm_carol = _make_communicator(self.group_b.pk, self.carol)

        await comm_alice.connect()
        await comm_carol.connect()

        await comm_alice.send_json_to({'content': 'Тільки для GroupA'})
        await comm_alice.receive_json_from()  # Alice отримує власне

        # Carol НЕ має отримати це повідомлення
        carol_got_nothing = await comm_carol.receive_nothing(timeout=0.5)
        self.assertTrue(carol_got_nothing, "Carol не має отримувати повідомлення з іншої групи")

        await comm_alice.disconnect()
        await comm_carol.disconnect()
