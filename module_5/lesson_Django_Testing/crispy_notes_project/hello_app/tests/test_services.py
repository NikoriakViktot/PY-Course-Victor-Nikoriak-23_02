"""
════════════════════════════════════════════════════════════════════════════════
test_services.py — Unit тести для services.py

Запуск:
    python manage.py test hello_app.tests.test_services -v 2
════════════════════════════════════════════════════════════════════════════════

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
НАВІЩО ТЕСТУВАТИ СЕРВІСИ?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

services.py — це бізнес-логіка додатку. Саме тут:
  • Перевіряється ownership (нотатка belongs to user)
  • Виконуються транзакції (кілька операцій в одному atomic блоці)
  • Обробляються edge cases (шерінг з неіснуючим юзером)

БЕЗ ТЕСТІВ СЕРВІСІВ → найнебезпечніші баги:
  • create_notebook(is_default=True) не скидає старий default →
    у юзера два "дефолтних" записники → непередбачувана поведінка форм
  • create_note(tag_ids=[bob_tag_id]) додає чужий тег →
    Alice бачить теги Bob'а у своїй нотатці
  • add_user_to_group() дозволяє дублікати →
    один юзер додається двічі → COUNT(*) показує неправильно

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ЧОМУ СЕРВІСИ ЛЕГКО ТЕСТУВАТИ?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Функції сервісів НЕ залежать від HTTP (request, response, session).
Вони приймають прості Python-об'єкти і повертають результат:

    services.create_note(user=alice, title='Test')  ← прямий виклик
    # ≠
    self.client.post('/notes/new/', {'title': 'Test'})  ← через HTTP

Сервіс можна тестувати "в ізоляції" без запуску веб-сервера.
Це робить тести швидкими і точними.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ШАБЛОН КОЖНОГО ТЕСТУ СЕРВІСУ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def test_service_does_something(self):
        # ARRANGE: підготовка об'єктів у тестовій БД
        user = User.objects.create_user(...)
        tag = Tag.objects.create(...)

        # ACT: виклик сервісу
        result = services.create_note(user=user, title='...')

        # ASSERT: перевірка результату АБО стану БД
        self.assertEqual(result.title, '...')       # перевіряємо повернений об'єкт
        self.assertEqual(Note.objects.count(), 1)   # перевіряємо стан БД
"""

from django.contrib.auth.models import Group, User
from django.test import TestCase

from hello_app import services
from hello_app.models import Note, Notebook, Tag, TodoList


# ─────────────────────────────────────────────────────────────────────────────
# Базовий клас: уникаємо дублювання setUp у кожному класі
# ─────────────────────────────────────────────────────────────────────────────

class BaseServiceTest(TestCase):
    """
    Базовий клас для всіх сервісних тестів.

    Два користувачі (alice, bob) потрібні для тестів ізоляції:
    "операція Alice не зачіпає дані Bob'а" і навпаки.

    Наслідування через super().setUp() гарантує що базовий setUp
    завжди викликається перед setUp дочірнього класу.
    """

    def setUp(self):
        self.alice = User.objects.create_user('alice', password='pass123')
        self.bob = User.objects.create_user('bob', password='pass123')


# ═════════════════════════════════════════════════════════════════════════════
# ТЕСТИ: services.create_note / delete_note / toggle_pin_note
# ═════════════════════════════════════════════════════════════════════════════

class NoteServiceTest(BaseServiceTest):
    """
    Тести для основних операцій з нотатками.

    create_note() — атомарна операція: створює Note + призначає теги.
    toggle_pin_note() — використовує F() expression для flip без race condition.
    delete_note() — каскадно видаляє всі Reminder.
    """

    def test_create_note_returns_note_object(self):
        """
        ЩО ПЕРЕВІРЯЄМО: create_note() повертає екземпляр Note.

        НАВІЩО: views.py робить так:
            note = services.create_note(user=request.user, title=...)
            return redirect('note_detail', pk=note.pk)

        Якщо create_note() раптом поверне None або словник замість Note —
        наступний .pk вибухне з AttributeError.

        assertIsInstance(note, Note) — перевіряємо тип, а не просто
        що note != None.
        """
        note = services.create_note(user=self.alice, title='Test Note')
        self.assertIsInstance(note, Note)

    def test_create_note_saves_to_database(self):
        """
        ЩО ПЕРЕВІРЯЄМО: після create_note() у БД справді є 1 нотатка.

        НАВІЩО: теоретично функція могла б створити об'єкт в пам'яті
        але не зберегти його (.save() забули). Перевірка через
        Note.objects.count() == 1 підтверджує що дані справді в БД.

        РІЗНИЦЯ від попереднього тесту:
          test_create_note_returns_note_object → перевіряє повернений об'єкт
          test_create_note_saves_to_database  → перевіряє стан БД
        Обидва важливі — об'єкт може бути в пам'яті але не в БД.
        """
        services.create_note(user=self.alice, title='DB Note')
        self.assertEqual(Note.objects.count(), 1)

    def test_create_note_sets_correct_user(self):
        """
        ЩО ПЕРЕВІРЯЄМО: нотатка створюється для правильного користувача.

        НАВІЩО: це ключовий security тест сервісного рівня.
        Якщо create_note(user=alice) раптом збереже нотатку з user=bob —
        Alice побачить чужі нотатки і навпаки. IDOR (Insecure Direct
        Object Reference) — критична вразливість у веб-додатках.

        NOTE.OBJECTS.FILTER(user=alice) не поверне нотатку якщо user=bob.
        Цей тест перевіряє що сервіс правильно передає user.
        """
        note = services.create_note(user=self.alice, title='Alice Note')
        self.assertEqual(note.user, self.alice)

    def test_create_note_sets_title(self):
        """
        ЩО ПЕРЕВІРЯЄМО: title нотатки зберігається без змін.

        НАВІЩО: може здатись очевидним, але:
          1. Документує очікувану поведінку (specification as test)
          2. Виявляє якщо title раптом truncate-иться або escaping-ується
          3. Якщо хтось додасть "нормалізацію" title у create_note —
             цей тест одразу покаже що title змінився

        ПРИНЦИП: "Obvious code still needs tests, because specifications change."
        """
        note = services.create_note(user=self.alice, title='My Title')
        self.assertEqual(note.title, 'My Title')

    def test_create_note_default_priority_is_low(self):
        """
        ЩО ПЕРЕВІРЯЄМО: якщо priority не вказано — дефолт PRIORITY_LOW (1).

        НАВІЩО: у view note_create() передається тільки form.cleaned_data
        без явного priority (якщо форма не заповнена). Якщо дефолт у
        сервісі зміниться — нові нотатки матимуть несподіваний пріоритет.

        NOTE.PRIORITY_LOW — константа, тому якщо хтось змінить значення
        константи (наприклад з 1 на 0) — тест теж це виявить.
        """
        note = services.create_note(user=self.alice, title='Test')
        self.assertEqual(note.priority, Note.PRIORITY_LOW)

    def test_create_note_custom_priority(self):
        """
        ЩО ПЕРЕВІРЯЄМО: явно переданий priority зберігається правильно.

        НАВІЩО: разом з попереднім тестом (default) — ці два тести
        документують поведінку priority:
          • Без priority → 1 (LOW)
          • З priority=4 → 4 (URGENT)

        Якщо хтось додасть "захист" в create_note що обмежує priority
        до 1-3 — цей тест виявить що PRIORITY_URGENT (4) не зберігається.
        """
        note = services.create_note(
            user=self.alice, title='Urgent', priority=Note.PRIORITY_URGENT
        )
        self.assertEqual(note.priority, Note.PRIORITY_URGENT)

    def test_create_note_assigns_tags(self):
        """
        ЩО ПЕРЕВІРЯЄМО: теги з tag_ids правильно призначаються нотатці.

        НАВІЩО: create_note() використовує note.tags.set(valid_tags).
        M:N зв'язок — особливий: просто .save() не зберігає теги.
        Потрібен явний .set() або .add(). Якщо цей рядок видалити —
        нотатка збережеться без тегів і тест одразу виявить проблему.

        КОД у services.py:
            if tag_ids:
                valid_tags = Tag.objects.filter(id__in=tag_ids, user=user)
                note.tags.set(valid_tags)   ← без цього тест провалиться

        assertIn(tag, note_tags): перевіряємо що КОЖЕН тег присутній.
        """
        tag1 = Tag.objects.create(user=self.alice, name='work')
        tag2 = Tag.objects.create(user=self.alice, name='python')

        note = services.create_note(
            user=self.alice, title='Tagged', tag_ids=[tag1.id, tag2.id]
        )

        note_tags = list(note.tags.all())
        self.assertIn(tag1, note_tags)
        self.assertIn(tag2, note_tags)

    def test_create_note_ignores_other_users_tags(self):
        """
        ЩО ПЕРЕВІРЯЄМО: якщо передати tag_id що belongs до Bob'а —
        він НЕ призначається нотатці Alice.

        НАВІЩО: це security тест — Mass Assignment вразливість.
        Якщо зловмисник надішле POST з чужим tag_id:
            POST /notes/new/ → tag_ids=[bob_secret_tag_id]
        — без фільтрації Alice побачить теги Bob'а у своїй нотатці.

        КОД у services.py (захист):
            valid_tags = Tag.objects.filter(id__in=tag_ids, user=user)
            #                                              ^^^^^^^^^^
            #                              Фільтрація по user — ключовий рядок!

        Якщо цей фільтр прибрати — цей тест провалиться і виявить вразливість.
        """
        bob_tag = Tag.objects.create(user=self.bob, name='bob-secret')

        # Alice передає ID тегу Bob'а — зловмисна або помилкова дія
        note = services.create_note(
            user=self.alice, title='Alice Note', tag_ids=[bob_tag.id]
        )

        # Тег Bob'а НЕ має бути призначений нотатці Alice
        self.assertEqual(note.tags.count(), 0)

    def test_create_note_no_tags_by_default(self):
        """
        ЩО ПЕРЕВІРЯЄМО: нотатка без tag_ids створюється без тегів (не з всіма тегами).

        НАВІЩО: перевіряємо що при відсутності tag_ids сервіс не призначає
        "всі теги юзера" або не кидає виняток. tags.count() == 0 — clean state.
        """
        note = services.create_note(user=self.alice, title='No Tags')
        self.assertEqual(note.tags.count(), 0)

    def test_toggle_pin_note_pins_unpinned_note(self):
        """
        ЩО ПЕРЕВІРЯЄМО: toggle_pin_note() змінює is_pinned=False на True.

        НАВІЩО: toggle = перемикач. При першому виклику — закріплює.
        При другому — знімає. Це інваріант функції.

        КОД у services.py:
            Note.objects.filter(pk=note.pk).update(is_pinned=~F('is_pinned'))
            note.refresh_from_db(fields=['is_pinned'])

        F('is_pinned') — Django ORM вираз що читає поточне значення
        і перевертає його АТОМАРНО на рівні БД (без race condition).
        """
        note = Note.objects.create(user=self.alice, title='Test', is_pinned=False)
        updated = services.toggle_pin_note(note)
        self.assertTrue(updated.is_pinned)

    def test_toggle_pin_note_unpins_pinned_note(self):
        """
        ЩО ПЕРЕВІРЯЄМО: toggle_pin_note() змінює is_pinned=True на False.

        НАВІЩО: разом з попереднім тестом документуємо ОБА напрями toggle.
        Якщо хтось випадково написав is_pinned=True (замість ~F('is_pinned')) —
        цей тест виявить що вже закріплена нотатка не знімає закріплення.
        """
        note = Note.objects.create(user=self.alice, title='Test', is_pinned=True)
        updated = services.toggle_pin_note(note)
        self.assertFalse(updated.is_pinned)

    def test_toggle_pin_note_persisted_in_db(self):
        """
        ЩО ПЕРЕВІРЯЄМО: зміна is_pinned зберігається у БД, а не тільки в пам'яті.

        НАВІЩО: це один з найважливіших видів тестів для сервісів —
        "чи дані справді збереглися?". Функція могла б змінити
        note.is_pinned в пам'яті але не викликати .save().

        КЛЮЧОВА РІЗНИЦЯ від попередніх тестів:
          Попередні: перевіряємо повернений об'єкт updated
          Цей: свіжо завантажуємо з БД і перевіряємо там

          note_from_db = Note.objects.get(pk=note.pk)  ← новий запит до БД

        Це "persistence test" — перевірка що дані справді зберіглися.
        """
        note = Note.objects.create(user=self.alice, title='Test', is_pinned=False)
        services.toggle_pin_note(note)

        # Завантажуємо свіжий об'єкт з БД — ігноруємо кешований в пам'яті
        note_from_db = Note.objects.get(pk=note.pk)
        self.assertTrue(note_from_db.is_pinned)

    def test_delete_note_removes_from_db(self):
        """
        ЩО ПЕРЕВІРЯЄМО: після delete_note() нотатки більше немає в БД.

        НАВІЩО: views.py:
            services.delete_note(note)
            return redirect('note_list')

        Якщо delete_note() не видаляє (наприклад archive замість delete) —
        юзер думає що видалив, але нотатка лишилась. Privacy issue.

        assertFalse(Note.objects.filter(pk=pk).exists()):
          .exists() — ефективний спосіб перевірити наявність без завантаження.
          Краще ніж assertRaises(Note.DoesNotExist, Note.objects.get, pk=pk).
        """
        note = Note.objects.create(user=self.alice, title='To Delete')
        pk = note.pk  # запам'ятовуємо pk ДО видалення

        services.delete_note(note)

        # Перевіряємо що рядку з цим pk більше немає
        self.assertFalse(Note.objects.filter(pk=pk).exists())


# ═════════════════════════════════════════════════════════════════════════════
# ТЕСТИ: services.create_notebook (is_default логіка)
# ═════════════════════════════════════════════════════════════════════════════

class NotebookServiceTest(BaseServiceTest):
    """
    Записники мають важливу бізнес-логіку: тільки ОДИН може бути дефолтним.
    Ця логіка реалізована через транзакцію: спочатку скидаємо старий default,
    потім встановлюємо новий.
    """

    def test_create_notebook_saves_to_db(self):
        """
        ЩО ПЕРЕВІРЯЄМО: create_notebook() зберігає запис у БД.

        НАВІЩО: базовий smoke test. Якщо навіть збереження не працює —
        далі нема сенсу тестувати деталі.
        """
        services.create_notebook(user=self.alice, title='Work')
        self.assertEqual(Notebook.objects.count(), 1)

    def test_create_notebook_not_default_by_default(self):
        """
        ЩО ПЕРЕВІРЯЄМО: новий записник без is_default=True → is_default=False.

        НАВІЩО: якщо записник дефолтний без запиту — він автоматично
        отримує нові нотатки. Несподівана поведінка для юзера.
        """
        nb = services.create_notebook(user=self.alice, title='Notes')
        self.assertFalse(nb.is_default)

    def test_create_notebook_as_default(self):
        """
        ЩО ПЕРЕВІРЯЄМО: is_default=True зберігається.

        НАВІЩО: явна перевірка що параметр is_default=True не ігнорується.
        Разом з попереднім тестом: дефолт = False, дефолт = True — обидва сценарії.
        """
        nb = services.create_notebook(user=self.alice, title='Main', is_default=True)
        self.assertTrue(nb.is_default)

    def test_create_notebook_default_unsets_previous_default(self):
        """
        ЩО ПЕРЕВІРЯЄМО: при створенні нового default записника —
        старий default автоматично скидається.

        НАВІЩО: це КЛЮЧОВИЙ бізнес-інваріант — у юзера може бути тільки
        ОДИН дефолтний записник. Якщо їх два — в яку нотатку піде нова нотатка?
        Форма вибере перший чи останній? Поведінка стає непередбачуваною.

        КОД у services.py (транзакційна логіка):
            with transaction.atomic():
                if is_default:
                    Notebook.objects.filter(user=user, is_default=True).update(is_default=False)
                    #  ^^^^ СКИДАЄМО старий default ^^^^
                return Notebook.objects.create(..., is_default=is_default)
                #      ^^^^ СТВОРЮЄМО новий ^^^^

        Якщо прибрати рядок з .update(is_default=False) — обидва
        записники матимуть is_default=True і цей тест це виявить.

        refresh_from_db() — КРИТИЧНО:
            old_default — об'єкт у пам'яті, він не знає що БД змінилась.
            Без refresh_from_db() old_default.is_default ще True в пам'яті!
        """
        # Arrange — спочатку Alice має один default записник
        old_default = services.create_notebook(
            user=self.alice, title='Old Default', is_default=True
        )
        self.assertTrue(old_default.is_default)  # переконуємось що встановлено

        # Act — створюємо другий default
        new_default = services.create_notebook(
            user=self.alice, title='New Default', is_default=True
        )

        # Assert — старий скинутий, новий встановлений
        old_default.refresh_from_db()             # читаємо свіжий стан з БД!
        self.assertFalse(old_default.is_default)  # старий скинутий
        self.assertTrue(new_default.is_default)   # новий встановлений

    def test_create_notebook_default_only_affects_same_user(self):
        """
        ЩО ПЕРЕВІРЯЄМО: коли Alice встановлює свій default записник —
        default записник Bob'а не змінюється.

        НАВІЩО: ізоляція між користувачами. Без фільтра user= в запиті:
            Notebook.objects.filter(is_default=True).update(...)
            ^^^^ БЕЗ user= — скине дефолт У ВСІХ ЮЗЕРІВ! ^^^^

        КОД (правильно):
            Notebook.objects.filter(user=user, is_default=True).update(...)
            ^^^^ З user= — скидає тільки для одного юзера ^^^^

        Це класична помилка при multi-tenant системах. Тест виявляє її.
        """
        # Arrange — Bob має свій default
        bob_default = services.create_notebook(
            user=self.bob, title='Bob Default', is_default=True
        )

        # Act — Alice встановлює свій default (не Bob!)
        services.create_notebook(
            user=self.alice, title='Alice Default', is_default=True
        )

        # Assert — Bob Default залишився нетронутим
        bob_default.refresh_from_db()
        self.assertTrue(bob_default.is_default)  # Bob не зачіпається


# ═════════════════════════════════════════════════════════════════════════════
# ТЕСТИ: services.create_or_get_tag (idempotent операція)
# ═════════════════════════════════════════════════════════════════════════════

class TagServiceTest(BaseServiceTest):
    """
    create_or_get_tag — idempotent операція (get_or_create).
    Викликати двічі з тими ж параметрами = той самий результат, без дублікатів.
    """

    def test_create_new_tag(self):
        """
        ЩО ПЕРЕВІРЯЄМО: перший виклик → створює тег, created=True.

        НАВІЩО: get_or_create повертає (object, created_bool).
        created=True означає що тег був НОВИЙ. Якщо повертається created=False
        при першому виклику — щось дивне (тег вже існував без нашого відома).
        """
        tag, created = services.create_or_get_tag(user=self.alice, name='python')

        self.assertTrue(created)            # новий тег
        self.assertEqual(tag.name, 'python')

    def test_get_existing_tag(self):
        """
        ЩО ПЕРЕВІРЯЄМО: другий виклик з тою ж назвою → повертає ІСНУЮЧИЙ тег,
        created=False. Новий тег НЕ створюється.

        НАВІЩО: idempotency — ключова властивість для зовнішніх API і форм.
        Якщо юзер двічі натисне "Створити тег python" — має отримати один тег,
        а не два. Без get_or_create була б помилка unique_together.

        ПЕРЕВІРЯЄМО tag1.pk == tag2.pk: це впевнює що це ОДИН І ТОЙ САМИЙ
        об'єкт у БД (не просто з однаковою назвою).
        """
        tag1, _ = services.create_or_get_tag(user=self.alice, name='python')
        tag2, created = services.create_or_get_tag(user=self.alice, name='python')

        self.assertFalse(created)        # не новий — вже існував
        self.assertEqual(tag1.pk, tag2.pk)  # той самий рядок у БД

    def test_tag_name_normalized_to_lowercase(self):
        """
        ЩО ПЕРЕВІРЯЄМО: назва нормалізується: '  Python  ' → 'python'.

        НАВІЩО: без нормалізації 'Python', 'python', '  python  ' стали б
        РІЗНИМИ тегами. У юзера накопичились би дублікати:
          'python', 'Python', 'PYTHON', '  python  '

        КОД у services.py:
            tag, created = Tag.objects.get_or_create(
                user=user,
                name=name.lower().strip(),   ← нормалізація
                defaults={'color': color}
            )

        ПРИМІТКА: тест перевіряє що після нормалізації
        tag.name == 'python', а created=True (новий нормалізований тег).
        """
        tag, created = services.create_or_get_tag(user=self.alice, name='  Python  ')

        self.assertEqual(tag.name, 'python')  # нормалізовано
        self.assertTrue(created)

    def test_same_name_different_users_creates_separate_tags(self):
        """
        ЩО ПЕРЕВІРЯЄМО: Alice і Bob можуть мати теги з однаковою назвою —
        це РІЗНІ об'єкти у БД.

        НАВІЩО: теги ізольовані per-user. Якщо get_or_create не фільтрує
        по user — Alice отримає тег Bob'а замість свого. Це data leakage.

        КОД (правильно):
            Tag.objects.get_or_create(user=user, name=..., ...)
            ^^^^^ фільтрує по user — кожен юзер має свої теги ^^^^^
        """
        alice_tag, _ = services.create_or_get_tag(user=self.alice, name='work')
        bob_tag, _ = services.create_or_get_tag(user=self.bob, name='work')

        self.assertNotEqual(alice_tag.pk, bob_tag.pk)  # різні рядки у БД
        self.assertEqual(Tag.objects.count(), 2)        # два теги, не один


# ═════════════════════════════════════════════════════════════════════════════
# ТЕСТИ: services для Django Group (групи користувачів)
# ═════════════════════════════════════════════════════════════════════════════

class GroupServiceTest(BaseServiceTest):
    """
    Group — Django вбудована модель для груп (Сім'я, Команда).
    Дозволяє шерити нотатки між членами групи.
    """

    def test_create_group_creates_django_group(self):
        """
        ЩО ПЕРЕВІРЯЄМО: create_group() повертає Group з правильною назвою.

        НАВІЩО: базова перевірка що сервіс повертає Group (не None, не dict).
        assertIsInstance(group, Group) + assertEqual(name) = повна перевірка.
        """
        group = services.create_group(name='Family', creator=self.alice)

        self.assertIsInstance(group, Group)
        self.assertEqual(group.name, 'Family')

    def test_create_group_adds_creator_as_member(self):
        """
        ЩО ПЕРЕВІРЯЄМО: творець групи автоматично стає членом після створення.

        НАВІЩО: це UX-вимога — коли Alice створює групу, вона відразу
        є її членом. Якщо цей рядок пропустити — Alice побачить групу
        у списку, але не зможе взаємодіяти як член.

        КОД у services.py:
            group = Group.objects.create(name=name)
            group.user_set.add(creator)   ← Alice стає членом
        """
        group = services.create_group(name='Team', creator=self.alice)
        self.assertIn(self.alice, group.user_set.all())

    def test_create_group_creator_is_only_initial_member(self):
        """
        ЩО ПЕРЕВІРЯЄМО: відразу після створення у групі є тільки 1 член (творець).

        НАВІЩО: перевіряємо що create_group() не додає зайвих членів.
        Якщо через баг додається кожен існуючий юзер — group.user_set.count()
        буде > 1 і цей тест це покаже.
        """
        group = services.create_group(name='Solo', creator=self.alice)
        self.assertEqual(group.user_set.count(), 1)

    def test_add_user_to_group_success(self):
        """
        ЩО ПЕРЕВІРЯЄМО: add_user_to_group() додає Bob'а до групи і повертає (True, '').

        НАВІЩО: happy path тест. Перевіряємо ОБА аспекти результату:
          1. success=True — сервіс повідомляє про успіх
          2. Bob справді є у group.user_set.all() — перевіряємо БД

        Перевірка обох аспектів важлива: сервіс може повернути True
        але не додати юзера (або додати юзера без повернення True).
        """
        group = services.create_group(name='Friends', creator=self.alice)

        success, message = services.add_user_to_group(group, username='bob')

        self.assertTrue(success)
        self.assertEqual(message, '')               # порожнє повідомлення при успіху
        self.assertIn(self.bob, group.user_set.all())

    def test_add_user_to_group_nonexistent_user(self):
        """
        ЩО ПЕРЕВІРЯЄМО: якщо юзера 'nobody' немає в БД — повертається
        (False, повідомлення з ім'ям юзера).

        НАВІЩО: у view group_detail це виглядає так:
            success, message = services.add_user_to_group(group, username)
            if not success:
                messages.error(request, message)

        Якщо success=True при помилці — view не покаже помилку юзеру.
        Якщо 'nobody' не у message — юзер не зрозуміє хто не знайдений.

        КОД у services.py:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return False, f'Користувача «{username}» не знайдено.'
        """
        group = services.create_group(name='Test', creator=self.alice)

        success, message = services.add_user_to_group(group, username='nobody')

        self.assertFalse(success)
        self.assertIn('nobody', message)  # ім'я юзера є у повідомленні

    def test_add_user_to_group_duplicate_returns_false(self):
        """
        ЩО ПЕРЕВІРЯЄМО: спроба додати вже існуючого члена групи →
        (False, повідомлення) + кількість членів НЕ збільшується.

        НАВІЩО: без цього захисту член може бути доданий двічі.
        Django M2M зазвичай запобігає дублікатам на рівні БД,
        але без перевірки:
          1. Сервіс повертає True — view показує "успішно додано"
          2. Юзер бачить дивний UX — "bob є членом" але щойно "додали" знову

        ТАКОЖ: ми перевіряємо що count() == 2 (alice + bob, не 3).
        Це додаткова страховка що дублікат справді не з'явився.
        """
        group = services.create_group(name='Dup', creator=self.alice)
        services.add_user_to_group(group, username='bob')  # 1й раз — успіх

        # 2й раз — bob вже є членом
        success, message = services.add_user_to_group(group, username='bob')

        self.assertFalse(success)
        self.assertIn('bob', message)
        self.assertEqual(group.user_set.count(), 2)  # alice + bob (не 3!)

    def test_remove_user_from_group(self):
        """
        ЩО ПЕРЕВІРЯЄМО: remove_user_from_group() видаляє юзера з групи.

        НАВІЩО: у view group_detail юзер може покинути групу або адмін
        може видалити члена. Якщо remove не працює — юзер "виходить" але
        залишається членом і бачить спільні нотатки.
        """
        group = services.create_group(name='ToLeave', creator=self.alice)
        group.user_set.add(self.bob)  # додаємо Bob'а напряму (не через сервіс)

        services.remove_user_from_group(group, self.bob)

        self.assertNotIn(self.bob, group.user_set.all())

    def test_delete_group_removes_group(self):
        """
        ЩО ПЕРЕВІРЯЄМО: delete_group() видаляє групу з БД.

        НАВІЩО: базова перевірка що delete справді видаляє. Якщо замість
        видалення сервіс робить soft-delete або просто очищає членів —
        Group.objects.filter(pk=group_pk).exists() все ще True.
        """
        group = services.create_group(name='ToDelete', creator=self.alice)
        group_pk = group.pk

        services.delete_group(group)

        self.assertFalse(Group.objects.filter(pk=group_pk).exists())

    def test_delete_group_sets_note_group_to_null(self):
        """
        ЩО ПЕРЕВІРЯЄМО: при видаленні групи нотатки НЕ видаляються —
        вони стають особистими (note.group = None).

        НАВІЩО: це наслідок Note.group = ForeignKey(Group, on_delete=SET_NULL).
        Але тест потрібен щоб ДОКУМЕНТУВАТИ і ЗАХИСТИТИ цю поведінку.

        Якщо хтось змінить on_delete=SET_NULL на on_delete=CASCADE:
          • Всі нотатки групи ВИДАЛЯТЬСЯ при видаленні групи
          • Юзер втратить всі записи — критична втрата даних!
          • Цей тест одразу виявить цю зміну

        refresh_from_db() — читаємо свіжий стан нотатки з БД після
        видалення групи. Без цього note.group ще 'в пам'яті' вказує на групу.
        """
        group = services.create_group(name='ToDelete', creator=self.alice)
        note = Note.objects.create(user=self.alice, title='Group Note', group=group)

        services.delete_group(group)
        note.refresh_from_db()  # ОБОВ'ЯЗКОВО — читаємо свіжий стан з БД

        self.assertIsNone(note.group)  # нотатка стала особистою, не видалена


# ═════════════════════════════════════════════════════════════════════════════
# ТЕСТИ: services.share_todo_list
# ═════════════════════════════════════════════════════════════════════════════

class TodoListServiceTest(BaseServiceTest):
    """
    Шерінг списку справ з іншими користувачами.
    Тут важливо перевіряти edge cases: неіснуючий юзер, шерінг із собою.
    """

    def setUp(self):
        super().setUp()  # <- обов'язково викликаємо базовий setUp!
        # Додаткова підготовка специфічна для цього класу
        self.todo_list = services.create_todo_list(
            user=self.alice, title='Alice Shopping'
        )

    def test_share_todo_list_with_existing_user(self):
        """
        ЩО ПЕРЕВІРЯЄМО: share_todo_list() успішно шерить список з Bob'ом.

        НАВІЩО: happy path — перевіряємо що шерінг працює в нормальних умовах.
        Після шерінгу Bob має бачити список у своєму shared_todo_lists.

        ПЕРЕВІРЯЄМО ДВА АСПЕКТИ:
          1. success=True — функція повідомляє про успіх
          2. bob ∈ shared_with — BD фактично оновлена
        """
        success, message = services.share_todo_list(self.todo_list, 'bob')

        self.assertTrue(success)
        self.assertIn(self.bob, self.todo_list.shared_with.all())

    def test_share_todo_list_with_nonexistent_user(self):
        """
        ЩО ПЕРЕВІРЯЄМО: шерінг з неіснуючим юзером → (False, повідомлення).

        НАВІЩО: юзер може помилитись у username. Сервіс має коректно
        обробити цей випадок і повернути зрозуміле повідомлення.

        КОД у services.py:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return False, f'Користувача «{username}» не знайдено.'

        assertIn('nobody', message) — перевіряємо що помилка містить
        ім'я того, кого не знайшли. Це допомагає юзеру зрозуміти проблему.
        """
        success, message = services.share_todo_list(self.todo_list, 'nobody')

        self.assertFalse(success)
        self.assertIn('nobody', message)

    def test_share_todo_list_with_self_returns_false(self):
        """
        ЩО ПЕРЕВІРЯЄМО: Alice не може поділитись списком із самою собою.

        НАВІЩО: поділитись із собою — логічна нісенітниця. Alice вже
        є власником списку. Якщо сервіс дозволить це:
          1. Alice з'являється у shared_with (хоч і так є власником)
          2. При видаленні sharing список залишиться у двох "версіях"
          3. COUNT виходить неправильним

        КОД у services.py:
            if user == todo_list.user:
                return False, 'Не можна поділитись із собою.'

        assertNotIn(alice, shared_with): перевіряємо що Alice не
        потрапила до shared_with навіть після спроби.
        """
        success, message = services.share_todo_list(self.todo_list, 'alice')

        self.assertFalse(success)
        self.assertNotIn(self.alice, self.todo_list.shared_with.all())

    def test_create_todo_list_saved(self):
        """
        ЩО ПЕРЕВІРЯЄМО: create_todo_list() зберігає список у БД для правильного юзера.

        НАВІЩО: setUp() викликає create_todo_list — тут ми перевіряємо що
        він спрацював правильно (базовий smoke test для setUp).
        Якщо create_todo_list повернув None або зберіг для Bob'а — подальші
        тести мали б дивні результати.
        """
        self.assertEqual(TodoList.objects.count(), 1)
        self.assertEqual(self.todo_list.user, self.alice)
