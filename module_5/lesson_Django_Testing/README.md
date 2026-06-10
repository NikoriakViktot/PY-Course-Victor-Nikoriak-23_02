# Урок: Django Testing — Тестування Django-застосунків

> **Проєкт уроку:** `crispy_notes_project/` — персональний менеджер нотаток з авторизацією,  
> групами та crispy forms. Ми навчимось тестувати кожен шар цього застосунку.

---

## Навіщо тестувати?

Уявіть: ви додали групи до нотаток. Все виглядає добре. Але через 3 тижні, після рефакторингу
`selectors.py`, нотатки вже не фільтруються за групами — і ви про це не знаєте, бо вручну
перевіряти 34 view занадто довго.

**Тести — це автоматична сигналізація.** Вони перевіряють «чи все ще працює» за секунди.

```
БЕЗ ТЕСТІВ:
  git push → CI зелений → деплой → користувачі бачать чужі нотатки

З ТЕСТАМИ:
  git push → CI: FAIL test_note_visible_only_to_owner → виправляємо до деплою
```

---

## 🏔 Піраміда тестування

```
        /\
       /E2E\          ← Selenium: реальний браузер, повний сценарій
      /──────\           (повільно, крихко, дорого)
     /  Integr.\      ← Django TestClient: запити + відповіді + БД
    /────────────\       (середня швидкість, реалістично)
   /    Unit      \   ← pytest/unittest: окрема функція/метод/клас
  /────────────────\     (миттєво, ізольовано, легко писати)
```

**Правило:** 70% unit → 20% integration → 10% E2E

---

## Структура уроку

```
lesson_Django_Testing/
│
├── README.md                     ← ВИ ТУТ — огляд та швидкий старт
│
├── basics/                       ← ПОЧИНАЙ ЗВІДСИ — Python тести без Django
│   ├── README.md                 # Як запускати приклади
│   ├── 01_first_test.py          # Перший тест: assert + def test_
│   ├── 02_unittest_testcase.py   # unittest.TestCase, setUp, tearDown
│   ├── 03_assertions.py          # Повна таблиця assertions
│   ├── 04_pytest_fixtures.py     # @pytest.fixture та scope
│   └── 05_parametrize.py         # @pytest.mark.parametrize
│
├── TESTING_FOUNDATIONS.md        ← Теорія: піраміда, принципи, AAA-паттерн
├── UNITTEST_BASICS.md            ← Python unittest: TestCase, методи, lifecycle
├── PYTEST_BASICS.md              ← pytest: fixtures, markers, конфігурація
├── DJANGO_TESTING.md             ← Django: TestCase, Client, тестова БД
├── TEST_DATA_AND_FIXTURES.md     ← Фікстури, factory_boy, setUp strategies
├── MOCKING_AND_PATCHING.md       ← Mock, patch, зовнішні сервіси
├── TESTING_PRACTICE_PROJECT.md  ← Повний сценарій + Selenium E2E
│
└── crispy_notes_project/         ← Реальний Django проєкт для практики
    └── hello_app/
        └── tests/                ← Наші тести (написані у цьому уроці)
            ├── test_models.py    # Unit: моделі, constraints, relationships
            ├── test_services.py  # Unit: бізнес-логіка, транзакції
            └── test_forms.py     # Unit: валідація, security фільтрування
```

---

## ⚡ Швидкий старт

### 1. Запуск basics/ (не потрібен Django)

```bash
cd module_5/lesson_Django_Testing/basics

# Встановити pytest (якщо не встановлений)
pip install pytest

# Запустити всі приклади
python -m pytest . -v

# Запустити один файл
python -m pytest 01_first_test.py -v
```

### 2. Запуск Django тестів

```bash
cd module_5/lesson_Django_Testing/crispy_notes_project

# Активувати venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Linux/Mac

# Запустити всі тести
python manage.py test hello_app.tests -v 2

# Запустити конкретний модуль
python manage.py test hello_app.tests.test_models -v 2

# Запустити конкретний клас
python manage.py test hello_app.tests.test_services.NoteServiceTest -v 2

# Запустити конкретний тест
python manage.py test hello_app.tests.test_services.NoteServiceTest.test_create_note_assigns_tags -v 2
```

---

## 01 · ОСНОВИ — Що таке тест?

**Тест** — це функція, яка:
1. Готує стан (Arrange)
2. Виконує дію (Act)
3. Перевіряє результат (Assert)

```python
# AAA-паттерн (Arrange / Act / Assert)
def test_capitalize():
    # Arrange — підготуємо вхідні дані
    text = "hello world"

    # Act — виконуємо дію, яку тестуємо
    result = text.capitalize()

    # Assert — перевіряємо, чи результат правильний
    assert result == "Hello world"
```

---

## 02 · ПІДХОДИ — unittest vs pytest

| Критерій | `unittest.TestCase` | `pytest` |
|----------|---------------------|----------|
| Стиль | Клас + методи | Функції або класи |
| Setup | `setUp()` / `tearDown()` | `@pytest.fixture` |
| Django | `django.test.TestCase` | `pytest-django` |
| Assertion | `assertEqual(a, b)` | `assert a == b` |
| Запуск | `manage.py test` | `pytest` |

**У Django зазвичай використовують `django.test.TestCase`** (підклас `unittest.TestCase`) — він
автоматично обгортає кожен тест у транзакцію і відкочує зміни після кожного тесту.

---

## 03 · DJANGO TESTCASE — Особливості

```python
from django.test import TestCase
from django.contrib.auth.models import User

class MyTest(TestCase):
    """
    django.test.TestCase:
    - Створює тестову БД (окрема від робочої!)
    - Кожен тест обгорнутий у транзакцію → rollback після тесту
    - Тому можна вільно створювати/змінювати/видаляти об'єкти
    - Надає self.client — HTTP-клієнт для тестування views
    """

    def setUp(self):
        # setUp() викликається ПЕРЕД кожним тестом
        self.user = User.objects.create_user('alice', password='pass123')

    def tearDown(self):
        # tearDown() викликається ПІСЛЯ кожного тесту (зазвичай не потрібен)
        pass

    def test_user_created(self):
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(self.user.username, 'alice')
```

---

## 04 · АРХІТЕКТУРА crispy_notes_project для тестування

```
Views (HTTP layer)
    ↓ → test_views.py  (Integration: request → response → DB)
Services (business logic)
    ↓ → test_services.py  (Unit: функція → результат у БД)
Selectors (queries)
    ↓ → test_selectors.py  (Unit: запит → правильні об'єкти)
Forms (validation)
    ↓ → test_forms.py  (Unit: дані → valid/invalid + cleaned_data)
Models (data layer)
    ↓ → test_models.py  (Unit: constraints, relationships, __str__)
```

**Ключова перевага архітектури сервісів:** кожен шар можна тестувати ізольовано.

---

## 05 · БЕЗПЕКА — Що тестувати обов'язково

### IDOR (Insecure Direct Object Reference)

IDOR — коли користувач A може прочитати/змінити об'єкт користувача B.

```python
# Приклад IDOR тесту (views):
def test_cannot_edit_other_users_note(self):
    """Alice не повинна редагувати нотатки Bob'а."""
    bob_note = Note.objects.create(user=self.bob, title='Bob secret')

    # Alice намагається відредагувати нотатку Bob'а
    self.client.login(username='alice', password='pass')
    response = self.client.get(f'/notes/{bob_note.pk}/edit/')

    # Очікуємо 404 (не 200 і не 403!)
    self.assertEqual(response.status_code, 404)
```

### Form queryset filtering

```python
def test_note_form_filters_notebooks_by_user(self):
    """Alice не повинна бачити записники Bob'а у своїй формі."""
    bob_notebook = Notebook.objects.create(user=self.bob, title="Bob's notebook")

    form = NoteForm(user=self.alice)

    # Записник Bob'а не повинен бути у queryset Alice
    self.assertNotIn(bob_notebook, form.fields['notebook'].queryset)
```

---

## 06 · ТЕСТУВАННЯ VIEWS — Django Test Client

```python
from django.test import TestCase, Client

class NoteViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', password='pass123')
        self.client.login(username='alice', password='pass123')

    def test_note_list_requires_login(self):
        """Анонімний користувач перенаправляється на login."""
        self.client.logout()
        response = self.client.get('/notes/')
        self.assertRedirects(response, '/accounts/login/?next=/notes/')

    def test_note_create_post(self):
        """POST на /notes/new/ створює нотатку і редиректить."""
        response = self.client.post('/notes/new/', {
            'title': 'Test Note',
            'content': 'Content',
            'priority': 1,
        })
        self.assertRedirects(response, '/notes/')
        self.assertEqual(Note.objects.count(), 1)
        self.assertEqual(Note.objects.first().user, self.user)
```

---

## 07 · MOCKING — Коли потрібний?

Коли код взаємодіє із зовнішніми системами:

```python
from unittest.mock import patch

class EmailTest(TestCase):
    @patch('django.core.mail.send_mail')
    def test_password_reset_sends_email(self, mock_send_mail):
        response = self.client.post('/accounts/password_reset/', {
            'email': 'alice@example.com'
        })
        # Перевіряємо, що send_mail було викликано
        mock_send_mail.assert_called_once()
```

---

## Навчальний маршрут

```
① basics/01_first_test.py         — 10 хвилин
② basics/02_unittest_testcase.py  — 15 хвилин
③ basics/03_assertions.py         — 10 хвилин
④ basics/04_pytest_fixtures.py    — 20 хвилин
⑤ basics/05_parametrize.py        — 15 хвилин
⑥ TESTING_FOUNDATIONS.md          — прочитати теорію
⑦ UNITTEST_BASICS.md              — поглиблено про unittest
⑧ DJANGO_TESTING.md               — Django специфіка
⑨ tests/test_models.py            — дивитись + розуміти
⑩ tests/test_services.py          — дивитись + розуміти
⑪ tests/test_forms.py             — дивитись + розуміти
⑫ TESTING_PRACTICE_PROJECT.md    — самостійно написати views тести
```

---

## Корисні команди

```bash
# Запустити тести з виводом print() (корисно для дебагу)
python manage.py test hello_app.tests --verbosity=2

# Зупинитись на першому провалі
python manage.py test hello_app.tests --failfast

# Запустити тільки тести з певним патерном у назві
python manage.py test hello_app.tests -k "note"  # (через pytest-django)

# pytest (якщо встановлений pytest-django)
pytest hello_app/tests/ -v
pytest hello_app/tests/ -v -k "service"
pytest hello_app/tests/ --tb=short
```

---

*Цей урок є частиною [курсу Python](../../../course.yaml).  
Попередній урок: Django Auth | Наступний урок: Django REST Framework*
