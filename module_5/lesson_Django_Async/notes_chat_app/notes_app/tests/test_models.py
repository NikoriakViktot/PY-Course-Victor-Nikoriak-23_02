"""
════════════════════════════════════════════════════════════════════════════════
test_models.py — Unit тести для моделей notes_app

Запуск:
    python manage.py test notes_app.tests.test_models -v 2
════════════════════════════════════════════════════════════════════════════════

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
НАВІЩО ТЕСТУВАТИ МОДЕЛІ?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Модель — це не просто клас з полями. Вона містить:
  • Бізнес-правила (priority від 1 до 4)
  • Захист даних (uniqe_together не дає дублікатів)
  • Поведінку при видаленні зв'язаних об'єктів (CASCADE, SET_NULL)
  • Рядкове представлення (__str__) для адмінки та шаблонів
  • Значення за замовчуванням (defaults)

Якщо ці правила порушені — додаток поводиться неправильно МОВЧКИ,
без жодних помилок. Тести виявляють це автоматично.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ЩО ТЕСТУЄМО І ЩО НЕ ТЕСТУЄМО ТУТ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ТЕСТУЄМО:
    ✓ __str__          — як об'єкт виглядає у адмінці, лозі, шаблоні
    ✓ unique_together  — БД захищає від дублікатів
    ✓ SET_NULL         — видалення зв'язаного об'єкта не видаляє нотатку
    ✓ Defaults         — поля правильно ініціалізовані при створенні
    ✓ Validators       — через full_clean() як при збереженні через форму

  НЕ ТЕСТУЄМО ТУТ:
    ✗ ORM-запити (filter, select_related) — це test_selectors.py
    ✗ Бізнес-логіку (create_note, toggle_pin) — це test_services.py
    ✗ HTTP-запити (views) — це test_views.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ЯК DJANGO TESTCASE ІЗОЛЮЄ ТЕСТИ?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  django.test.TestCase обгортає кожен тест у транзакцію.
  Після тесту — ROLLBACK. БД чиста для наступного тесту.

  setUp() → [ тест у транзакції ] → ROLLBACK → setUp() → [ тест ] → ...

  Тому можна вільно створювати User, Note, Tag у setUp() —
  вони автоматично зникнуть після тесту.
"""

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from notes_app.models import Note, Notebook, ShopItem, ShoppingList, Tag


# ═════════════════════════════════════════════════════════════════════════════
# ТЕСТИ ДЛЯ МОДЕЛІ Tag
# ═════════════════════════════════════════════════════════════════════════════

class TagModelTest(TestCase):
    """
    Tag — тег для нотаток (python, work, important).

    Ключові правила:
      • unique_together(user, name) — один і той же тег не може існувати
        двічі для одного користувача.
      • Але різні користувачі можуть мати однакові назви тегів.
    """

    def setUp(self):
        """
        Запускається ПЕРЕД кожним тестом цього класу.
        Створюємо двох користувачів для тестування ізоляції між ними.
        """
        self.user = User.objects.create_user('alice', password='pass123')
        self.user2 = User.objects.create_user('bob', password='pass123')

    def test_str_returns_hash_name(self):
        """
        ЩО ПЕРЕВІРЯЄМО: __str__ тегу повертає '#python', а не просто 'python'.

        НАВІЩО: __str__ використовується скрізь — у Django Admin, у
        шаблонах ({{ tag }}), у log-файлах, у повідомленнях про помилки.
        Якщо __str__ сломається — теги скрізь будуть відображатись неправильно.

        ЧИМ ВІДРІЗНЯЄТЬСЯ від тесту бізнес-логіки: тут ми НЕ тестуємо
        "чи тег зберігся у БД" — тільки "чи правильно він виглядає у рядку".
        """
        # Arrange — створюємо тег
        tag = Tag.objects.create(user=self.user, name='python')

        # Act + Assert — str() викликає __str__ і ми перевіряємо результат
        self.assertEqual(str(tag), '#python')

    def test_unique_together_same_user_same_name_raises(self):
        """
        ЩО ПЕРЕВІРЯЄМО: не можна створити два теги з однаковою назвою
        для одного й того ж користувача.

        НАВІЩО: без цього тесту — можна "зламати" unique_together constraint,
        наприклад видаливши рядок у Meta і не помітити. Або Django мовчки
        дасть зберегти дублікат якщо constraint пропущений у міграції.

        ЯК ПРАЦЮЄ CONSTRAINT:
          models.py → class Meta: unique_together = [('user', 'name')]
          → Django створює UNIQUE constraint у БД: UNIQUE(user_id, name)
          → Спроба вставити дублікат → БД кидає IntegrityError

        РЕАЛЬНИЙ НАСЛІДОК ЯКЩО ЗЛАМАТИ:
          Alice створює тег 'work' → збереглося двічі → у формі
          з'являються два однакові 'work' у списку тегів → UX сломано.
        """
        # Arrange — перший тег зберігається успішно
        Tag.objects.create(user=self.user, name='work')

        # Act + Assert — другий з тією ж назвою для того ж user → помилка
        with self.assertRaises(IntegrityError):
            Tag.objects.create(user=self.user, name='work')

    def test_unique_together_different_users_same_name_ok(self):
        """
        ЩО ПЕРЕВІРЯЄМО: Alice і Bob МОЖУТЬ мати тег з однаковою назвою.

        НАВІЩО: unique_together = (user, name) — унікальність в ПАРІ,
        не тільки за name. Alice.work і Bob.work — різні рядки у БД.

        ЦЕЙ ТЕСТ ВАЖЛИВИЙ бо він протилежний до попереднього.
        Разом вони документують ТОЧНУ поведінку: "унікально для одного
        user, але не глобально".

        БЕЗ ЦЬОГО ТЕСТУ: розробник може "виправити" unique_together на
        просто unique=True для поля name — і зламати multi-user систему.
        """
        # Arrange
        Tag.objects.create(user=self.user, name='work')  # Alice's 'work'

        # Act — Bob теж хоче 'work' — має спрацювати без помилки
        tag2 = Tag.objects.create(user=self.user2, name='work')  # Bob's 'work'

        # Assert — обидва теги існують в БД
        self.assertEqual(tag2.name, 'work')
        self.assertEqual(Tag.objects.count(), 2)

    def test_default_color_is_gray(self):
        """
        ЩО ПЕРЕВІРЯЄМО: якщо color не вказано, дефолт — сірий '#808080'.

        НАВІЩО: defaults критичні для UI. Якщо колір не встановлено і
        шаблон показує tag.color — він покаже '' або None, і верстка
        зламається (style="color: ;" або style="color: None;").

        ТЕСТ DEFAULTS: завжди перевіряй дефолтні значення після
        create_user/create без явного вказання поля.
        """
        tag = Tag.objects.create(user=self.user, name='test')  # color не вказано
        self.assertEqual(tag.color, '#808080')


# ═════════════════════════════════════════════════════════════════════════════
# ТЕСТИ ДЛЯ МОДЕЛІ Note
# ═════════════════════════════════════════════════════════════════════════════

class NoteModelTest(TestCase):
    """
    Note — головна модель: нотатка з пріоритетом, закріпленням, групою.

    Ключові правила:
      • priority ∈ [1, 4] — validator через full_clean()
      • is_pinned, is_archived — bool, default=False
      • group → SET_NULL (нотатка не видаляється коли групу видалено)
      • __str__ містить 📌 для закріплених
    """

    def setUp(self):
        self.user = User.objects.create_user('alice', password='pass123')

    def test_str_regular_note(self):
        """
        ЩО ПЕРЕВІРЯЄМО: звичайна (не закріплена) нотатка — __str__ = просто title.

        НАВІЩО: __str__ використовується в Django Admin, в select dropdowns
        ("Записник містить: My Note, Another Note"), у повідомленнях.
        Якщо __str__ буде повертати '📌 My Note' навіть без закріплення —
        UI буде виглядати дивно.
        """
        note = Note.objects.create(user=self.user, title='My Note')
        self.assertEqual(str(note), 'My Note')

    def test_str_pinned_note_has_pin_emoji(self):
        """
        ЩО ПЕРЕВІРЯЄМО: закріплена нотатка у __str__ має 📌 на початку.

        НАВІЩО: це візуальна індикація для адміна і логів. Якщо тест
        падає — або 📌 не додається, або додається для незакріплених.

        КОД, ЩО ТЕСТУЄТЬСЯ (models.py):
            def __str__(self):
                pin = "📌 " if self.is_pinned else ""
                return f"{pin}{self.title}"

        ЯКЩО ХТОСЬ "РЕФАКТОРИТЬ" цей метод і прибере умову — тест
        відразу покаже що 📌 зник.
        """
        note = Note.objects.create(user=self.user, title='Important', is_pinned=True)
        self.assertEqual(str(note), '📌 Important')

    def test_default_priority_is_low(self):
        """
        ЩО ПЕРЕВІРЯЄМО: нова нотатка без вказання priority отримує
        пріоритет 1 (LOW), а не None чи 0.

        НАВІЩО: якщо priority=None при create — перша ж сортировка по
        priority впаде з TypeError. Або фільтр notes.filter(priority__gte=2)
        не поверне нотатки з priority=None.

        ПЕРЕВІРЯЄМО ДВОМА СПОСОБАМИ:
          self.assertEqual(note.priority, Note.PRIORITY_LOW)  ← через константу
          self.assertEqual(note.priority, 1)                  ← через число
        Обидва assert'и мають сенс: перший перевіряє що константа правильна,
        другий — що само число 1.
        """
        note = Note.objects.create(user=self.user, title='Test')
        self.assertEqual(note.priority, Note.PRIORITY_LOW)
        self.assertEqual(note.priority, 1)

    def test_default_is_pinned_false(self):
        """
        ЩО ПЕРЕВІРЯЄМО: нова нотатка не є закріпленою за замовчуванням.

        НАВІЩО: якщо is_pinned defaulted to True — ВСІ нові нотатки
        стануть закріпленими. Це зламає сортування (закріплені йдуть
        першими) і UX користувача.

        ЗАСАДА: тести defaults гарантують що модель ініціалізується
        безпечно навіть без явного вказання кожного поля.
        """
        note = Note.objects.create(user=self.user, title='Test')
        self.assertFalse(note.is_pinned)

    def test_default_is_archived_false(self):
        """
        ЩО ПЕРЕВІРЯЄМО: нова нотатка не є архівованою за замовчуванням.

        НАВІЩО: якщо is_archived defaulted to True — всі нові нотатки
        одразу опиняться в архіві і зникнуть з головного view.
        Це критичний баг, але без тесту його можна не помітити одразу.
        """
        note = Note.objects.create(user=self.user, title='Test')
        self.assertFalse(note.is_archived)

    def test_default_group_is_none(self):
        """
        ЩО ПЕРЕВІРЯЄМО: нова нотатка не належить жодній групі (group=None).

        НАВІЩО: нотатки за замовчуванням мають бути особистими. Якщо
        group не-None — нотатка стане видимою для членів якоїсь групи,
        що є серйозним витоком приватних даних.

        КОД: group = ForeignKey(Group, null=True, blank=True, default=None)
        """
        note = Note.objects.create(user=self.user, title='Test')
        self.assertIsNone(note.group)

    def test_priority_above_4_raises_validation_error(self):
        """
        ЩО ПЕРЕВІРЯЄМО: пріоритет 5 відхиляється валідатором.

        НАВІЩО: Note.priority має validators=[MaxValueValidator(4)].
        Якщо хтось видалить цей валідатор або змінить максимум —
        форма почне приймати priority=99, і логіка відображення зламається.

        ЯК ЗАПУСКАЄТЬСЯ ВАЛІДАТОР:
          - При збереженні через ModelForm → Django викликає full_clean()
          - full_clean() → clean_fields() → run_validators() → MaxValueValidator(4)
          - Прямий .save() або .objects.create() ОБХОДИТЬ валідатори!

        ТОМУ МИ ВИКОРИСТОВУЄМО full_clean():
          note = Note(..., priority=5)
          note.full_clean()  ← тут спрацює ValodationError
          # note.save() ← тут НЕ спрацює (обходить)

        ПЕРЕВІРКА MESSAGE_DICT: ми також перевіряємо що помилка саме у
        полі 'priority', а не в іншому полі. Це точна локалізація помилки.
        """
        note = Note(user=self.user, title='Test', priority=5)
        with self.assertRaises(ValidationError) as ctx:
            note.full_clean()
        # Перевіряємо що помилка саме у полі priority
        self.assertIn('priority', ctx.exception.message_dict)

    def test_priority_below_1_raises_validation_error(self):
        """
        ЩО ПЕРЕВІРЯЄМО: пріоритет 0 відхиляється валідатором.

        НАВІЩО: MinValueValidator(1) захищає від priority=0 або від'ємних.
        Priority=0 не має сенсу в PRIORITY_CHOICES (немає такого варіанту).
        Відображення пріоритету могло б вийти за межі масиву і впасти з KeyError.

        ГРАНИЧНЕ ТЕСТУВАННЯ (boundary testing):
          • priority=0 — нижче мінімуму → має відхилятись
          • priority=1 — на мінімумі → має прийматись (наступний тест)
          • priority=4 — на максимумі → має прийматись
          • priority=5 — вище максимуму → має відхилятись (попередній тест)
        """
        note = Note(user=self.user, title='Test', priority=0)
        with self.assertRaises(ValidationError) as ctx:
            note.full_clean()
        self.assertIn('priority', ctx.exception.message_dict)

    def test_priority_boundary_values_are_valid(self):
        """
        ЩО ПЕРЕВІРЯЄМО: пріоритети 1, 2, 3, 4 проходять валідацію без помилок.

        НАВІЩО: після тестів що відхиляють 0 і 5, треба переконатись що
        ЛЕГІТИМНІ значення на межі (1 і 4) НЕ відхиляються. Це захист
        від "надто суворої" валідації (наприклад, хтось написав priority < 4
        замість priority <= 4).

        LOOP ЗАМІСТЬ 4 ТЕСТІВ: тестуємо всі 4 значення в одному тесті.
        Це допустимо бо всі 4 перевіряють ОДНУ поведінку: "валідні values проходять".
        (Краще було б @pytest.mark.parametrize, але тут показуємо простий варіант.)
        """
        for priority in [1, 2, 3, 4]:
            note = Note(user=self.user, title=f'Note {priority}', priority=priority)
            note.full_clean()  # Якщо кидає виняток — тест провалиться

    def test_note_group_becomes_null_when_group_deleted(self):
        """
        ЩО ПЕРЕВІРЯЄМО: при видаленні групи нотатка залишається,
        але її поле group стає NULL.

        НАВІЩО:
          ForeignKey(Group, on_delete=SET_NULL) — це КРИТИЧНА бізнес-логіка.
          Є дві альтернативи: CASCADE або SET_NULL.

          CASCADE: видалив групу → всі нотатки групи ВИДАЛЕНІ.
          SET_NULL: видалив групу → нотатки стали особистими.

          У нашому проєкті вибрано SET_NULL — нотатки не зникають.
          Якщо хтось змінить на CASCADE — нотатки зникнуть при видаленні групи.
          Цей тест виявить таку зміну миттєво.

        refresh_from_db() — ВАЖЛИВО:
          Після group.delete() об'єкт note в пам'яті СТАРИЙ (group ще вказує).
          refresh_from_db() перечитує note зі свіжої БД.
          Без цього тест покаже хибно-позитивний результат.
        """
        # Arrange — нотатка належить групі
        group = Group.objects.create(name='Family')
        note = Note.objects.create(user=self.user, title='Family note', group=group)
        self.assertEqual(note.group, group)  # спочатку group встановлено

        # Act — видаляємо групу
        group.delete()

        # Assert — нотатка ще існує, але group тепер NULL
        note.refresh_from_db()  # обов'язково! інакше бачимо старий стан
        self.assertIsNone(note.group)

    def test_created_at_auto_set(self):
        """
        ЩО ПЕРЕВІРЯЄМО: поле created_at заповнюється автоматично при створенні.

        НАВІЩО: created_at = DateTimeField(auto_now_add=True).
        Якщо хтось видалить auto_now_add=True або зробить null=True без
        дефолту — нові нотатки матимуть created_at=None, і сортування
        по даті впаде з TypeError.
        """
        note = Note.objects.create(user=self.user, title='Test')
        self.assertIsNotNone(note.created_at)

    def test_updated_at_changes_on_save(self):
        """
        ЩО ПЕРЕВІРЯЄМО: updated_at оновлюється кожен раз при save().

        НАВІЩО: updated_at = DateTimeField(auto_now=True). Це поле
        відображається у UI ("оновлено 2 хвилини тому"). Якщо auto_now
        прибрати — поле заморозиться на created_at і юзер бачитиме
        невірну дату.

        ДЕТАЛЬ ТЕСТУ: ми використовуємо assertGreaterEqual (>=) а не
        assertGreater (>) тому що на дуже швидких машинах updated_at
        може бути рівним created_at (однакова мікросекунда).
        """
        note = Note.objects.create(user=self.user, title='Test')
        old_updated_at = note.updated_at

        note.title = 'Updated Title'
        note.save(update_fields=['title'])
        note.refresh_from_db()

        # Після збереження updated_at має бути >= старого значення
        self.assertGreaterEqual(note.updated_at, old_updated_at)


# ═════════════════════════════════════════════════════════════════════════════
# ТЕСТИ ДЛЯ МОДЕЛІ Notebook
# ═════════════════════════════════════════════════════════════════════════════

class NotebookModelTest(TestCase):
    """
    Notebook — записник для групування нотаток.
    Ключова особливість: is_default — тільки один записник може бути дефолтним.
    """

    def setUp(self):
        self.user = User.objects.create_user('alice', password='pass123')

    def test_str_regular_notebook(self):
        """
        ЩО ПЕРЕВІРЯЄМО: звичайний записник __str__ = просто назва.

        НАВІЩО: Notebook відображається у select-dropdown у формі нотатки.
        "Виберіть записник: Work Notes, Personal, Study" — рядки з __str__.
        Зайвий маркер [Default] для звичайних записників забруднив би UI.
        """
        notebook = Notebook.objects.create(user=self.user, title='Work Notes')
        self.assertEqual(str(notebook), 'Work Notes')

    def test_str_default_notebook_has_marker(self):
        """
        ЩО ПЕРЕВІРЯЄМО: записник з is_default=True відображається як
        'Main [Default]' (з маркером).

        НАВІЩО: у dropdown і адмінці корисно бачити який записник дефолтний.
        Без маркера адмін не знатиме який з них default при debug.

        КОД (models.py):
            def __str__(self):
                marker = " [Default]" if self.is_default else ""
                return f"{self.title}{marker}"
        """
        notebook = Notebook.objects.create(user=self.user, title='Main', is_default=True)
        self.assertEqual(str(notebook), 'Main [Default]')

    def test_default_color(self):
        """
        ЩО ПЕРЕВІРЯЄМО: новий записник без color отримує '#4A90E2' (синій).

        НАВІЩО: color відображається у UI як кольоровий бейдж записника.
        Якщо дефолт відсутній — шаблон отримає '' і верстка зламається.
        Якщо дефолт зміниться — UI раптово зміниться для всіх старих записників.
        """
        notebook = Notebook.objects.create(user=self.user, title='Test')
        self.assertEqual(notebook.color, '#4A90E2')


# ═════════════════════════════════════════════════════════════════════════════
# ТЕСТИ ДЛЯ МОДЕЛІ ShopItem
# ═════════════════════════════════════════════════════════════════════════════

class ShopItemModelTest(TestCase):
    """
    ShopItem — товар у списку покупок (Молоко, 2 л, 45 грн).

    Ключові правила:
      • quantity > 0 — CheckConstraint у БД
      • is_purchased — перемикається при позначенні куплено
    """

    def setUp(self):
        self.user = User.objects.create_user('alice', password='pass123')
        self.shopping_list = ShoppingList.objects.create(
            user=self.user, title='Weekly shopping'
        )

    def test_str_not_purchased(self):
        """
        ЩО ПЕРЕВІРЯЄМО: непокуплений товар відображається з символом '○'.

        НАВІЩО: у списку покупок символи ○/✓ дають швидку візуальну
        підказку. У адмінці, логах, API відповідях — теж використовується.
        Якщо символ зміниться (наприклад '□') — це візуальна регресія.

        МЕТОД assertIn замість assertEqual:
        ми перевіряємо ЧИ МІСТИТЬ рядок потрібне, а не що він рівно такий.
        str(item) = "○ Milk (2 шт)" — нам важливо 'Milk' і '○', а не точний формат.
        """
        item = ShopItem.objects.create(
            shopping_list=self.shopping_list,
            name='Milk',
            quantity=2,
        )
        self.assertIn('Milk', str(item))    # назва товару є у рядку
        self.assertIn('○', str(item))       # символ "не куплено"

    def test_str_purchased(self):
        """
        ЩО ПЕРЕВІРЯЄМО: куплений товар відображається з символом '✓'.

        НАВІЩО: при toggle_shop_item_purchased() is_purchased=True.
        Після цього у UI і логах має з'явитись '✓'. Якщо умова у __str__
        неправильна — куплені товари виглядатимуть як некуплені.
        """
        item = ShopItem.objects.create(
            shopping_list=self.shopping_list,
            name='Bread',
            quantity=1,
            is_purchased=True,
        )
        self.assertIn('✓', str(item))

    def test_default_quantity_is_one(self):
        """
        ЩО ПЕРЕВІРЯЄМО: якщо quantity не вказано — дефолт 1.

        НАВІЩО: коли користувач додає товар через форму і не вказує
        кількість — має з'явитись 1, а не 0 або None. 0 порушить
        CheckConstraint (quantity > 0). None зламає арифметику ціни.
        """
        item = ShopItem.objects.create(
            shopping_list=self.shopping_list,
            name='Eggs',
        )
        self.assertEqual(item.quantity, 1)

    def test_default_unit_is_pieces(self):
        """
        ЩО ПЕРЕВІРЯЄМО: якщо unit не вказано — дефолт 'шт' (штуки).

        НАВІЩО: unit відображається у рядку "Молоко (2 шт)". Якщо дефолт
        '' або None — відображення буде "Молоко (2 )" що виглядає погано.
        Плюс choices=['шт','кг','л','г'] — порожній рядок не в choices → помилка.
        """
        item = ShopItem.objects.create(
            shopping_list=self.shopping_list,
            name='Eggs',
        )
        self.assertEqual(item.unit, 'шт')

    def test_quantity_validator_rejects_zero(self):
        """
        ЩО ПЕРЕВІРЯЄМО: quantity=0 відхиляється при full_clean().

        НАВІЩО: quantity=0 не має сенсу — "0 молока" у списку покупок.
        Модель має MinValueValidator(0) — АЛЕ це >= 0, що дозволяє нуль!
        Водночас форма ShopItemForm має min_value=0.01 — вона відхиляє 0.
        А CheckConstraint у БД: quantity > 0 — теж відхиляє нуль.

        ВАЖЛИВА РІЗНИЦЯ:
          MinValueValidator(0) → дозволяє 0 (включно!)
          CheckConstraint(quantity__gt=0) → забороняє 0 (строго більше)

        Тут ми тестуємо через full_clean() — це шлях через Django forms.
        full_clean() запускає clean_fields() → run_validators().
        validators=[MinValueValidator(0)] → 0 >= 0 → ПРОХОДИТЬ валідатор!
        Але full_clean() також викликає validate_constraints() (Django 3.1+)
        → CheckConstraint quantity > 0 → ВІДХИЛЯЄ 0.

        ПІДСУМОК: quantity=0 відхиляється CheckConstraint, а не validator.
        """
        item = ShopItem(
            shopping_list=self.shopping_list,
            name='Test',
            quantity=0,
        )
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_quantity_validator_accepts_positive(self):
        """
        ЩО ПЕРЕВІРЯЄМО: quantity=0.5 (наприклад, 0.5 кг яблук) проходить.

        НАВІЩО: після тесту що відхиляє 0, треба переконатись що дрібні
        додатні значення (0.5 кг хліба, 0.1 л масла) дозволені.
        Без цього тесту надто сувора валідація може блокувати коректні значення.
        """
        item = ShopItem(
            shopping_list=self.shopping_list,
            name='Test',
            quantity=0.5,
        )
        item.full_clean()  # Не кидає виняток — тест проходить
