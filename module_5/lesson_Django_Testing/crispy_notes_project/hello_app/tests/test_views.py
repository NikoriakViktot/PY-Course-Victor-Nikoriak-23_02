"""
test_views.py — Інтеграційні тести через Django Test Client

ЯК ЗАПУСТИТИ:
  # Перейти до папки проєкту (якщо ще не там)
  cd module_5/lesson_Django_Testing/crispy_notes_project

  # Всі тести цього файлу (41 тест)
  python manage.py test hello_app.tests.test_views -v 2

  # Конкретний клас
  python manage.py test hello_app.tests.test_views.NoteListViewTest -v 2
  python manage.py test hello_app.tests.test_views.NoteDetailViewTest -v 2
  python manage.py test hello_app.tests.test_views.NoteCreateViewTest -v 2
  python manage.py test hello_app.tests.test_views.NoteEditViewTest -v 2
  python manage.py test hello_app.tests.test_views.NoteDeleteViewTest -v 2
  python manage.py test hello_app.tests.test_views.NotebookViewTest -v 2
  python manage.py test hello_app.tests.test_views.GroupViewTest -v 2
  python manage.py test hello_app.tests.test_views.TodoListSharingViewTest -v 2

  # Конкретний тест
  python manage.py test hello_app.tests.test_views.NoteDetailViewTest.test_group_member_can_view_note -v 2

  # Зупинитись на першому провалі
  python manage.py test hello_app.tests.test_views --failfast -v 2

  # Всі тести проєкту разом
  python manage.py test hello_app.tests -v 1

ВІДМІННІСТЬ ВІД UNIT ТЕСТІВ:
  Unit тести (test_services.py):
    services.create_note(user=alice, title='Test')   ← прямий виклик Python
    Тестуємо: бізнес-логіку, не HTTP

  Інтеграційні тести (цей файл):
    self.client.get(reverse('hello_app:note_list'))  ← симуляція HTTP запиту
    Тестуємо: URL routing → view → DB → HTTP response

  Що інтеграційний тест перевіряє, чого unit тест НЕ може:
  - Чи @login_required справді захищає view?
  - Чи redirect після POST іде у правильну URL?
  - Чи Bob дійсно отримує 404 при спробі доступу до нотатки Alice?
  - Чи form errors передаються до контексту шаблону?
  - Чи назва нотатки видна в HTML відповіді?

ВАЖЛИВІ КОНЦЕПЦІЇ:
  force_login(user) — логін без перевірки пароля, швидше за client.login()
  assertRedirects    — перевіряє HTTP 302 + кінцевий URL
  assertContains     — шукає рядок у HTML response.content
  response.context   — контекст шаблону (form, notes, etc.)
  response.status_code — 200 OK, 302 redirect, 404 not found, 403 forbidden
"""

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from hello_app.models import Note, Notebook, TodoList


# ─────────────────────────────────────────────────────────────────────────────
# BASE CLASS
# ─────────────────────────────────────────────────────────────────────────────

class BaseViewTest(TestCase):
    """
    Спільна підготовка для всіх view тестів.

    Два юзери (alice і bob) дозволяють тестувати:
    - Чи alice бачить свої нотатки
    - Чи bob НЕ може доступитись до нотаток alice (ownership enforcement)

    Note: force_login() — стандарт у view тестах.
    Він швидший за client.login() бо не проходить повний auth pipeline.
    """

    def setUp(self):
        self.alice = User.objects.create_user('alice', password='pass123')
        self.bob   = User.objects.create_user('bob',   password='pass123')

        # Базова нотатка Alice — використовується в більшості тестів
        self.alice_note = Note.objects.create(
            user=self.alice, title="Alice Note", content="Alice content"
        )
        # Записник Alice — для тестів Notebook views
        self.alice_notebook = Notebook.objects.create(
            user=self.alice, title="Alice Notebook"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 1. AUTHENTICATION — login_required на всіх захищених views
# ─────────────────────────────────────────────────────────────────────────────

class AuthenticationViewTest(BaseViewTest):
    """
    Перевіряємо що всі захищені views вимагають авторизацію.

    ЩО МИ ЗАХИЩАЄМО:
      @login_required decorator повинен редіректити на /accounts/login/?next=...
      якщо юзер не залогінений.

    ЧОМУ ЦЕ ВАЖЛИВО:
      Якщо забути @login_required на одному view — анонімний юзер отримує
      доступ до приватних даних. Цей тест одразу виявить таке забуття.

    СИГНАТУРА assertRedirects:
      assertRedirects(response, expected_url, fetch_redirect_response=False)
      fetch_redirect_response=False — не робимо другий запит, тільки перевіряємо URL
    """

    def _assert_login_required(self, url):
        """Допоміжний метод: будь-яка URL → redirect на login."""
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_note_list_redirects_anonymous(self):
        """Незалогінений юзер не може переглянути список нотаток."""
        self._assert_login_required(reverse('hello_app:note_list'))

    def test_note_create_redirects_anonymous(self):
        """Незалогінений юзер не може відкрити форму створення нотатки."""
        self._assert_login_required(reverse('hello_app:note_create'))

    def test_note_detail_redirects_anonymous(self):
        """Незалогінений юзер не може переглянути деталі нотатки."""
        self._assert_login_required(reverse('hello_app:note_detail', args=[self.alice_note.pk]))

    def test_note_edit_redirects_anonymous(self):
        """Незалогінений юзер не може відкрити форму редагування."""
        self._assert_login_required(reverse('hello_app:note_edit', args=[self.alice_note.pk]))

    def test_note_delete_redirects_anonymous(self):
        """Незалогінений юзер не може видалити нотатку."""
        self._assert_login_required(reverse('hello_app:note_delete', args=[self.alice_note.pk]))

    def test_notebook_list_redirects_anonymous(self):
        """Захист notebooks — теж вимагає авторизацію."""
        self._assert_login_required(reverse('hello_app:notebook_list'))

    def test_group_list_redirects_anonymous(self):
        """Захист груп."""
        self._assert_login_required(reverse('hello_app:group_list'))

    def test_todo_list_redirects_anonymous(self):
        """Захист to do списків."""
        self._assert_login_required(reverse('hello_app:todo_list'))


# ─────────────────────────────────────────────────────────────────────────────
# 2. NOTE LIST — список нотаток поточного юзера
# ─────────────────────────────────────────────────────────────────────────────

class NoteListViewTest(BaseViewTest):
    """
    Перевіряємо що список нотаток показує тільки нотатки поточного юзера.

    ЩО ТЕСТУЄМО:
      selectors.get_user_notes(request.user) повинен фільтрувати за user.
      Але view може помилково викликати Note.objects.all() замість filter!
      Цей тест виявить таку регресію одразу.

    ЯК ЧИТАТИ assertContains / assertNotContains:
      assertContains(response, text) — перевіряє що рядок є в HTML
      assertNotContains(response, text) — перевіряє що рядка НЕМАЄ в HTML
    """

    def test_authenticated_user_gets_200(self):
        """Залогінений юзер отримує сторінку зі списком (HTTP 200 OK)."""
        self.client.force_login(self.alice)
        response = self.client.get(reverse('hello_app:note_list'))
        self.assertEqual(response.status_code, 200)

    def test_note_list_shows_own_notes(self):
        """Alice бачить свою нотатку в списку."""
        self.client.force_login(self.alice)
        response = self.client.get(reverse('hello_app:note_list'))
        self.assertContains(response, 'Alice Note')

    def test_note_list_excludes_other_user_notes(self):
        """
        Alice НЕ бачить нотатки Bob'а — multi-tenant ізоляція.

        Якщо selectors.get_user_notes() не фільтрує за user=request.user,
        цей тест впаде і покаже де саме витік даних.
        """
        bob_note = Note.objects.create(user=self.bob, title="Bob Secret Note", content="...")
        self.client.force_login(self.alice)
        response = self.client.get(reverse('hello_app:note_list'))
        self.assertNotContains(response, 'Bob Secret Note')


# ─────────────────────────────────────────────────────────────────────────────
# 3. NOTE DETAIL — перегляд нотатки
# ─────────────────────────────────────────────────────────────────────────────

class NoteDetailViewTest(BaseViewTest):
    """
    Перевіряємо access control для note_detail.

    АРХІТЕКТУРА ДОСТУПУ:
      selectors.get_note_detail(user, pk) повертає нотатку якщо:
        - note.user == user (власник)
        - note.group in user.groups.all() (член групи)
      Якщо не одне і не інше → Note.DoesNotExist → Http404 у view

    ВАЖЛИВО:
      Це тест "групового доступу" — коли нотатка прив'язана до Django Group
      і Bob є членом цієї групи, він МАЄ бачити нотатку.
      Це критично для функції спільних нотаток в CrispyNotes.
    """

    def test_owner_can_view_own_note(self):
        """Alice (власниця) може переглянути свою нотатку — 200 OK."""
        self.client.force_login(self.alice)
        response = self.client.get(
            reverse('hello_app:note_detail', args=[self.alice_note.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alice Note')

    def test_non_owner_gets_404(self):
        """
        Bob (не власник, не в жодній групі) намагається переглянути нотатку Alice → 404.

        Чому 404, а не 403?
        Showing 403 reveals that the resource EXISTS but access is denied.
        Showing 404 is safer — reveals nothing about the resource.
        """
        self.client.force_login(self.bob)
        response = self.client.get(
            reverse('hello_app:note_detail', args=[self.alice_note.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_group_member_can_view_note(self):
        """
        Bob доданий до групи 'Family'. Alice створює нотатку в групі 'Family'.
        Bob (член групи) може переглянути нотатку Alice → 200 OK.

        Це перевірка ключового бізнес-фічеру: спільні нотатки через групи.
        """
        family_group = Group.objects.create(name='Family')
        self.alice.groups.add(family_group)
        self.bob.groups.add(family_group)

        group_note = Note.objects.create(
            user=self.alice, title='Family Note', content='...', group=family_group
        )

        self.client.force_login(self.bob)
        response = self.client.get(
            reverse('hello_app:note_detail', args=[group_note.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_non_group_member_cannot_view_note(self):
        """
        Bob НЕ є членом групи 'Family', тому нотатка Alice (в групі) для нього недоступна → 404.
        """
        family_group = Group.objects.create(name='Family2')
        self.alice.groups.add(family_group)
        # Bob NOT added to group

        group_note = Note.objects.create(
            user=self.alice, title='Family Only Note', group=family_group
        )

        self.client.force_login(self.bob)
        response = self.client.get(
            reverse('hello_app:note_detail', args=[group_note.pk])
        )
        self.assertEqual(response.status_code, 404)


# ─────────────────────────────────────────────────────────────────────────────
# 4. NOTE CREATE — форма створення нотатки
# ─────────────────────────────────────────────────────────────────────────────

class NoteCreateViewTest(BaseViewTest):
    """
    Тестуємо повний цикл створення нотатки через HTTP:
    GET (отримати форму) → POST (відправити дані) → redirect.

    ВАЖЛИВІ ПЕРЕВІРКИ:
    1. Valid POST → redirect (302) + нотатка в БД + belongs to alice
    2. Invalid POST (empty title) → 200 + form errors у контексті шаблону
    3. IDOR prevention: alice не може вибрати notebook Bob'а через form

    ЩО ПЕРЕВІРЯЄ response.context['form'].errors:
      Якщо форма невалідна, view ре-рендерить шаблон з тією ж формою.
      Помилки доступні через response.context['form'].errors['field_name']
    """

    def test_get_create_form_returns_200(self):
        """GET /notes/new/ → форма створення, HTTP 200."""
        self.client.force_login(self.alice)
        response = self.client.get(reverse('hello_app:note_create'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_valid_post_creates_note_and_redirects(self):
        """
        POST з валідними даними → нотатка збережена в БД → redirect до note_detail.

        Важливо: перевіряємо і redirect (302) і факт збереження в БД.
        """
        self.client.force_login(self.alice)
        response = self.client.post(
            reverse('hello_app:note_create'),
            data={'title': 'New Note', 'content': 'Body text', 'priority': 1},
        )
        # View робить redirect після успішного POST
        self.assertEqual(response.status_code, 302)
        # Нотатка справді збережена в БД
        self.assertTrue(Note.objects.filter(title='New Note').exists())

    def test_created_note_belongs_to_logged_in_user(self):
        """
        Нотатка стає власністю залогіненого юзера — не довільного.

        view.py: note = services.create_note(user=request.user, ...)
        Якщо хтось змінить на user=form.cleaned_data.get('user') → Mass Assignment!
        Цей тест виявить це.
        """
        self.client.force_login(self.alice)
        self.client.post(
            reverse('hello_app:note_create'),
            data={'title': 'Alice New Note', 'content': '', 'priority': 1},
        )
        note = Note.objects.get(title='Alice New Note')
        self.assertEqual(note.user, self.alice)

    def test_empty_title_shows_form_error(self):
        """
        POST з порожнім title → форма невалідна → 200 (ре-рендер) + помилка у полі title.

        Якщо view передає форму до шаблону, студент може перевірити:
        response.context['form'].errors — словник {field_name: [error_messages]}
        """
        self.client.force_login(self.alice)
        response = self.client.post(
            reverse('hello_app:note_create'),
            data={'title': '', 'content': 'Body', 'priority': 1},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('title', response.context['form'].errors)

    def test_form_rejects_other_users_notebook_idor_prevention(self):
        """
        IDOR prevention через форму:
        Alice намагається POST з notebook=bob_notebook.id (маніпуляція даними).
        NoteForm(user=alice) фільтрує queryset → Bob's notebook = invalid choice → form invalid.

        БЕЗ ЗАХИСТУ: alice могла б прив'язати свою нотатку до чужого записника.
        З ЗАХИСТОМ: NoteForm фільтрує queryset по user= → invalid choice error.
        """
        bob_notebook = Notebook.objects.create(user=self.bob, title="Bob Notebook")
        self.client.force_login(self.alice)
        response = self.client.post(
            reverse('hello_app:note_create'),
            data={'title': 'Hack Note', 'content': '', 'priority': 1, 'notebook': bob_notebook.pk},
        )
        # Form invalid → 200 ре-рендер (не 302 redirect)
        self.assertEqual(response.status_code, 200)
        # Нотатка НЕ збережена
        self.assertFalse(Note.objects.filter(title='Hack Note').exists())


# ─────────────────────────────────────────────────────────────────────────────
# 5. NOTE EDIT — редагування нотатки
# ─────────────────────────────────────────────────────────────────────────────

class NoteEditViewTest(BaseViewTest):
    """
    Тестуємо ownership enforcement у note_edit view.

    ЛОГІКА У views.py:
      note = get_object_or_404(
          Note.objects.filter(Q(user=request.user) | Q(group__in=user_groups)),
          pk=pk,
      )
      if note.user != request.user:
          # redirect з помилкою (якщо в групі але не власник)
      ...

    Для Bob (не в жодній групі): get_object_or_404 поверне 404.
    """

    def test_owner_can_open_edit_form(self):
        """Alice (власниця) отримує форму редагування — 200 OK."""
        self.client.force_login(self.alice)
        response = self.client.get(
            reverse('hello_app:note_edit', args=[self.alice_note.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_non_owner_cannot_edit_gets_404(self):
        """
        Bob (не власник, не в групі) намагається відкрити edit форму Alice → 404.

        Правило: якщо нотатка не існує для тебе (не твоя і не в твоїй групі)
        → 404, а не 403. Так ми не розкриваємо чи існує нотатка.
        """
        self.client.force_login(self.bob)
        response = self.client.get(
            reverse('hello_app:note_edit', args=[self.alice_note.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_valid_edit_updates_note_in_db(self):
        """
        Alice POST редагування → нотатка оновлена в БД → redirect.

        Persistence test: перевіряємо що зміни дійсно збережені.
        """
        self.client.force_login(self.alice)
        self.client.post(
            reverse('hello_app:note_edit', args=[self.alice_note.pk]),
            data={'title': 'Updated Title', 'content': 'New content', 'priority': 2},
        )
        self.alice_note.refresh_from_db()
        self.assertEqual(self.alice_note.title, 'Updated Title')

    def test_invalid_edit_shows_form_errors(self):
        """POST порожнього title → 200 + form errors, нотатка НЕ оновлена."""
        self.client.force_login(self.alice)
        response = self.client.post(
            reverse('hello_app:note_edit', args=[self.alice_note.pk]),
            data={'title': '', 'content': 'Updated', 'priority': 1},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('title', response.context['form'].errors)
        # Назва нотатки не змінилась
        self.alice_note.refresh_from_db()
        self.assertEqual(self.alice_note.title, 'Alice Note')


# ─────────────────────────────────────────────────────────────────────────────
# 6. NOTE DELETE — видалення нотатки
# ─────────────────────────────────────────────────────────────────────────────

class NoteDeleteViewTest(BaseViewTest):
    """
    Тестуємо що тільки власник може видалити нотатку.

    FLOW DELETE VIEW:
      GET  /notes/<pk>/delete/ → підтвердження (confirm page)
      POST /notes/<pk>/delete/ → видалення + redirect до note_list
    """

    def test_owner_can_delete_note(self):
        """
        Alice POST /notes/<pk>/delete/ → нотатка видалена з БД + redirect.
        """
        pk = self.alice_note.pk
        self.client.force_login(self.alice)
        response = self.client.post(
            reverse('hello_app:note_delete', args=[pk])
        )
        # Redirect після видалення
        self.assertEqual(response.status_code, 302)
        # Нотатка ВИДАЛЕНА з БД
        self.assertFalse(Note.objects.filter(pk=pk).exists())

    def test_non_owner_cannot_delete_gets_404(self):
        """
        Bob (не власник) намагається видалити нотатку Alice → 404.
        Нотатка залишається в БД.
        """
        pk = self.alice_note.pk
        self.client.force_login(self.bob)
        response = self.client.post(
            reverse('hello_app:note_delete', args=[pk])
        )
        self.assertEqual(response.status_code, 404)
        # Нотатка НЕ видалена
        self.assertTrue(Note.objects.filter(pk=pk).exists())

    def test_delete_get_shows_confirm_page(self):
        """GET /notes/<pk>/delete/ → сторінка підтвердження (200 OK)."""
        self.client.force_login(self.alice)
        response = self.client.get(
            reverse('hello_app:note_delete', args=[self.alice_note.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_delete_redirects_to_note_list(self):
        """Після успішного видалення → redirect до note_list."""
        self.client.force_login(self.alice)
        response = self.client.post(
            reverse('hello_app:note_delete', args=[self.alice_note.pk])
        )
        self.assertRedirects(response, reverse('hello_app:note_list'),
                             fetch_redirect_response=False)


# ─────────────────────────────────────────────────────────────────────────────
# 7. NOTEBOOK VIEWS — ownership enforcement
# ─────────────────────────────────────────────────────────────────────────────

class NotebookViewTest(BaseViewTest):
    """
    Notebook edit/delete використовують:
      get_object_or_404(Notebook, pk=pk, user=request.user)
    → якщо notebook.user != request.user → 404

    Відмінність від note_edit: notebook не має групового доступу.
    Тому 404 для будь-якого чужого юзера, без умов.
    """

    def test_notebook_list_shows_own_notebooks(self):
        """Alice бачить свій записник у списку."""
        self.client.force_login(self.alice)
        response = self.client.get(reverse('hello_app:notebook_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alice Notebook')

    def test_notebook_list_excludes_other_users(self):
        """Alice НЕ бачить записники Bob'а."""
        Notebook.objects.create(user=self.bob, title='Bob Secret Notebook')
        self.client.force_login(self.alice)
        response = self.client.get(reverse('hello_app:notebook_list'))
        self.assertNotContains(response, 'Bob Secret Notebook')

    def test_non_owner_cannot_edit_notebook(self):
        """
        Bob намагається GET notebook_edit Alice → 404.
        get_object_or_404(Notebook, pk=pk, user=request.user) не знаходить.
        """
        self.client.force_login(self.bob)
        response = self.client.get(
            reverse('hello_app:notebook_edit', args=[self.alice_notebook.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_non_owner_cannot_delete_notebook(self):
        """Bob намагається POST notebook_delete Alice → 404."""
        self.client.force_login(self.bob)
        response = self.client.post(
            reverse('hello_app:notebook_delete', args=[self.alice_notebook.pk])
        )
        self.assertEqual(response.status_code, 404)
        # Записник не видалений
        self.assertTrue(Notebook.objects.filter(pk=self.alice_notebook.pk).exists())


# ─────────────────────────────────────────────────────────────────────────────
# 8. GROUP VIEWS — membership check
# ─────────────────────────────────────────────────────────────────────────────

class GroupViewTest(BaseViewTest):
    """
    Перевіряємо access control для Django Groups.

    group_detail перевіряє членство через:
      selectors.get_group_with_members(pk, request.user)
      → повертає None якщо не член → Http404 у view

    group_delete перевіряє через:
      group.user_set.filter(pk=request.user.pk).exists()
      → PermissionDenied (403) якщо не член
    """

    def test_group_list_returns_200_for_authenticated(self):
        """Залогінений юзер може переглянути список груп — 200 OK."""
        self.client.force_login(self.alice)
        response = self.client.get(reverse('hello_app:group_list'))
        self.assertEqual(response.status_code, 200)

    def test_create_group_adds_creator_as_member(self):
        """
        POST /groups/new/ → група створена + Alice автоматично стала членом.

        services.create_group(name=..., creator=alice) додає alice до group.user_set.
        Цей тест через HTTP перевіряє що view правильно передає creator=request.user.
        """
        self.client.force_login(self.alice)
        self.client.post(
            reverse('hello_app:group_create'),
            data={'name': 'Test Group'},
        )
        group = Group.objects.get(name='Test Group')
        self.assertIn(self.alice, group.user_set.all())

    def test_non_member_cannot_access_group_detail(self):
        """
        Bob (не член групи) намагається переглянути деталі групи → 404.
        """
        group = Group.objects.create(name='Private Group')
        self.alice.groups.add(group)  # тільки Alice

        self.client.force_login(self.bob)
        response = self.client.get(
            reverse('hello_app:group_detail', args=[group.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_member_can_view_group_detail(self):
        """Член групи може переглянути деталі → 200 OK."""
        group = Group.objects.create(name='Open Group')
        self.alice.groups.add(group)

        self.client.force_login(self.alice)
        response = self.client.get(
            reverse('hello_app:group_detail', args=[group.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_non_member_delete_returns_403(self):
        """
        Bob (не член) намагається видалити групу → 403 Forbidden.

        Відмінність від note: тут PermissionDenied, а не Http404.
        Обидва підходи правильні — залежить від контексту.
        """
        group = Group.objects.create(name='Alice Group')
        self.alice.groups.add(group)

        self.client.force_login(self.bob)
        response = self.client.post(
            reverse('hello_app:group_delete', args=[group.pk])
        )
        self.assertEqual(response.status_code, 403)
        # Група не видалена
        self.assertTrue(Group.objects.filter(pk=group.pk).exists())


# ─────────────────────────────────────────────────────────────────────────────
# 9. TODOLIST SHARING — спільний доступ
# ─────────────────────────────────────────────────────────────────────────────

class TodoListSharingViewTest(BaseViewTest):
    """
    Тестуємо функцію "поділитись" для TodoList.

    ЛОГІКА ДОСТУПУ:
      selectors.get_todo_list_detail(user, pk) повертає список якщо:
        - user == todo.user (власник)
        - user in todo.shared_with.all() (поділились)
      Інакше → None → Http404

    SHARING WORKFLOW:
      POST /todo/<pk>/share/ з username='bob' → bob доданий до shared_with
      Тепер bob може GET /todo/<pk>/ → 200 OK
    """

    def setUp(self):
        super().setUp()
        self.alice_todo = TodoList.objects.create(
            user=self.alice, title='Alice Shopping'
        )

    def test_owner_can_view_todo_list(self):
        """Alice (власниця) переглядає свій список → 200 OK."""
        self.client.force_login(self.alice)
        response = self.client.get(
            reverse('hello_app:todo_detail', args=[self.alice_todo.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_non_owner_non_shared_gets_404(self):
        """
        Bob (не власник, не в shared_with) намагається переглянути → 404.
        """
        self.client.force_login(self.bob)
        response = self.client.get(
            reverse('hello_app:todo_detail', args=[self.alice_todo.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_shared_user_can_view_todo_list(self):
        """
        Alice поділилась списком з Bob'ом.
        Bob тепер може переглянути список → 200 OK.

        Тест перевіряє end-to-end sharing workflow через HTTP.
        """
        # Alice shares with Bob
        self.client.force_login(self.alice)
        self.client.post(
            reverse('hello_app:todo_share', args=[self.alice_todo.pk]),
            data={'username': 'bob'},
        )

        # Bob can now view the list
        self.client.force_login(self.bob)
        response = self.client.get(
            reverse('hello_app:todo_detail', args=[self.alice_todo.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_share_with_nonexistent_user_shows_error(self):
        """
        Alice намагається поділитись з неіснуючим юзером.
        POST → 200 (ре-рендер) + error у контексті (не crash!).

        services.share_todo_list() повертає (False, 'повідомлення про помилку').
        View передає error= до шаблону.
        """
        self.client.force_login(self.alice)
        response = self.client.post(
            reverse('hello_app:todo_share', args=[self.alice_todo.pk]),
            data={'username': 'nonexistent_user_xyz'},
        )
        self.assertEqual(response.status_code, 200)
        # error переданий у контекст шаблону
        self.assertIsNotNone(response.context.get('error'))
