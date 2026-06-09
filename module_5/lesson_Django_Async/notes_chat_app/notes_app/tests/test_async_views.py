"""
test_async_views.py — тести для async views.

ЯК ЗАПУСТИТИ:
  # Тільки async тести
  python manage.py test notes_app.tests.test_async_views -v 2

  # Конкретний клас
  python manage.py test notes_app.tests.test_async_views.AsyncNoteListViewTest -v 2

  # Всі тести проєкту (sync + async разом)
  python manage.py test notes_app -v 1

═══════════════════════════════════════════════════════════════════
КЛЮЧОВІ ВІДМІННОСТІ ASYNC ТЕСТІВ ВІД SYNC ТЕСТІВ
═══════════════════════════════════════════════════════════════════

Sync тест (test_views.py):             Async тест (цей файл):
─────────────────────────────────────  ─────────────────────────────────────
from django.test import TestCase       from django.test import TestCase
                                       from django.test import AsyncClient

class NoteListViewTest(TestCase):      class AsyncNoteListViewTest(TestCase):

    def setUp(self):                       def setUp(self):
        self.alice = User.objects...           self.alice = User.objects...  ← SYNC ОК
        self.bob = ...                         self.bob = ...

    def test_redirects(self):              async def test_redirects(self):
        r = self.client.get('/notes/')         client = AsyncClient()
        self.assertEqual(r.status_code, 302)   r = await client.get('/async/notes/')
                                               self.assertEqual(r.status_code, 302)

    def test_auth_user(self):              async def test_auth_user(self):
        self.client.force_login(self.alice)    client = AsyncClient()
        r = self.client.get('/notes/')         await sync_to_async(client.force_login)(self.alice)
        self.assertEqual(r.status_code, 200)   r = await client.get('/async/notes/')
                                               self.assertEqual(r.status_code, 200)

═══════════════════════════════════════════════════════════════════

ВАЖЛИВО про setUp:
  setUp() — звичайна sync функція. Django TestCase виконує її до кожного тесту
  в sync-контексті з автоматичною транзакцією.
  Можна використовувати звичайний ORM (User.objects.create_user) без await.

ВАЖЛИВО про test_* методи:
  async def test_*() — Django 4.1+ підтримує async test methods у TestCase.
  Django автоматично обгортає їх у event loop через async_to_sync.
  Ти пишеш await — Django запускає coroutine.

ВАЖЛИВО про AsyncClient:
  AsyncClient — async-версія self.client.
  Всі HTTP методи — корутини: await client.get(), await client.post(), тощо.

  УВАГА: force_login() у Django 5.2 НЕ є справжньою async функцією!
  Вона успадкована від Client і всередині викликає sync ORM для збереження сесії.
  З async context це кидає SynchronousOnlyOperation.
  Рішення: обгортати у sync_to_async:
      await sync_to_async(client.force_login)(user)  ✅
      await client.force_login(user)                 ❌ (Django 5.2)

ВАЖЛИВО про SESSION у async tests (Django 5.2 + Python 3.14):
  Стандартний DB session backend читає сесію з DB синхронно під час кожного запиту.
  Це кидає SynchronousOnlyOperation в async view context.
  Рішення: signed_cookies session backend — зберігає дані в cookie, DB не потрібна.
  Ми застосовуємо @override_settings(SESSION_ENGINE=...) до BaseViewTest класу.
  Це ПЕДАГОГІЧНА особливість тестового середовища — production код не змінюється.

ВАЖЛИВО про DATABASE у async tests:
  TestCase обгортає кожен тест у транзакцію (rollback після тесту).
  Це відбувається на рівні Django, незалежно від async/sync тесту.
  ORM у setUp — завжди sync і завжди безпечний.

Документація:
  AsyncClient: https://docs.djangoproject.com/en/5.2/topics/testing/tools/#asynchronous-tests
  Async tests: https://docs.djangoproject.com/en/5.2/topics/testing/overview/#async-tests
"""

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.test import TestCase, AsyncClient, override_settings
from django.urls import reverse

from notes_app.models import Note, Notebook


# ─────────────────────────────────────────────────────────────────────────────
# BASE CLASS — спільна підготовка
# ─────────────────────────────────────────────────────────────────────────────

# signed_cookies: зберігає сесію в cookie — жодних DB-запитів при зчитуванні.
# DEBUG=False: вимикає Django Debug Toolbar, який під час рендерингу шаблону
#   викликає context processors синхронно і натрапляє на request.user (sync ORM).
#   Продуктивний код async_views.py правильний; це обмеження тестового середовища.
@override_settings(
    SESSION_ENGINE='django.contrib.sessions.backends.signed_cookies',
    DEBUG=False,
)
class AsyncBaseViewTest(TestCase):
    """
    Базовий клас для async view тестів.

    setUp() — синхронна (ORM можна викликати напряму).
    Два юзери для тестування ізоляції даних між користувачами.

    Порівняй із BaseViewTest у test_views.py — структура ідентична.
    Різниця буде у test_* методах: async def + AsyncClient.
    """

    def setUp(self):
        # Sync ORM у setUp — завжди безпечно, Django обгортає в sync context
        self.alice = User.objects.create_user('alice_async', password='pass123')
        self.bob = User.objects.create_user('bob_async', password='pass123')


# ─────────────────────────────────────────────────────────────────────────────
# NOTE LIST VIEW TESTS
# ─────────────────────────────────────────────────────────────────────────────

class AsyncNoteListViewTest(AsyncBaseViewTest):
    """
    Тести для async_note_list view.

    URL: /async/notes/
    Sync-аналог: NoteListViewTest у test_views.py

    Перевіряємо:
      1. Неавтентифікований → redirect до login
      2. Автентифікований → 200 OK
      3. Alice бачить свої нотатки, але НЕ бачить нотатки Bob
    """

    async def test_unauthenticated_redirects_to_login(self):
        """
        GET /async/notes/ без логіну → redirect до /accounts/login/

        Порівняй із sync версією: test_views.py::NoteListViewTest::test_redirects_to_login
        Ключова різниця: AsyncClient + await.
        """
        # Новий AsyncClient без сесії (не автентифікований)
        client = AsyncClient()

        # await — бо client.get() тепер корутина
        response = await client.get(reverse('notes_app:async_note_list'))

        # @login_required → 302 redirect до login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    async def test_authenticated_user_gets_200(self):
        """
        Alice логіниться → 200 OK із списком нотаток.
        """
        client = AsyncClient()

        # await force_login — async версія force_login (без перевірки пароля)
        await sync_to_async(client.force_login)(self.alice)

        # await GET запит до async view
        response = await client.get(reverse('notes_app:async_note_list'))

        self.assertEqual(response.status_code, 200)
        # Перевіряємо що шаблон note_list.html використовується
        self.assertTemplateUsed(response, 'notes_app/note_list.html')

    async def test_alice_sees_only_her_notes(self):
        """
        Alice бачить свою нотатку. Bob's нотатка не видима.

        Sync-аналог: test_views.py::NoteListViewTest::test_only_own_notes_visible
        """
        # Sync ORM у async test — НЕБЕЗПЕЧНО (у async context)!
        # Але у setUp ми вже створили юзерів. Тут нам треба NOTE.
        # Рішення: ORM в async тесті через sync_to_async
        # Створюємо нотатки через sync_to_async
        # Note.objects.create() — sync ORM → обгортаємо
        alice_note = await sync_to_async(Note.objects.create)(
            user=self.alice,
            title='Нотатка Alice',
            content='Секретний зміст',
        )
        await sync_to_async(Note.objects.create)(
            user=self.bob,
            title='Нотатка Bob',
            content='Інший зміст',
        )

        client = AsyncClient()
        await sync_to_async(client.force_login)(self.alice)
        response = await client.get(reverse('notes_app:async_note_list'))

        self.assertEqual(response.status_code, 200)
        # Alice бачить свою нотатку
        self.assertContains(response, 'Нотатка Alice')
        # Alice НЕ бачить нотатку Bob (multi-tenant isolation)
        self.assertNotContains(response, 'Нотатка Bob')


# ─────────────────────────────────────────────────────────────────────────────
# NOTE DETAIL VIEW TESTS
# ─────────────────────────────────────────────────────────────────────────────

class AsyncNoteDetailViewTest(AsyncBaseViewTest):
    """
    Тести для async_note_detail view.

    URL: /async/notes/<pk>/
    Sync-аналог: NoteDetailViewTest у test_views.py

    Перевіряємо:
      1. Неавтентифікований → redirect
      2. Alice може бачити свою нотатку
      3. Bob отримує 404 на нотатку Alice
    """

    def setUp(self):
        super().setUp()
        # sync ORM у setUp — ОК
        self.alice_note = Note.objects.create(
            user=self.alice,
            title='Нотатка Alice для detail тесту',
            content='Зміст нотатки',
        )

    async def test_owner_can_view_note(self):
        """Alice може переглянути свою нотатку."""
        client = AsyncClient()
        await sync_to_async(client.force_login)(self.alice)

        response = await client.get(
            reverse('notes_app:async_note_detail', args=[self.alice_note.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Нотатка Alice для detail тесту')

    async def test_other_user_gets_404(self):
        """
        Bob намагається отримати нотатку Alice → 404.

        Це перевіряє ownership isolation: async ORM фільтрує по user.
        """
        client = AsyncClient()
        await sync_to_async(client.force_login)(self.bob)

        response = await client.get(
            reverse('notes_app:async_note_detail', args=[self.alice_note.pk])
        )

        # async_get_note_detail кидає Note.DoesNotExist → view піднімає Http404
        self.assertEqual(response.status_code, 404)

    async def test_unauthenticated_redirects(self):
        """Без логіну → redirect до login."""
        client = AsyncClient()
        response = await client.get(
            reverse('notes_app:async_note_detail', args=[self.alice_note.pk])
        )
        self.assertEqual(response.status_code, 302)


# ─────────────────────────────────────────────────────────────────────────────
# NOTE CREATE VIEW TESTS
# ─────────────────────────────────────────────────────────────────────────────

class AsyncNoteCreateViewTest(AsyncBaseViewTest):
    """
    Тести для async_note_create view.

    URL: GET/POST /async/notes/create/
    Sync-аналог: NoteCreateViewTest у test_views.py

    Перевіряємо:
      1. GET → форма відображається
      2. POST із валідними даними → нотатку створено, redirect
      3. POST із невалідними даними → форма з помилками
    """

    async def test_get_shows_form(self):
        """GET /async/notes/create/ → форма створення."""
        client = AsyncClient()
        await sync_to_async(client.force_login)(self.alice)

        response = await client.get(reverse('notes_app:async_note_create'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes_app/note_form.html')
        # Форма є в контексті
        self.assertIn('form', response.context)

    async def test_valid_post_creates_note(self):
        """
        POST із заголовком → нотатку створено, redirect до detail.

        Це тестує що:
          1. async_create_note (через sync_to_async) спрацьовує
          2. Note.objects.count() збільшився на 1
          3. Redirect на async_note_detail
        """
        client = AsyncClient()
        await sync_to_async(client.force_login)(self.alice)

        # Кількість нотаток до
        count_before = await sync_to_async(Note.objects.filter(user=self.alice).count)()

        response = await client.post(
            reverse('notes_app:async_note_create'),
            data={
                'title': 'Нова async нотатка',
                'content': 'Зміст через async view',
                'priority': 2,
            },
        )

        # Після redirect (302) нотатку має бути створено
        count_after = await sync_to_async(Note.objects.filter(user=self.alice).count)()
        self.assertEqual(count_after, count_before + 1)

        # Redirect до detail новоствореної нотатки
        self.assertEqual(response.status_code, 302)

    async def test_empty_title_shows_form_again(self):
        """POST без заголовку → форма показується знову з помилками."""
        client = AsyncClient()
        await sync_to_async(client.force_login)(self.alice)

        response = await client.post(
            reverse('notes_app:async_note_create'),
            data={'title': '', 'content': 'Зміст без заголовку'},
        )

        # 200 (форма повернена) замість 302 (redirect)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes_app/note_form.html')


# ─────────────────────────────────────────────────────────────────────────────
# NOTE DELETE VIEW TESTS
# ─────────────────────────────────────────────────────────────────────────────

class AsyncNoteDeleteViewTest(AsyncBaseViewTest):
    """
    Тести для async_note_delete view.

    URL: GET/POST /async/notes/<pk>/delete/
    Sync-аналог: NoteDeleteViewTest у test_views.py

    Перевіряємо:
      1. GET → сторінка підтвердження
      2. POST → нотатку видалено, redirect
      3. Bob не може видалити нотатку Alice
    """

    def setUp(self):
        super().setUp()
        self.alice_note = Note.objects.create(
            user=self.alice,
            title='Нотатка для видалення',
        )

    async def test_get_shows_confirmation(self):
        """GET → сторінка підтвердження видалення."""
        client = AsyncClient()
        await sync_to_async(client.force_login)(self.alice)

        response = await client.get(
            reverse('notes_app:async_note_delete', args=[self.alice_note.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Нотатка для видалення')

    async def test_post_deletes_note(self):
        """
        POST → нотатку видалено через adelete(), redirect до list.

        Перевіряємо що nota більше не існує у DB.
        """
        client = AsyncClient()
        await sync_to_async(client.force_login)(self.alice)

        response = await client.post(
            reverse('notes_app:async_note_delete', args=[self.alice_note.pk])
        )

        # Redirect до async_note_list
        # fetch_redirect_response=False: не слідуємо за redirect, бо self.client async
        self.assertRedirects(response, reverse('notes_app:async_note_list'),
                             fetch_redirect_response=False)

        # Нотатки більше немає у DB
        exists = await sync_to_async(
            Note.objects.filter(pk=self.alice_note.pk).exists
        )()
        self.assertFalse(exists)

    async def test_bob_cannot_delete_alice_note(self):
        """Bob намагається видалити нотатку Alice → 404."""
        client = AsyncClient()
        await sync_to_async(client.force_login)(self.bob)

        response = await client.post(
            reverse('notes_app:async_note_delete', args=[self.alice_note.pk])
        )

        # async_get_note_detail фільтрує по user → DoesNotExist → 404
        self.assertEqual(response.status_code, 404)


# ─────────────────────────────────────────────────────────────────────────────
# NOTE TOGGLE PIN VIEW TESTS
# ─────────────────────────────────────────────────────────────────────────────

class AsyncNoteTogglePinViewTest(AsyncBaseViewTest):
    """
    Тести для async_note_toggle_pin view.

    URL: POST /async/notes/<pk>/pin/
    Цей endpoint існує тільки в async версії (демонстрація aupdate + F()).

    Перевіряємо:
      1. POST → is_pinned змінюється True→False або False→True
      2. Bob не може пінувати нотатку Alice
    """

    def setUp(self):
        super().setUp()
        self.alice_note = Note.objects.create(
            user=self.alice,
            title='Нотатка для pin тесту',
            is_pinned=False,
        )

    async def test_toggle_pin_changes_status(self):
        """
        POST → is_pinned змінюється (False → True).

        Перевіряємо значення в DB після aupdate().
        """
        client = AsyncClient()
        await sync_to_async(client.force_login)(self.alice)

        # Перевіряємо що нотатка НЕ закріплена
        self.assertFalse(self.alice_note.is_pinned)

        # POST → aupdate() змінює is_pinned
        response = await client.post(
            reverse('notes_app:async_note_toggle_pin', args=[self.alice_note.pk])
        )

        self.assertEqual(response.status_code, 302)

        # Перезавантажуємо з DB (refresh_from_db)
        refresh = sync_to_async(self.alice_note.refresh_from_db)
        await refresh()

        # Тепер повинна бути True
        self.assertTrue(self.alice_note.is_pinned)

    async def test_bob_cannot_pin_alice_note(self):
        """Bob намагається пінувати нотатку Alice → 404."""
        client = AsyncClient()
        await sync_to_async(client.force_login)(self.bob)

        response = await client.post(
            reverse('notes_app:async_note_toggle_pin', args=[self.alice_note.pk])
        )

        self.assertEqual(response.status_code, 404)
