# CrispyNotes — Django Тестування від A до Z

> Цей туторіал проводить тебе через **повний стек тестування Django-застосунку**:
> unit тести → сервіси → форми → integration (views) → E2E (Selenium).
>
> Проєкт — **той самий CrispyNotes** з попередніх уроків (crispy forms + auth + групи).
> У цьому уроці ми пишемо тести для вже готового застосунку.
> Ти побачиш як кожен рівень тестів захищає різний шар системи.
>
> **Результат:** 129 тестів — 123 pass + 6 Selenium

---

## Зміст

**Теорія** _(читати перед кодом)_
- [01 · НАВІЩО ТЕСТИ — сигналізація замість ручної перевірки](#01--навіщо-тести)
- [02 · ПІРАМІДА — unit vs integration vs E2E](#02--піраміда-тестування)
- [03 · DJANGO TESTCASE — як це працює під капотом](#03--django-testcase)
- [04 · ТЕСТОВА БД — ізоляція і rollback](#04--тестова-бд)
- [05 · AAA ПАТТЕРН — структура кожного тесту](#05--aaa-паттерн)
- [06 · ЧИТАННЯ ВИВОДУ — PASSED / FAILED / ERROR](#06--читання-виводу)

**Що ми тестуємо і навіщо**
- [07 · МОДЕЛІ — constraints, defaults, SET_NULL](#07--тестування-моделей)
- [08 · СЕРВІСИ — бізнес-логіка і security](#08--тестування-сервісів)
- [09 · ФОРМИ — валідація і queryset filtering](#09--тестування-форм)
- [10 · DJANGO TEST CLIENT — integration тести](#10--django-test-client)
- [11 · SELENIUM — тести через браузер](#11--selenium)

**Покрокова реалізація**
1. [Крок 0 — Запуск проєкту](#крок-0--запуск)
2. [Крок 1 — Структура tests/ пакету](#крок-1--структура-tests)
3. [Крок 2 — test_models.py](#крок-2--test_modelspy)
4. [Крок 3 — test_services.py](#крок-3--test_servicespy)
5. [Крок 4 — test_forms.py](#крок-4--test_formspy)
6. [Крок 5 — test_views.py](#крок-5--test_viewspy)
7. [Крок 6 — test_selenium.py](#крок-6--test_seleniumpy)
8. [Крок 7 — Запуск і розуміння результатів](#крок-7--запуск)
9. [Крок 8 — GitHub Actions CI](#крок-8--github-actions-ci)
10. [Структура файлів](#структура-файлів)

---

## 01 · НАВІЩО ТЕСТИ

> **Головне питання:** Як дізнатись що після змін нічого не зламалось?
>
> Відповідь без тестів: запустити вручну, клацати по сайту, сподіватись.
> Відповідь з тестами: запустити одну команду і побачити все за 30 секунд.

### Аналогія — пожежна сигналізація

Будинок без сигналізації: виявляєш пожежу коли вже горить.
Будинок з сигналізацією: дізнаєшся про іскру ДО того як все охопить вогнем.

**Тести = сигналізація вашого коду.** Вони перевіряють "чи все ще правильно" при кожній зміні.

```
БЕЗ ТЕСТІВ                              З ТЕСТАМИ
──────────────────────────────────────  ──────────────────────────────────────
Пишеш новий фічер                       Пишеш новий фічер
Вручну клацаєш 10+ сторінок             Запускаєш: manage.py test
"Виглядає ок"                           FAIL: test_note_visible_only_to_owner
git push → деплой                       Бачиш ТОЧНО що зламалось
Через тиждень: "Баг у продакшені!"      Виправляєш ДО деплою
Стаєш детективом — шукаєш причину      git push → деплой → все зелено
```

### Реальний сценарій: ти міняєш `selectors.py`

```python
# СТАРА версія (правильна):
def get_user_notes(user, *, archived=False):
    user_groups = user.groups.all()
    return Note.objects.filter(
        Q(user=user) | Q(group__in=user_groups),   # ← власні + групові
        is_archived=archived,
    )

# НОВА версія після "рефакторингу" (помилка!):
def get_user_notes(user, *, archived=False):
    return Note.objects.filter(
        user=user,    # ← забули Q-filter для груп!
        is_archived=archived,
    )
```

**Без тестів:** Всі групові нотатки зникають для всіх юзерів.
Виявляють клієнти через тиждень після деплою в production.

**З тестами:** `test_selectors.py` одразу:
```
FAIL: test_group_notes_visible_to_members
AssertionError: <Note: Team meeting> not found in queryset for bob
```
Виправляєш за 2 хвилини до коміту.

### Що ще дають тести

| Перевага | Пояснення |
|----------|-----------|
| **Документація** | `test_create_notebook_default_unsets_previous_default` пояснює інваріант краще за коментар |
| **Рефакторинг без страху** | Змінив реалізацію → тести підтверджують що поведінка та сама |
| **Виявлення edge cases** | При написанні тесту думаєш: "а що якщо None? а якщо порожньо?" |
| **Захист від регресій** | Баг виправлений + тест написаний = баг ніколи не повернеться |
| **Security перевірка** | `test_notebook_queryset_excludes_other_user_notebooks` — IDOR неможливий |

---

## 02 · ПІРАМІДА ТЕСТУВАННЯ

> **Не всі тести однакові.** Різні рівні мають різну вартість і швидкість.

```
              ╱╲
             ╱E2E╲          Selenium, Playwright
            ╱──────╲        Реальний браузер, повний сценарій
           ╱ Integr. ╲      Повільно (секунди/тест), крихко
          ╱────────────╲    Django Test Client: запити → БД → відповідь
         ╱     Unit      ╲  Середньо (100мс/тест)
        ╱──────────────────╲ pytest/TestCase: функція → результат
       ╱────────────────────╲ Швидко (1-10мс/тест), надійно

      70% Unit | 20% Integration | 10% E2E
```

### Що тестуємо на кожному рівні

**Unit тести** (цей урок):
```python
# Тестуємо функцію ізольовано від HTTP
def test_create_notebook_default_unsets_previous_default(self):
    old = services.create_notebook(user=alice, title='Old', is_default=True)
    new = services.create_notebook(user=alice, title='New', is_default=True)
    old.refresh_from_db()
    self.assertFalse(old.is_default)  # 1 is_default на юзера — інваріант
```

**Integration тести** (наступний рівень):
```python
# Тестуємо через HTTP — view + БД + відповідь
def test_note_list_shows_only_user_notes(self):
    self.client.login(username='alice', password='pass')
    response = self.client.get('/notes/')
    self.assertEqual(response.status_code, 200)
    self.assertNotContains(response, "Bob's Secret Note")
```

**E2E тести** (Selenium):
```python
# Тестуємо через реальний браузер — кліки, форми, навігація
def test_user_can_create_and_share_note(self):
    self.browser.get('/accounts/login/')
    self.browser.find_element(By.NAME, 'username').send_keys('alice')
    # ...
```

### Де живуть наші тести

| Рівень | Файл | Що тестує | Кількість |
|--------|------|-----------|-----------|
| Unit | `tests/test_models.py` | Модель: constraints, __str__, defaults | 23 |
| Unit | `tests/test_services.py` | Бізнес-логіка: create, update, delete, security | 36 |
| Unit | `tests/test_forms.py` | Валідація, нормалізація, queryset filtering | 23 |
| Integration | `tests/test_views.py` | Views через self.client: HTTP коди, ownership, redirects | 41 |
| E2E | `tests/test_selenium.py` | Браузер: форми, навігація, DOM (skip без geckodriver) | 6 |

---

## 03 · DJANGO TESTCASE

> `django.test.TestCase` — це `unittest.TestCase` + магія Django.

### Що відрізняє Django TestCase

```python
import unittest
from django.test import TestCase

# unittest.TestCase — базовий, без БД
class PureUnitTest(unittest.TestCase):
    def test_math(self):
        assert 2 + 2 == 4   # ОК, без БД

# django.test.TestCase — з повним Django стеком
class DjangoTest(TestCase):
    def test_with_db(self):
        user = User.objects.create_user('alice')  # ← потребує тестової БД
        self.assertEqual(user.username, 'alice')
```

### Що Django TestCase дає автоматично

```
┌─────────────────────────────────────────────────────────────────┐
│  Перед ВСІМА тестами класу:                                     │
│    → Створює тестову БД в пам'яті                               │
│    → Застосовує всі міграції                                     │
│                                                                 │
│  Перед КОЖНИМ тестом:                                           │
│    → Відкриває транзакцію                                       │
│    → Викликає setUp()                                           │
│                                                                 │
│    ┌─── ТЕСТ ВИКОНУЄТЬСЯ ──────────────────────────────────┐   │
│    │  User.objects.create(...)  ← записи в тестовій БД     │   │
│    │  Note.objects.create(...)  ← ізольовано від реальної  │   │
│    └───────────────────────────────────────────────────────┘   │
│                                                                 │
│  Після КОЖНОГО тесту:                                          │
│    → ROLLBACK транзакції (всі записи зникають!)                │
│    → Викликає tearDown()                                        │
│                                                                 │
│  Після ВСІХ тестів:                                             │
│    → Видаляє тестову БД                                         │
└─────────────────────────────────────────────────────────────────┘
```

### Чому rollback — це добре

```python
class MyTest(TestCase):
    def test_first(self):
        User.objects.create_user('alice')    # ← alice ІСНУЄ
        self.assertEqual(User.objects.count(), 1)
        # Після тесту → ROLLBACK → alice зникла

    def test_second(self):
        # alice НЕ існує — кожен тест починає з чистого стану
        self.assertEqual(User.objects.count(), 0)  # ← 0, не 1!
```

**Без rollback** тести б впливали один на одного:
- тест 1 створює alice → тест 2 бачить alice → результати непередбачувані
- Порядок виконання тестів впливав би на результат

**З rollback** кожен тест ізольований → результат не залежить від порядку.

### setUp — підготовка перед кожним тестом

```python
class NoteServiceTest(TestCase):

    def setUp(self):
        """Виконується ПЕРЕД кожним тестом. БД чиста."""
        self.alice = User.objects.create_user('alice', password='pass123')
        self.bob   = User.objects.create_user('bob',   password='pass123')
        # Ці юзери будуть у кожному тесті цього класу
        # Після кожного тесту → ROLLBACK → вони зникають → наступний setUp створить знову

    def test_something(self):
        # self.alice і self.bob вже існують тут
        note = services.create_note(user=self.alice, title='Test')
        ...
```

---

## 04 · ТЕСТОВА БД

> **Найважливіше правило:** Тести ніколи не торкаються твоєї робочої БД.

### Як Django створює тестову БД

```bash
$ python manage.py test hello_app.tests

Creating test database for alias 'default' ...
#  ↑ Django створює test_<db_name> або in-memory (SQLite)
#    Вся дані там — не в твоєму db.sqlite3!

Found 82 test(s).
...

Destroying test database for alias 'default' ...
#  ↑ Тестова БД видаляється після завершення
```

### Три ізоляції одночасно

```
1. ІЗОЛЯЦІЯ ВІД РЕАЛЬНОЇ БД:
   db.sqlite3 (твоя робоча) ≠ тестова БД (окрема, тимчасова)
   Тести не можуть зламати твої реальні дані.

2. ІЗОЛЯЦІЯ МІЖ ТЕСТАМИ:
   Кожен тест — своя транзакція → rollback.
   Тест A не бачить даних Тесту B.

3. ІЗОЛЯЦІЯ ВІД ЗОВНІШНІХ СИСТЕМ:
   Email: EMAIL_BACKEND = console (не надсилається реально)
   Файли: не змінюються в production
   API: треба mock (unittest.mock.patch)
```

---

## 05 · AAA ПАТТЕРН

> Кожен тест має три чіткі частини. Це стандарт у всіх мовах.

```python
def test_create_note_assigns_tags(self):

    # ── ARRANGE: підготовка стану ─────────────────────────────────────────
    # Що потрібно для тесту? Створюємо мінімально необхідний стан.
    tag1 = Tag.objects.create(user=self.alice, name='work')
    tag2 = Tag.objects.create(user=self.alice, name='python')

    # ── ACT: виконуємо те, що тестуємо ───────────────────────────────────
    # Один виклик — одна дія. Що саме тестуємо? Тільки це.
    note = services.create_note(
        user=self.alice, title='Tagged', tag_ids=[tag1.id, tag2.id]
    )

    # ── ASSERT: перевіряємо результат ────────────────────────────────────
    # Що має бути правдою після Act? Перевіряємо конкретно.
    note_tags = list(note.tags.all())
    self.assertIn(tag1, note_tags)
    self.assertIn(tag2, note_tags)
```

### Правила гарного тесту

| Правило | Пояснення |
|---------|-----------|
| **Один тест — одна поведінка** | `test_create_note_sets_user` ≠ `test_create_note_saves_to_db` |
| **Назва = специфікація** | `test_add_user_to_group_duplicate_returns_false` — назва пояснює все |
| **Незалежність** | Тест не залежить від порядку і від інших тестів |
| **Швидкість** | Unit тест < 50мс. Якщо повільно — перевір чи не робиш зайвих запитів |
| **Детермінованість** | Той самий тест при тих самих умовах = той самий результат |

---

## 06 · ЧИТАННЯ ВИВОДУ

> Розуміти що показує pytest / manage.py test — ключова навичка.

### Успішний запуск

```bash
$ python manage.py test hello_app.tests -v 2

Creating test database for alias 'default' ...
Found 82 test(s).

test_str_returns_hash_name (hello_app.tests.test_models.TagModelTest) ... ok
test_unique_together_same_user_same_name_raises (...) ... ok
test_create_note_assigns_tags (...) ... ok
...

----------------------------------------------------------------------
Ran 82 tests in 76.8s

OK   ← ВСЕ ЗЕЛЕНО! Можна робити git push.
```

### Провалений тест

```bash
$ python manage.py test hello_app.tests

FAIL: test_create_notebook_default_unsets_previous_default
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tests/test_services.py", line 179, in test_create_notebook_...
    self.assertFalse(old_default.is_default)
AssertionError: True is not false

----------------------------------------------------------------------
Ran 82 tests in 77.1s

FAILED (failures=1)
```

**Як читати провалений тест:**

```
FAIL: test_create_notebook_default_unsets_previous_default
 ↑ Назва тесту → одразу зрозуміло ЩО зламалось

File "tests/test_services.py", line 179
 ↑ Де саме у файлі

self.assertFalse(old_default.is_default)
AssertionError: True is not false
 ↑ Очікували False, отримали True
   → Старий default НЕ скинувся
   → Баг у services.create_notebook()
```

### Типи результатів

| Символ | Означає | Причина |
|--------|---------|---------|
| `.` | PASSED | Тест пройшов |
| `F` | FAILED | `assert` не спрацював — неправильний результат |
| `E` | ERROR | Виняток в тесті (не AssertionError) — наприклад, AttributeError |
| `s` | SKIPPED | `@unittest.skip` — тест пропущений навмисно |
| `x` | XFAIL | Очікуваний провал (`@unittest.expectedFailure`) |

### Рівні verbosity (-v 0/1/2)

```bash
# -v 0: тільки підсумок
python manage.py test hello_app.tests
# OK або FAILED (failures=3)

# -v 1 (default): крапки прогресу
python manage.py test hello_app.tests -v 1
# ...............F........ (82 тести)

# -v 2: кожен тест окремо
python manage.py test hello_app.tests -v 2
# test_str_returns_hash_name ... ok
# test_unique_together... ... ok
```

### Зупинитись на першому провалі

```bash
python manage.py test hello_app.tests --failfast
# Зупиняється одразу при першому FAIL
# Корисно при великій кількості помилок
```

---

## 07 · ТЕСТУВАННЯ МОДЕЛЕЙ

> **Питання:** Чому тестувати моделі? Це ж просто поля і зв'язки.

**Відповідь:** Модель містить бізнес-правила. Якщо їх порушити — додаток поводиться неправильно мовчки.

### Що живе в моделі (і що можна зламати)

```
Note модель
  ├── priority: validators=[MinValueValidator(1), MaxValueValidator(4)]
  │     Якщо хтось видалить validators → форма прийме priority=99
  │     → Відображення пріоритету зламається (KeyError в PRIORITY_CHOICES)
  │
  ├── group: ForeignKey(Group, on_delete=SET_NULL)
  │     Якщо змінити на CASCADE → видалення групи видалить всі нотатки!
  │     → Юзери втратять дані
  │
  ├── is_pinned: BooleanField(default=False)
  │     Якщо default стане True → всі нові нотатки стануть закріпленими
  │     → Сортування зламається
  │
  └── __str__: pin + title
        Якщо зміниться формат → Django Admin і логи показують неправильно
```

### Структура test_models.py

```python
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from hello_app.models import Note, Notebook, ShopItem, ShoppingList, Tag


class TagModelTest(TestCase):
    def setUp(self):
        self.user  = User.objects.create_user('alice', password='pass123')
        self.user2 = User.objects.create_user('bob',   password='pass123')

    # 1. __str__ method
    def test_str_returns_hash_name(self):
        tag = Tag.objects.create(user=self.user, name='python')
        self.assertEqual(str(tag), '#python')

    # 2. unique_together constraint
    def test_unique_together_same_user_same_name_raises(self):
        Tag.objects.create(user=self.user, name='work')
        with self.assertRaises(IntegrityError):
            Tag.objects.create(user=self.user, name='work')  # ← дублікат → помилка

    # 3. Різні юзери — ізоляція
    def test_unique_together_different_users_same_name_ok(self):
        Tag.objects.create(user=self.user,  name='work')  # Alice's 'work'
        Tag.objects.create(user=self.user2, name='work')  # Bob's 'work' — OK
        self.assertEqual(Tag.objects.count(), 2)
```

### Як тестувати validators через full_clean()

```python
# ВАЖЛИВО: validators не запускаються при .save() або .objects.create()!
# Вони запускаються тільки через full_clean() або ModelForm.

# НЕПРАВИЛЬНО (validators не перевіряться):
note = Note.objects.create(user=user, title='Test', priority=5)
# ← Django просто збереже priority=5! (validators проігноровані)
# ← CheckConstraint у БД може спрацювати, але не validators

# ПРАВИЛЬНО — через full_clean():
note = Note(user=user, title='Test', priority=5)  # ← НЕ зберігаємо одразу
note.full_clean()   # ← тут запускаються validators → ValidationError

# У тесті:
def test_priority_above_4_raises_validation_error(self):
    note = Note(user=self.user, title='Test', priority=5)
    with self.assertRaises(ValidationError) as ctx:
        note.full_clean()
    self.assertIn('priority', ctx.exception.message_dict)
    #              ↑ перевіряємо що помилка саме у полі priority
```

### Тест SET_NULL — захист від CASCADE

```python
def test_note_group_becomes_null_when_group_deleted(self):
    """
    Перевіряємо що Note.group = ForeignKey(Group, on_delete=SET_NULL)
    працює правильно: видалення групи → нотатка стає особистою.

    Якщо хтось змінить на CASCADE → цей тест ПРОВАЛИТЬСЯ і покаже:
    DoesNotExist: Note matching query does not exist.
    → ми дізнаємось ДО деплою що зміна зломала дані юзерів.
    """
    group = Group.objects.create(name='Family')
    note  = Note.objects.create(user=self.user, title='Family note', group=group)

    group.delete()               # видаляємо групу

    note.refresh_from_db()       # ← ОБОВ'ЯЗКОВО! читаємо свіжий стан з БД
    self.assertIsNone(note.group)# нотатка збереглась, group = NULL
```

> **Чому `refresh_from_db()`?** Після `group.delete()` об'єкт `note` у пам'яті
> ще зберігає стару reference. `refresh_from_db()` перечитує з БД.

---

## 08 · ТЕСТУВАННЯ СЕРВІСІВ

> **Сервіси — найкращий шар для unit тестів.** Без HTTP, без шаблонів, тільки логіка.

### Чому сервіси легко тестувати

```
VIEWS (HTTP layer):
  Приймає request → парсить форму → викликає сервіс → рендерить шаблон
  Залежить від: HTTP, сесії, форми, шаблони
  Важко тестувати ізольовано

SERVICES (business logic):
  create_note(user=alice, title='Test', tag_ids=[1,2])
  Приймає Python об'єкти → повертає результат → зберігає в БД
  Залежностей немає! Тестуємо прямо:
    result = services.create_note(user=alice, title='Test')
    self.assertEqual(result.title, 'Test')
```

### Два типи перевірки в сервісних тестах

```python
# ТИП 1: перевірка ПОВЕРНУТОГО ОБ'ЄКТА
def test_create_note_returns_note_object(self):
    note = services.create_note(user=self.alice, title='Test')
    self.assertIsInstance(note, Note)   # ← перевіряємо що повернулось

# ТИП 2: перевірка СТАНУ БД (persistence test)
def test_create_note_saves_to_database(self):
    services.create_note(user=self.alice, title='Test')
    self.assertEqual(Note.objects.count(), 1)   # ← перевіряємо що збереглось

# НАВІЩО ОБИДВА?
# create_note() міг повернути об'єкт але не зберегти (.save() забули)
# Або зберегти але повернути None
# Обидва тести разом покривають обидва сценарії
```

### Тест security: Mass Assignment через tag_ids

```python
def test_create_note_ignores_other_users_tags(self):
    """
    Атака: зловмисник надсилає POST з tag_id що belongs to Bob.
    POST /notes/new/ → tag_ids=[bob_secret_tag_id]

    БЕЗ ЗАХИСТУ (вразливо):
        note.tags.set(Tag.objects.filter(id__in=tag_ids))
        → Тег Bob'а прикріплюється до нотатки Alice
        → Alice бачить Bob's secret tag у своїй нотатці

    З ЗАХИСТОМ (наш код):
        note.tags.set(Tag.objects.filter(id__in=tag_ids, user=user))
        → Фільтр по user блокує чужі теги
    """
    bob_tag = Tag.objects.create(user=self.bob, name='bob-secret')

    note = services.create_note(
        user=self.alice, title='Note', tag_ids=[bob_tag.id]
    )

    self.assertEqual(note.tags.count(), 0)   # ← чужий тег не прикріпився
```

### Тест транзакційної логіки

```python
def test_create_notebook_default_unsets_previous_default(self):
    """
    Бізнес-інваріант: у юзера може бути тільки ОДИН default записник.

    Код у services.py:
        with transaction.atomic():
            if is_default:
                Notebook.objects.filter(user=user, is_default=True)
                                .update(is_default=False)   ← СКИДАЄМО старий
            return Notebook.objects.create(..., is_default=is_default)  ← СТВОРЮЄМО новий

    Якщо прибрати рядок з .update() → два записники з is_default=True
    → форма нотатки обирає "перший" → непередбачувана поведінка

    Цей тест виявить це ОДРАЗУ.
    """
    old = services.create_notebook(user=self.alice, title='Old', is_default=True)

    new = services.create_notebook(user=self.alice, title='New', is_default=True)

    old.refresh_from_db()       # ← читаємо свіжий стан старого записника
    self.assertFalse(old.is_default)  # старий скинутий
    self.assertTrue(new.is_default)   # новий встановлений
```

### Тест ізоляції між юзерами

```python
def test_create_notebook_default_only_affects_same_user(self):
    """
    Критичний тест multi-user системи.

    ПОМИЛКОВИЙ КОД (не фільтрує по user):
        Notebook.objects.filter(is_default=True).update(is_default=False)
        ↑ Скидає default У ВСІХ ЮЗЕРІВ! Bob втратить свій default.

    ПРАВИЛЬНИЙ КОД:
        Notebook.objects.filter(user=user, is_default=True).update(...)
        ↑ Скидає тільки для конкретного user. Bob в безпеці.
    """
    bob_default = services.create_notebook(user=self.bob,   title='Bob Default',   is_default=True)
    alice_def   = services.create_notebook(user=self.alice, title='Alice Default',  is_default=True)

    bob_default.refresh_from_db()
    self.assertTrue(bob_default.is_default)  # Bob не зачіпається!
```

### Тест (True/False, повідомлення) патерну

```python
def test_add_user_to_group_duplicate_returns_false(self):
    """
    add_user_to_group() повертає (bool, message).
    При дублікаті → (False, 'bob вже є членом').

    Навіщо перевіряти двічі? Функція може повернути (True, '') але не додати,
    або додати але повернути (False, ''). Перевіряємо обидва аспекти.
    """
    group = services.create_group(name='Team', creator=self.alice)
    services.add_user_to_group(group, username='bob')  # 1й раз — успіх

    success, message = services.add_user_to_group(group, username='bob')  # 2й

    self.assertFalse(success)                    # ← функція повернула False
    self.assertIn('bob', message)                # ← повідомлення містить ім'я
    self.assertEqual(group.user_set.count(), 2)  # ← БД не змінилась (alice + bob, не 3)
```

---

## 09 · ТЕСТУВАННЯ ФОРМ

> **Форма в Django — не просто HTML.** Це валідація, нормалізація і security бар'єр.

### Як тестувати форму без HTTP

```python
# Форму можна тестувати прямо, без client.post():

form = TagForm(data={'name': 'Python', 'color': '#ff0000'})
form.is_valid()              # True або False — перевіряємо
form.cleaned_data['name']   # 'python' — нормалізоване значення
form.errors                  # {'name': ['...']} — помилки по полях
```

### Три категорії тестів форм

**1. Нормалізація (`clean_*` методи)**

```python
def test_clean_name_lowercases(self):
    """
    TagForm.clean_name(): 'Python' → 'python'

    НАВІЩО: без нормалізації юзер може створити:
        'python', 'Python', 'PYTHON' — три різні теги!
    Unique_together вважає їх різними.
    clean_name() нормалізує перед збереженням.
    """
    form = TagForm(data={'name': 'Python', 'color': '#ff0000'})
    self.assertTrue(form.is_valid())
    self.assertEqual(form.cleaned_data['name'], 'python')  # нормалізовано

def test_clean_name_strips_whitespace(self):
    """'  work  ' → 'work' (пробіли по краях прибираються)"""
    form = TagForm(data={'name': '  work  ', 'color': '#ff0000'})
    self.assertTrue(form.is_valid())
    self.assertEqual(form.cleaned_data['name'], 'work')
```

**2. Security — queryset filtering (найважливіше!)**

```python
# Вразливість БЕЗ фільтрації:
#   NoteForm().fields['notebook'].queryset = Notebook.objects.all()
#   Alice бачить у dropdown: "Alice's Notes" і "Bob's Private Notes"!
#   Alice вибирає Bob's Private → нотатка Alice записується до Bob
#   Bob бачить чужі нотатки у своєму записнику → DATA LEAK

# Захист у нашому коді:
#   NoteForm(user=alice).fields['notebook'].queryset = Notebook.objects.filter(user=alice)
#   Alice бачить тільки свої записники → SAFE

def test_notebook_queryset_excludes_other_user_notebooks(self):
    """
    ГОЛОВНИЙ security тест — IDOR через форму неможливий.
    """
    form = NoteForm(user=self.alice)
    queryset = form.fields['notebook'].queryset
    self.assertNotIn(self.bob_notebook, queryset)  # Bob's notebook не видно!
```

**3. Безпечний fallback без user=**

```python
def test_form_without_user_has_empty_querysets(self):
    """
    Якщо форму створити без user= (помилка розробника):
        form = NoteForm(data=request.POST)  ← забули user=request.user

    НЕБЕЗПЕЧНО: queryset = Notebook.objects.all() → всі записники видимі
    БЕЗПЕЧНО (наш код): queryset = Notebook.objects.none() → порожній список

    Краще показати юзеру порожній dropdown ніж злити всі дані.
    """
    form = NoteForm()  # user не переданий
    self.assertFalse(form.fields['notebook'].queryset.exists())
    self.assertFalse(form.fields['tags'].queryset.exists())
```

### Таблиця: що перевіряємо у кожній формі

| Форма | Що тестуємо |
|-------|-------------|
| `TagForm` | `clean_name`: lowercase + strip, порожнє ім'я → помилка |
| `NoteForm` | queryset для notebook/tags/group фільтрується по user |
| `NoteForm` | без user= → порожні queryset (безпечний fallback) |
| `NoteForm` | порожній title → invalid, пріоритет 1-4 → valid, 99 → invalid |
| `GroupCreateForm` | `clean_name`: дублікат → ValidationError, strip whitespace |

---

## 10 · DJANGO TEST CLIENT

> **Питання:** Що integration тест перевіряє, чого unit тест НЕ може?

### Різниця між unit і integration тестом

```python
# UNIT ТЕСТ (test_services.py) — прямий виклик Python, без HTTP:
note = services.create_note(user=alice, title='Test')
self.assertEqual(note.user, alice)
# Перевіряє: бізнес-логіку в ізоляції

# INTEGRATION ТЕСТ (test_views.py) — через HTTP:
self.client.force_login(alice)
response = self.client.get(reverse('hello_app:note_list'))
self.assertEqual(response.status_code, 200)
# Перевіряє: URL routing → @login_required → view → selectors → DB → HTML response
```

### Що integration тест виявляє, чого unit НЕ виявить

| Що перевіряє | Unit (services) | Integration (views) |
|-------------|-----------------|---------------------|
| `@login_required` захищає view | ✗ | ✓ |
| URL routing (`/notes/` → note_list) | ✗ | ✓ |
| redirect після POST (302 → /notes/pk/) | ✗ | ✓ |
| form errors у контексті шаблону | ✗ | ✓ |
| Bob отримує 404 при спробі доступу | ✗ | ✓ |
| HTML сторінки містить назву нотатки | ✗ | ✓ |
| Бізнес-логіка create_note() правильна | ✓ | ✓ |

### Django Test Client — що це

`self.client` — це `django.test.Client`, вбудований HTTP клієнт для тестів.

```python
# Автоматично доступний у кожному TestCase як self.client
from django.test import TestCase

class MyTest(TestCase):
    def test_something(self):
        self.client  # ← готовий до використання
```

Він не відкриває реальний браузер. Він симулює HTTP запит **всередині Django процесу**: мінаючи мережу, але проходячи через весь Django middleware stack.

### force_login vs login

```python
# force_login — швидко, без перевірки пароля
self.client.force_login(self.alice)
# ↑ Використовуй в тестах завжди. Він не перевіряє пароль,
#   не запускає authentication backends — просто встановлює session.

# login — повна auth pipeline
self.client.login(username='alice', password='pass123')
# ↑ Використовуй тільки якщо тестуєш сам процес логіну.
```

### Ключові атрибути response

```python
response = self.client.get(reverse('hello_app:note_list'))

response.status_code      # → 200, 302, 404, 403, 500
response.context          # → контекст шаблону {'notes': queryset, 'form': form}
response.content          # → bytes HTML відповіді
response['Location']      # → URL для редіректу (якщо 302)
response.context['form'].errors  # → {'title': ['This field is required.']}
```

### Assert методи для HTTP тестів

```python
# HTTP статус коди
self.assertEqual(response.status_code, 200)    # OK
self.assertEqual(response.status_code, 302)    # redirect
self.assertEqual(response.status_code, 404)    # not found
self.assertEqual(response.status_code, 403)    # forbidden

# Перевірка redirect
self.assertRedirects(response, reverse('hello_app:note_list'),
                     fetch_redirect_response=False)
# fetch_redirect_response=False — не робимо другий GET запит

# Текст у HTML
self.assertContains(response, 'Alice Note')    # рядок є в HTML
self.assertNotContains(response, 'Bob Secret') # рядка НЕМАЄ в HTML

# Перевірка що URL містить login
self.assertIn('/accounts/login/', response['Location'])

# Form errors
self.assertIn('title', response.context['form'].errors)
```

### Що перевіряє кожна категорія тестів у test_views.py

```
AuthenticationViewTest    ← @login_required на кожному view
NoteListViewTest          ← multi-tenant: alice бачить тільки свої нотатки
NoteDetailViewTest        ← ownership + group-based access
NoteCreateViewTest        ← form valid/invalid, IDOR prevention, note.user = request.user
NoteEditViewTest          ← ownership: чужий → 404; свій → 302
NoteDeleteViewTest        ← ownership + cascade: нотатка видалена з БД
NotebookViewTest          ← ownership: get_object_or_404(user=request.user)
GroupViewTest             ← membership check: чужий → 404, non-member delete → 403
TodoListSharingViewTest   ← share/unshare workflow через HTTP
```

---

## 11 · SELENIUM

> **Selenium** — це Python код, який керує реальним браузером (Firefox / Chrome).

### Різниця між Django Test Client і Selenium

```
Django Test Client:
  Python → Django middleware → view → response
  Мінаємо мережу і браузер.
  Не бачимо JavaScript, CSS, DOM рендеринг.

Selenium:
  Python → geckodriver → Firefox → реальний HTTP → Django server
  Повний стек: браузер відкривається, сторінка завантажується, JS виконується.
  Бачимо все що бачить юзер.
```

### StaticLiveServerTestCase — реальний сервер

```python
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

class MySeleniumTest(StaticLiveServerTestCase):
    def test_something(self):
        self.live_server_url  # → 'http://127.0.0.1:PORT' (random port)
        self.driver.get(f'{self.live_server_url}/notes/')
```

`StaticLiveServerTestCase` запускає реальний Django HTTP сервер на тимчасовому порту. Selenium підключається до нього як справжній браузер.

### Session Cookie Trick — логін без форми

```python
def _login_via_cookie(self):
    """Логін без заповнення login форми в браузері."""
    # 1. Test Client встановлює session
    self.client.force_login(self.user)
    session_cookie = self.client.cookies['sessionid']

    # 2. Відкрити будь-яку сторінку (browser потребує активного домену)
    self.driver.get(f'{self.live_server_url}/')

    # 3. Скопіювати session cookie до Selenium
    self.driver.add_cookie({
        'name': 'sessionid', 'value': session_cookie.value, 'path': '/'
    })
    # Тепер driver авторизований!
```

**Навіщо:** login форма може мати CSRF, JS валідацію, рекапчу. Все це ламає E2E тести. Session cookie trick надійніший і швидший.

### Headless режим

```python
from selenium.webdriver.firefox.options import Options

options = Options()
options.add_argument('--headless')  # без GUI вікна
driver = webdriver.Firefox(options=options)
```

**headless** = браузер запускається без графічного інтерфейсу. Потрібно для:
- CI/CD серверів (GitHub Actions, Jenkins, Docker) — там немає дисплею
- Швидкість — не треба рендерити піксели на екран

### @unittest.skipUnless — graceful skip

```python
try:
    from selenium import webdriver
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

@unittest.skipUnless(SELENIUM_AVAILABLE, "selenium not installed")
class MySeleniumTest(StaticLiveServerTestCase):
    ...
```

Якщо `selenium` не встановлений → тести позначаються як `s` (skipped), **не падають**.

```
Ran 129 tests in 90.2s
OK (skipped=6)
```

Це важливо: `manage.py test` повинен завжди повертати OK, навіть без geckodriver.

### Чому Selenium тестів мало

```
Unit test: 0.01s  ×  100 = 1 секунда
Selenium:  10s    ×  100 = 16 хвилин

+ Selenium крихкий: зміна CSS класу ламає тест навіть якщо логіка правильна
+ Потрібен geckodriver, специфічна версія браузера
+ Нестабільний в CI без implicitly_wait

Правило: E2E тести тільки для КРИТИЧНИХ user flows.
         Все інше — unit/integration.
```

---

## Крок 0 — Запуск

```bash
# 1. Перейти до папки проєкту
cd module_5/lesson_Django_Testing/crispy_notes_project

# 2. Встановити залежності (якщо ще не встановлені)
pip install -r requirements.txt

# 3. Застосувати міграції
python manage.py migrate

# 4. Запустити сервер (для ручної перевірки)
python manage.py runserver
```

### Що дивитись у браузері

| URL | Що показує |
|-----|-----------|
| `http://127.0.0.1:8000/notes/` | Список нотаток (тільки залогінені) |
| `http://127.0.0.1:8000/groups/` | Групи поточного юзера |
| `http://127.0.0.1:8000/admin/` | Django Admin — моделі які ми тестуємо |

---

## Крок 1 — Структура tests/

```
hello_app/
├── models.py
├── views.py
├── forms.py
├── services.py
├── selectors.py
└── tests/                      ← пакет (директорія з __init__.py)
    ├── __init__.py              ← порожній файл, робить tests/ пакетом Python
    ├── test_models.py           ← Unit: constraints, __str__, SET_NULL (23 тести)
    ├── test_services.py         ← Unit: бізнес-логіка, security (36 тестів)
    ├── test_forms.py            ← Unit: валідація, queryset filtering (23 тести)
    ├── test_views.py            ← Integration: HTTP, ownership, redirects (41 тест)
    └── test_selenium.py         ← E2E: браузер (6 тестів, skip без geckodriver)
```

### Чому `tests/` пакет, а не один `tests.py`?

```
# Варіант 1: один файл tests.py
hello_app/tests.py   ← все в одному → стає 2000+ рядків, важко орієнтуватись

# Варіант 2: пакет tests/ (наш варіант)
hello_app/tests/
    test_models.py    ← тільки моделі   (23 тести)
    test_services.py  ← тільки сервіси  (36 тестів)
    test_forms.py     ← тільки форми    (23 тести)
    test_views.py     ← integration     (41 тест)
    test_selenium.py  ← E2E             (6 тестів)
```

### `__init__.py` — без нього не працює

```python
# hello_app/tests/__init__.py
# Файл порожній, але ОБОВ'ЯЗКОВИЙ.
# Без нього Django не знайде тести у цій директорії.
```

---

## Крок 2 — test_models.py

```python
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from hello_app.models import Note, Notebook, ShopItem, ShoppingList, Tag
```

### Що імпортуємо і навіщо

| Імпорт | Навіщо |
|--------|--------|
| `TestCase` | Базовий клас Django — транзакція + тестова БД |
| `IntegrityError` | Для тестів `unique_together` і `CHECK constraint` |
| `ValidationError` | Для тестів `full_clean()` — validators |
| `Group, User` | Django вбудовані моделі (використовуються у Note.group) |

### Ключові assert методи у тестах моделей

```python
self.assertEqual(str(tag), '#python')     # рівність рядків
self.assertFalse(note.is_pinned)          # перевірка False
self.assertIsNone(note.group)             # перевірка None
self.assertIsNotNone(note.created_at)     # перевірка що не None
self.assertIn('Milk', str(item))          # підрядок у рядку
self.assertGreaterEqual(updated, old)     # порівняння дат

# Для перевірки винятків:
with self.assertRaises(IntegrityError):
    Tag.objects.create(user=user, name='duplicate')

with self.assertRaises(ValidationError) as ctx:
    note.full_clean()
self.assertIn('priority', ctx.exception.message_dict)
```

---

## Крок 3 — test_services.py

```python
from django.contrib.auth.models import Group, User
from django.test import TestCase
from hello_app import services
from hello_app.models import Note, Notebook, Tag, TodoList
```

### BaseServiceTest — уникаємо дублювання

```python
class BaseServiceTest(TestCase):
    """
    Базовий клас з загальним setUp.
    Всі класи-нащадки автоматично отримують self.alice і self.bob.
    """
    def setUp(self):
        self.alice = User.objects.create_user('alice', password='pass123')
        self.bob   = User.objects.create_user('bob',   password='pass123')


class NoteServiceTest(BaseServiceTest):
    # setUp() НЕ потрібен — inherited від BaseServiceTest
    # self.alice і self.bob доступні в кожному тесті

    def test_create_note_sets_correct_user(self):
        note = services.create_note(user=self.alice, title='Test')
        self.assertEqual(note.user, self.alice)
```

### Persistence тест — "чи справді збереглось?"

```python
def test_toggle_pin_note_persisted_in_db(self):
    """
    ВАЖЛИВО: перевіряємо що зміна збережена в БД, а не тільки в пам'яті.

    Помилковий код міг би:
        note.is_pinned = True   ← змінив в пам'яті
        return note             ← повернув, але не зберіг!

    Тест ЯВНО читає з БД знову:
    """
    note = Note.objects.create(user=self.alice, title='Test', is_pinned=False)
    services.toggle_pin_note(note)

    # Завантажуємо НОВИЙ об'єкт з БД — ігноруємо кешований в пам'яті
    note_from_db = Note.objects.get(pk=note.pk)
    self.assertTrue(note_from_db.is_pinned)
    #                ↑ справді True в БД, не тільки у пам'яті об'єкта
```

### TodoListServiceTest — setUp() що наслідує базовий

```python
class TodoListServiceTest(BaseServiceTest):

    def setUp(self):
        super().setUp()   # ← ОБОВ'ЯЗКОВО! Викликаємо setUp батьківського класу
        # Додаткова підготовка специфічна для цього класу:
        self.todo_list = services.create_todo_list(
            user=self.alice, title='Alice Shopping'
        )
        # Тепер self.alice, self.bob і self.todo_list доступні в кожному тесті
```

---

## Крок 4 — test_forms.py

```python
from django.contrib.auth.models import Group, User
from django.test import TestCase
from hello_app.forms import GroupCreateForm, NoteForm, TagForm
from hello_app.models import Notebook, Tag
```

### Тестуємо форму без HTTP

```python
# Форма без HTTP-запиту — тільки Python:

# Перевіряємо valid дані:
form = NoteForm(data={'title': 'Test', 'priority': 1}, user=self.alice)
self.assertTrue(form.is_valid(), msg=form.errors)
# ↑ msg=form.errors — якщо провалиться, побачимо ЧОМУ невалідна

# Перевіряємо invalid дані:
form = NoteForm(data={'title': '', 'priority': 1}, user=self.alice)
self.assertFalse(form.is_valid())
self.assertIn('title', form.errors)
# ↑ Перевіряємо що помилка у КОНКРЕТНОМУ полі (не загальна)

# Перевіряємо cleaned_data (нормалізація):
form = TagForm(data={'name': 'Python', 'color': '#ff'})
form.is_valid()
self.assertEqual(form.cleaned_data['name'], 'python')
```

### NoteFormSecurityTest — повний security блок

```python
class NoteFormSecurityTest(BaseFormTest):

    def setUp(self):
        super().setUp()
        # Обидва юзери мають свої записники
        self.alice_notebook = Notebook.objects.create(user=self.alice, title="Alice's")
        self.bob_notebook   = Notebook.objects.create(user=self.bob,   title="Bob's")

    def test_notebook_queryset_contains_user_notebooks(self):
        """Alice бачить СВІЙ записник у dropdown."""
        form = NoteForm(user=self.alice)
        self.assertIn(self.alice_notebook, form.fields['notebook'].queryset)

    def test_notebook_queryset_excludes_other_user_notebooks(self):
        """Alice НЕ бачить записники Bob'а — IDOR неможливий."""
        form = NoteForm(user=self.alice)
        self.assertNotIn(self.bob_notebook, form.fields['notebook'].queryset)

    def test_group_queryset_excludes_groups_user_not_in(self):
        """Alice не бачить групи де вона не є членом."""
        group = Group.objects.create(name="Bob's Team")
        self.bob.groups.add(group)        # тільки Bob у групі

        form = NoteForm(user=self.alice)
        self.assertNotIn(group, form.fields['group'].queryset)
```

---

## Крок 5 — test_views.py

### Структура файлу

```python
from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from hello_app.models import Note, Notebook, TodoList

class BaseViewTest(TestCase):         # ← спільний setUp
class AuthenticationViewTest(...)     # ← login_required на всіх views
class NoteListViewTest(...)           # ← multi-tenant ізоляція
class NoteDetailViewTest(...)         # ← ownership + group access
class NoteCreateViewTest(...)         # ← form valid/invalid, IDOR prevention
class NoteEditViewTest(...)           # ← ownership check (чужий → 404)
class NoteDeleteViewTest(...)         # ← ownership + cascade до БД
class NotebookViewTest(...)           # ← ownership via get_object_or_404
class GroupViewTest(...)              # ← membership check
class TodoListSharingViewTest(...)    # ← share/unshare workflow
```

### Три найважливіших паттерни

**1. Перевірка login_required**

```python
def test_note_list_redirects_anonymous(self):
    """Незалогінений юзер не може переглянути список нотаток."""
    response = self.client.get(reverse('hello_app:note_list'))
    # Не 200! → redirect на login page
    self.assertEqual(response.status_code, 302)
    self.assertIn('/accounts/login/', response['Location'])
```

**2. Ownership check — Bob отримує 404**

```python
def test_non_owner_gets_404(self):
    """
    Bob (не власник) намагається переглянути нотатку Alice → 404.

    Чому 404 а не 403?
    404 — нічого не відомо про ресурс. Безпечніше.
    403 — ресурс існує, але доступ заборонено. Розкриває інформацію.
    """
    self.client.force_login(self.bob)
    response = self.client.get(
        reverse('hello_app:note_detail', args=[self.alice_note.pk])
    )
    self.assertEqual(response.status_code, 404)
```

**3. IDOR prevention через view**

```python
def test_form_rejects_other_users_notebook_idor_prevention(self):
    """
    Alice намагається POST з notebook=bob_notebook.id.
    NoteForm(user=alice) queryset не містить Bob's notebook → invalid choice.
    """
    bob_notebook = Notebook.objects.create(user=self.bob, title="Bob Notebook")
    self.client.force_login(self.alice)
    response = self.client.post(
        reverse('hello_app:note_create'),
        data={'title': 'Hack Note', 'notebook': bob_notebook.pk, 'priority': 1},
    )
    self.assertEqual(response.status_code, 200)  # ← форма invalid, не redirect
    self.assertFalse(Note.objects.filter(title='Hack Note').exists())
```

### Схема доступу: що повертає кожен view для кожного юзера

```
                    alice     bob (not member)   bob (member of group)
note_list           200       200 (own notes)    200 (own notes)
note_detail (own)   200       404                404
note_detail (group) 200       404                200 ← group access!
note_edit           200       404                302+error
note_delete         302 ok    404                302+error
notebook_edit       200       404                404
group_detail        200       404                200 ← if member
group_delete        302 ok    403                403
```

---

## Крок 6 — test_selenium.py

### Структура файлу

```python
import unittest
try:
    from selenium import webdriver
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from django.contrib.staticfiles.testing import StaticLiveServerTestCase

@unittest.skipUnless(SELENIUM_AVAILABLE, "selenium not installed")
class SeleniumLoginFlowTest(StaticLiveServerTestCase):
    # test_login_page_renders
    # test_valid_login_redirects_to_notes
    # test_invalid_login_shows_error

@unittest.skipUnless(SELENIUM_AVAILABLE, "selenium not installed")
class SeleniumNoteFlowTest(StaticLiveServerTestCase):
    # test_note_list_page_loads
    # test_create_note_via_form
    # test_created_note_appears_in_list
```

### Як запустити Selenium

```bash
# 1. Встановити selenium
pip install selenium

# 2. Завантажити geckodriver для Firefox
#    https://github.com/mozilla/geckodriver/releases
#    → розпакувати і додати до PATH

# 3. Запустити
python manage.py test hello_app.tests.test_selenium -v 2
```

### Якщо selenium НЕ встановлений

```bash
python manage.py test hello_app.tests -v 1

# Вивід:
# ...........s.s.s.s.s.s.........
# Ran 129 tests in 90.2s
# OK (skipped=6)   ← 6 Selenium тестів пропущені, але не впали!
```

`s` = skipped. `@unittest.skipUnless(SELENIUM_AVAILABLE, ...)` — якщо пакет не встановлений, тести позначаються skip. Загальний результат `OK`.

---

## Крок 7 — Запуск

### Команди запуску

```bash
# Всі тести (unit + integration + E2E)
python manage.py test hello_app.tests

# Тільки unit тести (швидко)
python manage.py test hello_app.tests.test_models
python manage.py test hello_app.tests.test_services
python manage.py test hello_app.tests.test_forms

# Тільки integration тести
python manage.py test hello_app.tests.test_views

# Тільки Selenium E2E
python manage.py test hello_app.tests.test_selenium

# Конкретний клас
python manage.py test hello_app.tests.test_views.NoteDetailViewTest

# Конкретний тест
python manage.py test hello_app.tests.test_views.NoteDetailViewTest.test_group_member_can_view_note

# З детальним виводом
python manage.py test hello_app.tests -v 2

# Зупинитись при першому провалі
python manage.py test hello_app.tests --failfast
```

### Очікуваний результат

```
$ python manage.py test hello_app.tests -v 1

Creating test database for alias 'default' ...
Found 129 test(s).
...........................................................................................................................ssssss
----------------------------------------------------------------------
Ran 129 tests in 90.2s

OK (skipped=6)
Destroying test database for alias 'default' ...
```

### Ключ до виводу

```
...........   ← крапки = passed tests
s             ← s = skipped (Selenium без geckodriver)
F             ← F = failed (assertion не спрацювала)
E             ← E = error (виняток у тесті, не assertion)

Ran 129 tests in 90.2s   ← 129 тестів разом
OK (skipped=6)           ← все зелено, 6 пропущено (очікувано)

Якщо бачиш FAILED (failures=X, errors=Y) — читай Traceback.
Traceback показує: файл, рядок, що очікувалось, що отримали.
```

### Що означають цифри

```
82  — unit тести (models + services + forms)
41  — integration тести (views через Test Client)
 6  — E2E тести (Selenium, skip без geckodriver)
───
129 — всього
```

---

## Крок 8 — GitHub Actions CI

> **Мета:** кожен `git push` автоматично запускає ті самі тести, які ти щойно навчився писати.
> Без твоєї участі. На чистому сервері. З результатом у GitHub за 2–3 хвилини.

### Де живе workflow

```
PY-Course-Victor-Nikoriak-23_02/          ← корінь репозиторію
└── .github/
    └── workflows/
        └── django-tests.yml              ← ★ РЕАЛЬНИЙ файл, GitHub бачить його
```

Файл `crispy_notes_project/.github/workflows/django-tests.yml` — **зразок/довідка**.
GitHub Actions читає workflow ТІЛЬКИ з кореневої папки репозиторію. Усе інше ігнорується.

---

### Що відбувається при git push

```
Ти:  git push origin main
         │
         ▼
GitHub:  Detect event → push до main
         paths змінились? module_5/lesson_Django_Testing/** → YES
         │
         ▼
Azure:   Provision Ubuntu 22.04 VM (нова, чиста)
         │
         ├── Job 1: unit-and-integration (~1-2 хв)
         │     checkout → python 3.12 → pip install → manage.py check → manage.py test
         │     Результат: ✅ або ❌
         │
         └── Job 2: selenium-e2e (~1-2 хв) — тільки якщо Job 1 ✅
               checkout → pip install → manage.py test test_selenium
               Chrome встановлений на ubuntu-latest, Selenium Manager = chromedriver
               Результат: ✅ або ❌
         │
         ▼
GitHub:  Зелений/червоний статус на коміті + email якщо ❌
```

---

### Повний workflow: рядок за рядком

Файл: [`.github/workflows/django-tests.yml`](../../../../.github/workflows/django-tests.yml)

#### Назва і тригери

```yaml
name: Django Tests (module_5/lesson_Django_Testing)
```

Ця назва відображається у вкладці **Actions** у GitHub.

```yaml
on:
  push:
    branches: [ main, master ]
    paths:
      - 'module_5/lesson_Django_Testing/**'
      - '.github/workflows/django-tests.yml'
  pull_request:
    branches: [ main, master ]
    paths:
      - 'module_5/lesson_Django_Testing/**'
      - '.github/workflows/django-tests.yml'
  workflow_dispatch:
```

**`on`** — визначає коли запускати workflow.
📖 [Документація: Events that trigger workflows](https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows)

| Ключ | Що означає |
|------|-----------|
| `push` | При кожному git push |
| `branches` | Тільки для гілок `main` або `master` |
| `paths` | **Тільки якщо ці файли змінились.** Якщо ти правиш module_1 — workflow не запускається |
| `pull_request` | При відкритті або оновленні PR |
| `workflow_dispatch` | Кнопка "Run workflow" у GitHub UI → Actions |

**Навіщо `paths`?**

Без `paths` — кожен push до будь-якого файлу курсу запускав би тести Django уроку. З `paths` — workflow запускається тільки коли змінились файли саме цього уроку або сам workflow. Економить хвилини CI.

---

#### Job 1: Unit & Integration Tests

```yaml
jobs:
  unit-and-integration:
    name: Unit & Integration Tests
    runs-on: ubuntu-latest
```

**`runs-on: ubuntu-latest`** — тип runner. Це свіжа Ubuntu 22.04 VM на Azure. Після завершення job VM знищується. Між запусками немає ніякого стану.

📖 [Документація: GitHub-hosted runners](https://docs.github.com/en/actions/using-github-hosted-runners/using-github-hosted-runners/about-github-hosted-runners#standard-github-hosted-runners-for-public-repositories)

```yaml
    defaults:
      run:
        working-directory: module_5/lesson_Django_Testing/crispy_notes_project
```

**`defaults.run.working-directory`** — усі команди `run:` у цьому job виконуються з цієї директорії. Без цього кожна команда починалась би з кореня репозиторію і треба було б писати `cd module_5/...` перед кожним кроком.

📖 [Документація: defaults.run](https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions#defaultsrun)

---

**Step 1 — Checkout**

```yaml
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
```

Клонує весь репозиторій на VM. Без цього кроку на runner немає жодного файлу з твоїм кодом.

📖 [actions/checkout на GitHub Marketplace](https://github.com/marketplace/actions/checkout)

---

**Step 2 — Setup Python**

```yaml
      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
```

Встановлює потрібну версію Python. Ubuntu-latest має кілька версій Python, цей action обирає і активує потрібну.

📖 [actions/setup-python на GitHub Marketplace](https://github.com/marketplace/actions/setup-up-a-specific-version-of-python)

---

**Step 3 — Cache pip**

```yaml
      - name: Cache pip dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('module_5/lesson_Django_Testing/crispy_notes_project/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-
```

Кешує папку `~/.cache/pip` між запусками workflow.

**Як це працює:**
1. При першому run — кешу немає, pip завантажує пакети (~60 секунд), кеш зберігається
2. При наступних runs — якщо `requirements.txt` не змінився, `key` збігається → pip завантажує пакети з кешу (~5 секунд)
3. Якщо `requirements.txt` змінився → `key` новий → кеш не знайдений → `restore-keys` дає частковий match → оновлення кешу

`${{ hashFiles(...) }}` — вираз GitHub Actions. Повертає SHA-256 хеш файлу. Якщо файл не змінився — хеш той самий → кеш влучний.

📖 [actions/cache на GitHub Marketplace](https://github.com/marketplace/actions/cache)
📖 [Документація: Caching dependencies](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/caching-dependencies-to-speed-up-workflows)

---

**Step 4 — Install dependencies**

```yaml
      - name: Install dependencies
        run: pip install -r requirements.txt
```

Проста shell команда. Виконується з `working-directory` → тобто з `crispy_notes_project/`.

---

**Step 5 — Django system check**

```yaml
      - name: Django system check
        run: python manage.py check
```

`manage.py check` — вбудована Django команда. Перевіряє:
- Правильність `settings.py`
- Синтаксис моделей
- Конфігурацію middleware
- URL patterns

Якщо є помилка у конфігурації — дізнаєшся тут за 3 секунди, а не після 2 хвилин тестів.

📖 [Документація: Django system check framework](https://docs.djangoproject.com/en/5.2/topics/checks/)

---

**Step 6 — Run tests**

```yaml
      - name: Run unit and integration tests
        run: |
          python manage.py test \
            hello_app.tests.test_models \
            hello_app.tests.test_services \
            hello_app.tests.test_forms \
            hello_app.tests.test_views \
            -v 2
```

Запускає 123 тести (unit + integration). Явно перераховані модулі без `test_selenium` — Selenium в окремому job.

`-v 2` — verbose: кожен тест виводиться окремим рядком. В CI це корисно: одразу видно яке ім'я тесту впало.

Якщо будь-який тест повертає `FAILED` → step повертає exit code 1 → GitHub Actions вважає step провалений → job зупиняється → Job 2 (selenium) не запускається.

---

**Step 7 — Coverage**

```yaml
      - name: Generate coverage report
        run: |
          coverage run manage.py test \
            hello_app.tests.test_models \
            hello_app.tests.test_services \
            hello_app.tests.test_forms \
            hello_app.tests.test_views
          coverage report --show-missing
          coverage xml -o coverage.xml
```

`coverage run` — запускає тести через `coverage`, відстежуючи які рядки коду виконуються.

`coverage report --show-missing` — виводить таблицю:

```
Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
hello_app/models.py             87      3    97%   45, 67, 89
hello_app/services.py          124      8    94%   34-41
hello_app/views.py             198     12    94%   ...
-----------------------------------------------------------
TOTAL                          409     23    94%
```

`coverage xml -o coverage.xml` — зберігає у XML для інтеграції з Codecov / SonarQube.

📖 [Coverage.py документація](https://coverage.readthedocs.io/en/latest/)

---

**Step 8 — Upload artifact**

```yaml
      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        with:
          name: coverage-xml
          path: module_5/lesson_Django_Testing/crispy_notes_project/coverage.xml
```

Зберігає `coverage.xml` як артефакт — файл прикріплюється до workflow run і його можна завантажити з GitHub UI.

Шлях вказаний відносно кореня репозиторію (не `working-directory`) — artifact upload не успадковує `defaults.run.working-directory`.

📖 [actions/upload-artifact на GitHub Marketplace](https://github.com/marketplace/actions/upload-a-build-artifact)

---

#### Job 2: Selenium E2E

```yaml
  selenium-e2e:
    name: Selenium E2E Tests
    runs-on: ubuntu-latest
    needs: unit-and-integration
```

**`needs: unit-and-integration`** — Job 2 запускається тільки після того як Job 1 завершився успішно. Якщо unit тести впали — Selenium навіть не стартує. Це правильно: нема сенсу перевіряти браузерний flow якщо базова логіка вже зламана.

📖 [Документація: needs](https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions#jobsjob_idneeds)

---

**Чому без service container для Selenium**

У зразку всередині проєкту (`crispy_notes_project/.github/...`) є секція `services: selenium: image: selenium/standalone-chrome`. Реальний workflow її **не використовує**. Ось чому:

```
Проблема з service container:

  Runner VM                     Docker container (selenium/standalone-chrome)
  ┌─────────────────────┐       ┌─────────────────────────────────────┐
  │ Django test server  │       │ Chrome                              │
  │ http://localhost:PORT│       │                                     │
  │                     │       │  Chrome відкриває                   │
  │                     │◄──────│  http://localhost:PORT              │
  └─────────────────────┘       │                                     │
                                │  ALE! localhost контейнера ≠        │
                                │  localhost runner-а                 │
                                │  → ERR_CONNECTION_REFUSED           │
                                └─────────────────────────────────────┘

Рішення (реальний workflow):

  Runner VM — все на одній машині
  ┌─────────────────────────────────────────────────────┐
  │ Django test server       Chrome (вже встановлений)  │
  │ http://localhost:PORT ◄─ http://localhost:PORT ✅    │
  │                                                     │
  │ Selenium Manager автоматично завантажує chromedriver│
  └─────────────────────────────────────────────────────┘
```

`ubuntu-latest` включає Chrome. `selenium>=4.6` має вбудований Selenium Manager — він сам знаходить встановлений Chrome і завантажує відповідну версію `chromedriver`. Нічого додатково не треба.

---

**Step — Run Selenium**

```yaml
      - name: Run Selenium E2E tests
        run: python manage.py test hello_app.tests.test_selenium -v 2
```

Без змінної `SELENIUM_REMOTE_URL` → `_make_driver()` у коді тестів використовує локальний Chrome з headless режимом. Django `StaticLiveServerTestCase` запускає сервер на випадковому порту, Chrome підключається до нього на тому ж `localhost`.

---

### Як переглянути результати

**1. Actions tab у репозиторії**

```
https://github.com/NikoriakViktot/PY-Course-Victor-Nikoriak-23_02/actions
```

Тут список всіх workflow runs. Зелений — all green. Червоний — щось впало.

**2. Граф Jobs**

Клікни на конкретний run → бачиш два прямокутники:

```
[Unit & Integration Tests] ──needs──► [Selenium E2E Tests]
      ✅ 1m 23s                              ✅ 1m 47s
```

**3. Logs конкретного step**

Клікни на job → клікни на step → розгорни:

```
Run python manage.py test ...

Creating test database for alias 'default' ...
Found 123 test(s).
test_str_returns_hash_name (hello_app.tests.test_models.TagModelTest) ... ok
test_unique_together_same_user_same_name_raises (...) ... ok
...
----------------------------------------------------------------------
Ran 123 tests in 34.2s
OK
```

**4. Download artifacts**

Actions run → Artifacts (внизу сторінки) → `coverage-xml` → завантажити `coverage.xml`.

**5. Статус на коміті**

Кожен коміт у списку комітів отримує значок:
- `✅` — всі workflow пройшли
- `❌` — хтось впав
- `🟡` — виконується

---

### Що значить кожен рядок у лозі при помилці

```
FAIL: test_note_list_excludes_other_user_notes
      ↑ Назва тесту → одразу зрозуміло ЩО зламалось

(hello_app.tests.test_views.NoteListViewTest)
      ↑ Клас і файл → можеш одразу відкрити

Traceback (most recent call last):
  File ".../test_views.py", line 89, in test_note_list_excludes_other_user_notes
    self.assertNotContains(response, "Bob's Secret Note")
AssertionError: Response should not contain "Bob's Secret Note"
      ↑ Очікували що рядка НЕМАЄ, але він є → нотатки Bob'а видимі Alice!
      → Баг у selectors.get_user_notes() — забули фільтр по user

Process completed with exit code 1
      ↑ Django test runner повернув 1 → GitHub Actions вважає step провалений
```

---

### Зв'язок: тести ↔ CI/CD

```
Ти пишеш:                  CI/CD запускає:           Ти отримуєш:

test_models.py    ─────►   Job 1, Step 6         ──► ✅ або ❌ за 30 сек
test_services.py  ─────►   (unit + integration)  ──► Traceback прямо в GitHub
test_forms.py     ─────►
test_views.py     ─────►

test_selenium.py  ─────►   Job 2                 ──► ✅ або ❌ після Job 1
                            (E2E, needs: job1)    ──► Chrome headless на Azure
```

Кожен тест, який ти написав у кроках 2–6, автоматично запускається у CI при кожному push.

---

### Посилання на документацію

| Тема | Посилання |
|------|-----------|
| GitHub Actions — Quick Start | https://docs.github.com/en/actions/writing-workflows/quickstart |
| Understanding GitHub Actions | https://docs.github.com/en/actions/about-github-actions/understanding-github-actions |
| Events that trigger workflows | https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows |
| Workflow syntax (повний довідник) | https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions |
| Caching dependencies | https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/caching-dependencies-to-speed-up-workflows |
| GitHub-hosted runners | https://docs.github.com/en/actions/using-github-hosted-runners/using-github-hosted-runners/about-github-hosted-runners |
| actions/checkout | https://github.com/marketplace/actions/checkout |
| actions/setup-python | https://github.com/marketplace/actions/setup-up-a-specific-version-of-python |
| actions/cache | https://github.com/marketplace/actions/cache |
| actions/upload-artifact | https://github.com/marketplace/actions/upload-a-build-artifact |
| Monitoring workflows (live logs) | https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/monitoring-workflows |
| Coverage.py | https://coverage.readthedocs.io/en/latest/ |
| Django system check | https://docs.djangoproject.com/en/5.2/topics/checks/ |
| Selenium Manager | https://www.selenium.dev/documentation/selenium_manager/ |

---

### Практика: перевір що CI/CD працює

1. Відкрий у браузері: `https://github.com/NikoriakViktot/PY-Course-Victor-Nikoriak-23_02/actions`
2. Знайди workflow **"Django Tests (module_5/lesson_Django_Testing)"**
3. Клікни на останній run
4. Розгорни Job 1 → Step "Run unit and integration tests"
5. Знайди рядок `Ran 123 tests in ... OK`
6. Перейди до Job 2 → подивись як запускається Selenium на Ubuntu runner

**Самостійно:** зроби навмисну помилку в будь-якому тесті (`assertFalse(True)`), зроби `git push`, подивись як CI показує FAIL і Traceback.

---

```
crispy_notes_project/
│
├── README.md                         ← ВИ ТУТ — повний туторіал по тестуванню
│
├── requirements.txt                  ← Django>=5.2, crispy-forms, crispy-bootstrap5
│
├── hello_project/
│   ├── settings.py                   ← конфігурація (EMAIL_BACKEND=console для тестів)
│   └── urls.py
│
├── hello_app/
│   ├── models.py                     ← Note, Tag, Notebook, ShopItem — що тестуємо
│   ├── forms.py                      ← NoteForm, TagForm, GroupCreateForm — що тестуємо
│   ├── services.py                   ← create_note, create_group — що тестуємо
│   ├── selectors.py                  ← ORM запити (тести через integration layer)
│   ├── views.py                      ← HTTP handlers — що тестуємо через Test Client
│   │
│   └── tests/                        ← ★ ПАПКА З ТЕСТАМИ (129 тестів)
│       ├── __init__.py               ← порожній — робить tests/ пакетом
│       ├── test_models.py            ←  23 unit тести: constraints, __str__, SET_NULL
│       ├── test_services.py          ←  36 unit тести: CRUD, security, транзакції
│       ├── test_forms.py             ←  23 unit тести: валідація, нормалізація, IDOR
│       ├── test_views.py             ←  41 integration: HTTP, ownership, redirects
│       └── test_selenium.py          ←   6 E2E: браузер (skip без geckodriver)
│
└── templates/                        ← HTML шаблони
```

---

## Підсумок: що і де вчити

### Unit тести

| Концепція | Де дивитись у коді |
|-----------|-------------------|
| **Базова структура тесту** | Будь-який метод test_* — Arrange / Act / Assert |
| **setUp і tearDown** | `BaseServiceTest.setUp()` в `test_services.py` |
| **assertRaises** | `test_models.py` — `TagModelTest.test_unique_together_*` |
| **full_clean() vs save()** | `test_models.py` — `test_priority_above_4_raises_validation_error` |
| **refresh_from_db()** | `test_models.py` — `test_note_group_becomes_null_when_group_deleted` |
| **Persistence test** | `test_services.py` — `test_toggle_pin_note_persisted_in_db` |
| **Security (Mass Assignment)** | `test_services.py` — `test_create_note_ignores_other_users_tags` |
| **Транзакційна логіка** | `test_services.py` — `test_create_notebook_default_unsets_previous_default` |
| **Ізоляція між юзерами** | `test_services.py` — `test_create_notebook_default_only_affects_same_user` |
| **Form queryset security** | `test_forms.py` — `NoteFormSecurityTest` (7 тестів) |

### Integration тести (test_views.py)

| Концепція | Де дивитись у коді |
|-----------|-------------------|
| **force_login vs login** | `BaseViewTest.setUp()` — `self.client.force_login(alice)` |
| **@login_required check** | `AuthenticationViewTest` — 8 тестів (всі захищені URL) |
| **response.status_code** | `NoteListViewTest.test_authenticated_user_gets_200` |
| **assertContains / assertNotContains** | `NoteListViewTest.test_note_list_excludes_other_user_notes` |
| **Ownership: 404 для чужого** | `NoteDetailViewTest.test_non_owner_gets_404` |
| **Group-based access** | `NoteDetailViewTest.test_group_member_can_view_note` |
| **IDOR через view** | `NoteCreateViewTest.test_form_rejects_other_users_notebook_*` |
| **Form errors у context** | `NoteCreateViewTest.test_empty_title_shows_form_error` |
| **assertRedirects** | `NoteDeleteViewTest.test_delete_redirects_to_note_list` |
| **403 Forbidden** | `GroupViewTest.test_non_member_delete_returns_403` |
| **Sharing workflow** | `TodoListSharingViewTest.test_shared_user_can_view_todo_list` |

### E2E тести (test_selenium.py)

| Концепція | Де дивитись у коді |
|-----------|-------------------|
| **StaticLiveServerTestCase** | Базовий клас Selenium тестів |
| **Session cookie trick** | `SeleniumNoteFlowTest._login_via_cookie()` |
| **Headless Firefox** | `_make_headless_driver()` — `options.add_argument('--headless')` |
| **implicitly_wait** | `setUpClass` — `cls.driver.implicitly_wait(5)` |
| **skipUnless** | `@unittest.skipUnless(SELENIUM_AVAILABLE, ...)` |
| **find_element + send_keys** | `SeleniumLoginFlowTest.test_valid_login_redirects_to_notes` |
| **page_source check** | `SeleniumNoteFlowTest.test_created_note_appears_in_list` |

---

## Документація уроку

| Файл | Тема |
|------|------|
| [`../README.md`](../README.md) | Навігація по всьому уроку тестування |
| [`../TESTING_FOUNDATIONS.md`](../TESTING_FOUNDATIONS.md) | Піраміда, принципи, AAA |
| [`../UNITTEST_BASICS.md`](../UNITTEST_BASICS.md) | Python unittest: TestCase, lifecycle |
| [`../PYTEST_BASICS.md`](../PYTEST_BASICS.md) | pytest: fixtures, parametrize |
| [`../DJANGO_TESTING.md`](../DJANGO_TESTING.md) | Django: TestCase, Client, тестова БД |
| [`../TEST_DATA_AND_FIXTURES.md`](../TEST_DATA_AND_FIXTURES.md) | factory_boy, fixtures |
| [`../MOCKING_AND_PATCHING.md`](../MOCKING_AND_PATCHING.md) | Mock, patch, зовнішні сервіси |
| [`../TESTING_PRACTICE_PROJECT.md`](../TESTING_PRACTICE_PROJECT.md) | E2E, Selenium, повний сценарій |
| [`../SELENIUM.md`](../SELENIUM.md) | Selenium WebDriver: By стратегії, waits, StaticLiveServerTestCase, session cookie trick |
| [`../CI_CD.md`](../CI_CD.md) | CI/CD теорія, GitHub Actions компоненти, events, runners |
| [`.github/workflows/django-tests.yml`](.github/workflows/django-tests.yml) | Зразок workflow для цього проєкту |
| [`../../../../.github/workflows/django-tests.yml`](../../../../.github/workflows/django-tests.yml) | Реальний workflow (корінь репо) |
| [`../basics/`](../basics/) | Runnable Python приклади тестів |
