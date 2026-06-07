"""
04 · PYTEST FIXTURES

Запуск:
    python -m pytest 04_pytest_fixtures.py -v

Фікстура — це функція з декоратором @pytest.fixture.
pytest автоматично передає її як аргумент у тест-функцію.
Приклад:

    @pytest.fixture
    def db():
        return UserRepository()

    def test_db_starts_empty(db):
        assert db.count() == 0

Тут pytest бачить аргумент db у тесті,
шукає фікстуру з назвою db,
виконує її,
і передає результат у тест.

Головна ідея:
    Фікстури потрібні для підготовки тестових даних.

Переваги над setUp():
  - Можна переиикористовувати між файлами (conftest.py)
  - Декларативні залежності (фікстура може залежати від фікстури)
  - yield-фікстури для teardown (без окремого tearDown методу)
  - Scope: function (default) / class / module / session
"""

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Класи для демонстрації
# ─────────────────────────────────────────────────────────────────────────────

class User:
    """
    Простий клас користувача.

    Поля:
        username  — ім'я користувача
        role      — роль користувача: "user" або "admin"
        is_active — активний користувач чи ні

    Метод:
        is_admin() — повертає True, якщо роль користувача дорівнює "admin".
    """

    def __init__(self, username, role="user"):
        self.username = username
        self.role = role
        self.is_active = True

    def is_admin(self):
        return self.role == "admin"


class UserRepository:
    """
    Просте сховище користувачів.

    У реальному проєкті це могла б бути база даних.
    Тут ми імітуємо БД через звичайний словник.

    Структура:
        self._users = {
            "alice": <User object>,
            "admin": <User object>
        }
    """

    def __init__(self):
        self._users = {}

    def save(self, user):
        """
        Зберігає користувача у словник.

        Ключ:
            user.username

        Значення:
            сам об'єкт user
        """
        self._users[user.username] = user
        return user

    def get(self, username):
        """
        Повертає користувача за username.

        Якщо користувача немає, повертає None.
        """
        return self._users.get(username)

    def all(self):
        """
        Повертає список усіх користувачів.
        """
        return list(self._users.values())

    def count(self):
        """
        Повертає кількість користувачів у сховищі.
        """
        return len(self._users)


# ─────────────────────────────────────────────────────────────────────────────
# БАЗОВІ ФІКСТУРИ
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def db():
    """
    Фікстура db.

    Для чого:
        Створює новий UserRepository для тесту.

    Scope:
        За замовчуванням scope="function".

    Це означає:
        pytest створює новий db перед кожним тестом.

    Чому це важливо:
        Кожен тест отримує чистий репозиторій.
        Дані з одного тесту не переходять в інший тест.
    """
    return UserRepository()


@pytest.fixture
def alice(db):
    """
    Фікстура alice.

    Для чого:
        Створює користувача alice з роллю "user"
        і зберігає його у db.

    Важливо:
        Ця фікстура залежить від іншої фікстури db.

    Як це працює:
        pytest бачить, що alice має аргумент db.
        Тому спочатку виконує фікстуру db,
        потім передає її результат у фікстуру alice.
    """
    user = User("alice", role="user")
    db.save(user)
    return user


@pytest.fixture
def admin(db):
    """
    Фікстура admin.

    Для чого:
        Створює користувача admin з роллю "admin"
        і зберігає його у db.

    Так само як alice,
    ця фікстура залежить від db.
    """
    user = User("admin", role="admin")
    db.save(user)
    return user


# ─────────────────────────────────────────────────────────────────────────────
# ТЕСТИ ЩО ВИКОРИСТОВУЮТЬ ФІКСТУРИ
# ─────────────────────────────────────────────────────────────────────────────

def test_db_starts_empty(db):
    """
    Тест: новий db має бути порожній.

    Для чого:
        Перевіряємо, що фікстура db створює чистий репозиторій.

    Очікування:
        У новому UserRepository немає жодного користувача.
    """

    # Arrange
    # pytest автоматично виконав фікстуру db:
    # db = UserRepository()

    # Act
    users_count = db.count()

    # Assert
    assert users_count == 0


def test_save_user(db):
    """
    Тест: збереження користувача в db.

    Для чого:
        Перевіряємо, що метод save() додає користувача в репозиторій.

    Очікування:
        1. Після збереження кількість користувачів дорівнює 1.
        2. Метод get("bob") повертає саме той об'єкт user.
    """

    # Arrange
    user = User("bob")

    # Act
    saved_user = db.save(user)

    # Assert
    assert db.count() == 1
    assert db.get("bob") is user
    assert saved_user is user


def test_alice_is_not_admin(db, alice):
    """
    Тест: alice не є адміністратором.

    Для чого:
        Перевіряємо, що фікстура alice створює звичайного користувача
        з роллю "user", а не "admin".

    Важливо:
        У тест передано дві фікстури:
            db
            alice

        pytest сам розуміє порядок:
            1. створити db;
            2. створити alice і зберегти її в db;
            3. передати db і alice в тест.
    """

    # Arrange
    # pytest підготував:
    # db = UserRepository()
    # alice = User("alice", role="user")
    # db.save(alice)

    # Act
    users_count = db.count()
    is_admin_result = alice.is_admin()

    # Assert
    assert users_count == 1
    assert is_admin_result is False


def test_admin_is_admin(db, admin):
    """
    Тест: admin є адміністратором.

    Для чого:
        Перевіряємо, що фікстура admin створює користувача з роллю "admin".

    Очікування:
        admin.is_admin() має повернути True.
    """

    # Arrange
    # pytest підготував:
    # db = UserRepository()
    # admin = User("admin", role="admin")
    # db.save(admin)

    # Act
    is_admin_result = admin.is_admin()

    # Assert
    assert is_admin_result is True


def test_multiple_users(db, alice, admin):
    """
    Тест: кілька фікстур можуть додавати дані в один db.

    Для чого:
        Перевіряємо, що фікстури alice і admin працюють разом.

    Очікування:
        1. У db має бути 2 користувачі.
        2. db.get("alice") має повернути об'єкт alice.
        3. db.get("admin") має повернути об'єкт admin.

    Важливо:
        У межах одного тесту всі фікстури використовують той самий db.
    """

    # Arrange
    # pytest підготував:
    # db = UserRepository()
    # alice = User("alice", role="user")
    # admin = User("admin", role="admin")
    # db.save(alice)
    # db.save(admin)

    # Act
    users_count = db.count()
    found_alice = db.get("alice")
    found_admin = db.get("admin")

    # Assert
    assert users_count == 2
    assert found_alice is alice
    assert found_admin is admin


# ─────────────────────────────────────────────────────────────────────────────
# YIELD-ФІКСТУРИ
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_log():
    """
    Yield-фікстура.

    Для чого:
        Демонструє setup і teardown в одній функції.

    Як працює:

        Код ДО yield:
            setup — підготовка перед тестом.

        Значення після yield:
            те, що отримає тест.

        Код ПІСЛЯ yield:
            teardown — очищення після тесту.

    Важливо:
        Код після yield виконується після завершення тесту,
        навіть якщо тест впаде з помилкою.
    """

    # Setup
    log = []
    log.append("START")

    # Передаємо log у тест
    yield log

    # Teardown
    log.clear()


def test_log_has_start_entry(temp_log):
    """
    Тест: temp_log починається зі значення "START".

    Для чого:
        Перевіряємо, що yield-фікстура виконала setup-код до yield.

    Очікування:
        temp_log має дорівнювати ["START"].
    """

    # Arrange
    # pytest виконав temp_log:
    # log = []
    # log.append("START")
    # yield log
    #
    # Тому в тест прийшов список:
    # temp_log = ["START"]

    # Act
    actual_log = temp_log

    # Assert
    assert actual_log == ["START"]


def test_log_append(temp_log):
    """
    Тест: у temp_log можна додавати нові записи.

    Для чого:
        Перевіряємо, що тест може працювати з об'єктом,
        який повернула yield-фікстура.

    Очікування:
        1. Після append("step 1") цей текст є у списку.
        2. Довжина списку дорівнює 2:
            ["START", "step 1"]
    """

    # Arrange
    # temp_log вже містить:
    # ["START"]

    new_log_entry = "step 1"

    # Act
    temp_log.append(new_log_entry)

    # Assert
    assert new_log_entry in temp_log
    assert len(temp_log) == 2


# ─────────────────────────────────────────────────────────────────────────────
# SCOPE — Час життя фікстури
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def shared_config():
    """
    Фікстура shared_config зі scope="module".

    Для чого:
        Демонструє фікстуру, яка створюється один раз для всього файлу.

    Scope:
        scope="module"

    Це означає:
        pytest створить shared_config один раз
        і використає її в усіх тестах цього модуля.

    Коли це корисно:
        - дорогий парсинг файлу;
        - завантаження конфігурації;
        - підготовка тестового середовища;
        - створення великого набору даних.
    """
    return {
        "debug": True,
        "max_retries": 3,
        "timeout": 30,
    }


def test_config_has_debug(shared_config):
    """
    Тест: конфігурація має debug=True.

    Для чого:
        Перевіряємо, що shared_config містить ключ "debug"
        і його значення дорівнює True.

    Очікування:
        shared_config["debug"] is True
    """

    # Arrange
    # pytest передав shared_config:
    # {
    #     "debug": True,
    #     "max_retries": 3,
    #     "timeout": 30,
    # }

    # Act
    debug_value = shared_config["debug"]

    # Assert
    assert debug_value is True


def test_config_has_timeout(shared_config):
    """
    Тест: конфігурація має timeout=30.

    Для чого:
        Перевіряємо, що shared_config містить правильне значення timeout.

    Очікування:
        shared_config["timeout"] == 30
    """

    # Arrange
    # shared_config створена один раз для всього модуля.

    # Act
    timeout_value = shared_config["timeout"]

    # Assert
    assert timeout_value == 30


# ─────────────────────────────────────────────────────────────────────────────
# ФІКСТУРИ У КЛАСАХ
# ─────────────────────────────────────────────────────────────────────────────

class TestUserRepository:
    """
    Тестовий клас для UserRepository.

    Важливо:
        У pytest не обов'язково наслідуватися від unittest.TestCase.

    pytest дозволяє писати класи просто так:

        class TestSomething:
            def test_something(self):
                ...

    Фікстури також можна передавати в методи класу
    як звичайні аргументи.
    """

    def test_save_and_get(self, db, alice):
        """
        Тест: збереження і отримання користувача.

        Для чого:
            Перевіряємо, що користувач alice,
            створений фікстурою alice,
            реально збережений у db.

        Очікування:
            db.get("alice") повертає саме той самий об'єкт alice.
        """

        # Arrange
        # pytest підготував:
        # db = UserRepository()
        # alice = User("alice", role="user")
        # db.save(alice)

        # Act
        found = db.get("alice")

        # Assert
        assert found is alice

    def test_get_nonexistent(self, db):
        """
        Тест: отримання неіснуючого користувача.

        Для чого:
            Перевіряємо поведінку методу get(),
            якщо користувача з таким username немає.

        Очікування:
            db.get("nobody") повертає None.
        """

        # Arrange
        username = "nobody"

        # Act
        result = db.get(username)

        # Assert
        assert result is None

    def test_all_returns_list(self, db, alice, admin):
        """
        Тест: метод all() повертає список користувачів.

        Для чого:
            Перевіряємо, що UserRepository.all()
            повертає саме list, а не dict_values, tuple або інший тип.

        Також перевіряємо:
            якщо в db є alice і admin,
            то довжина списку користувачів дорівнює 2.
        """

        # Arrange
        # pytest підготував:
        # db = UserRepository()
        # alice = User("alice", role="user")
        # admin = User("admin", role="admin")
        # db.save(alice)
        # db.save(admin)

        # Act
        users = db.all()

        # Assert
        assert isinstance(users, list)
        assert len(users) == 2