"""
05 · PYTEST.MARK.PARAMETRIZE — Один тест, багато наборів даних

Запуск:
    python -m pytest 05_parametrize.py -v

Проблема:
    def test_is_even_2(): assert is_even(2) is True
    def test_is_even_4(): assert is_even(4) is True
    def test_is_even_6(): assert is_even(6) is True
    ... × 10 тестів — дублювання коду

Рішення — parametrize:
    @pytest.mark.parametrize("n", [2, 4, 6, 8, 10])
    def test_is_even(n):
        assert is_even(n) is True

pytest запустить 5 незалежних тестів з одним рядком коду.
"""

import pytest



# ─────────────────────────────────────────────────────────────────────────────
# Функції що тестуємо
# ─────────────────────────────────────────────────────────────────────────────

def is_even(n):
    """
    Перевіряє, чи число парне.

    Парне число — це число, яке ділиться на 2 без остачі.

    Приклади:
        2  -> True
        4  -> True
        7  -> False
        -6 -> True
    """
    return n % 2 == 0


def clamp(value, min_val, max_val):
    """
    Обмежує value в межах min_val і max_val.

    Якщо value менше min_val — повертає min_val.
    Якщо value більше max_val — повертає max_val.
    Якщо value всередині діапазону — повертає саме value.

    Приклади:
        clamp(5, 0, 10)   -> 5
        clamp(-5, 0, 10)  -> 0
        clamp(15, 0, 10)  -> 10
    """
    return max(min_val, min(value, max_val))


def normalize_username(username):
    """
    Нормалізує ім'я користувача.

    Що робить:
        1. strip() прибирає пробіли зліва і справа.
        2. lower() переводить текст у нижній регістр.

    Приклади:
        "Alice"     -> "alice"
        "  BOB  "  -> "bob"
    """
    return username.strip().lower()


def slugify(text):
    """
    Спрощений slugify.

    Що робить:
        1. strip() прибирає пробіли зліва і справа.
        2. lower() переводить текст у нижній регістр.
        3. replace(" ", "-") замінює пробіли на дефіси.

    Приклади:
        "Hello World" -> "hello-world"
        "My Blog Post" -> "my-blog-post"
    """
    return text.strip().lower().replace(" ", "-")


def grade(score):
    """
    Повертає оцінку за балом від 0 до 100.

    Логіка:
        score >= 90 -> "A"
        score >= 75 -> "B"
        score >= 60 -> "C"
        score >= 50 -> "D"
        score < 50  -> "F"
    """
    if score >= 90:
        return "A"
    elif score >= 75:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= 50:
        return "D"
    else:
        return "F"


def parse_priority(value):
    """
    Перетворює текстовий пріоритет на число.

    Мапа значень:
        low    -> 1
        medium -> 2
        high   -> 3
        urgent -> 4

    Додатково:
        - lower() дозволяє приймати "Low", "LOW", "low";
        - strip() дозволяє приймати "  urgent  ".

    Якщо значення невідоме — кидаємо ValueError.
    """
    mapping = {
        "low": 1,
        "medium": 2,
        "high": 3,
        "urgent": 4,
    }

    key = value.lower().strip()

    if key not in mapping:
        raise ValueError(f"Unknown priority: '{value}'")

    return mapping[key]


# ─────────────────────────────────────────────────────────────────────────────
# БАЗОВИЙ PARAMETRIZE
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("n", [0, 2, 4, 100, -6])
def test_is_even_true(n):
    """
    Тест: is_even() повертає True для парних чисел.

    Для чого:
        Перевіряємо, що функція правильно визначає парні числа.

    Як працює parametrize:
        pytest запустить цей тест 5 разів:

            n = 0
            n = 2
            n = 4
            n = 100
            n = -6

    Очікування:
        Для кожного з цих значень is_even(n) має повернути True.
    """

    # Arrange
    # n приходить із parametrize.
    # Наприклад, в одному запуску n = 0,
    # в іншому запуску n = 2,
    # потім n = 4 і так далі.

    # Act
    result = is_even(n)

    # Assert
    assert result is True


@pytest.mark.parametrize("n", [1, 3, 7, -5, 99])
def test_is_even_false(n):
    """
    Тест: is_even() повертає False для непарних чисел.

    Для чого:
        Перевіряємо, що функція правильно визначає непарні числа.

    Як працює parametrize:
        pytest запустить цей тест 5 разів:

            n = 1
            n = 3
            n = 7
            n = -5
            n = 99

    Очікування:
        Для кожного з цих значень is_even(n) має повернути False.
    """

    # Arrange
    # n приходить із parametrize.
    # Кожне значення — окремий запуск тесту.

    # Act
    result = is_even(n)

    # Assert
    assert result is False


# ─────────────────────────────────────────────────────────────────────────────
# PARAMETRIZE З КІЛЬКОМА АРГУМЕНТАМИ
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("username,expected", [
    ("Alice", "alice"),
    ("  BOB  ", "bob"),
    ("CHARLIE123", "charlie123"),
    ("  MiXeD  ", "mixed"),
])
def test_normalize_username(username, expected):
    """
    Тест: normalize_username() нормалізує username.

    Для чого:
        Перевіряємо, що функція:
            1. прибирає пробіли зліва і справа;
            2. переводить текст у нижній регістр.

    Як працює parametrize:
        pytest передає в тест одразу два аргументи:

            username — вхідне значення
            expected — очікуваний результат

    Кейси:
        "Alice"       -> "alice"
        "  BOB  "    -> "bob"
        "CHARLIE123" -> "charlie123"
        "  MiXeD  "  -> "mixed"
    """

    # Arrange
    # username і expected приходять із parametrize.
    # Наприклад:
    # username = "  BOB  "
    # expected = "bob"

    # Act
    result = normalize_username(username)

    # Assert
    assert result == expected


@pytest.mark.parametrize("text,expected", [
    ("Hello World", "hello-world"),
    ("  Django  Testing  ", "django--testing"),
    ("python", "python"),
    ("My Blog Post", "my-blog-post"),
])
def test_slugify(text, expected):
    """
    Тест: slugify() створює простий slug.

    Для чого:
        Перевіряємо, що функція:
            1. прибирає пробіли зліва і справа;
            2. переводить текст у нижній регістр;
            3. замінює пробіли на дефіси.

    Важливий кейс:
        "  Django  Testing  " -> "django--testing"

    Чому два дефіси?
        Тому що всередині тексту є два пробіли між Django і Testing.
        replace(" ", "-") замінює кожен пробіл на окремий дефіс.
    """

    # Arrange
    # text і expected приходять із parametrize.
    # Кожна пара — окремий запуск тесту.

    # Act
    result = slugify(text)

    # Assert
    assert result == expected


# ─────────────────────────────────────────────────────────────────────────────
# PARAMETRIZE З NAMED CASES IDS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("score,expected", [
    (95, "A"),
    (75, "B"),
    (60, "C"),
    (50, "D"),
    (30, "F"),
    (100, "A"),
    (0, "F"),
], ids=[
    "score_95_is_A",
    "score_75_is_B",
    "score_60_is_C",
    "score_50_is_D",
    "score_30_is_F",
    "max_score_is_A",
    "zero_is_F",
])
def test_grade(score, expected):
    """
    Тест: grade() повертає правильну оцінку за балом.

    Для чого:
        Перевіряємо всі основні межі оцінювання.

    Як працює parametrize:
        pytest запустить цей тест 7 разів.

    Для чого потрібні ids:
        ids дають зрозумілі назви кейсам у виводі pytest.

    Наприклад замість:
        test_grade[95-A]

    можна побачити:
        test_grade[score_95_is_A]

    Кейси:
        95  -> "A"
        75  -> "B"
        60  -> "C"
        50  -> "D"
        30  -> "F"
        100 -> "A"
        0   -> "F"
    """

    # Arrange
    # score і expected приходять із parametrize.
    # Наприклад:
    # score = 95
    # expected = "A"

    # Act
    result = grade(score)

    # Assert
    assert result == expected


# ─────────────────────────────────────────────────────────────────────────────
# PARAMETRIZE ДЛЯ ПЕРЕВІРКИ ВАЛІДНИХ ЗНАЧЕНЬ
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("priority_str,expected_int", [
    ("low", 1),
    ("Low", 1),
    ("LOW", 1),
    ("medium", 2),
    ("high", 3),
    ("urgent", 4),
    ("  urgent  ", 4),
])
def test_parse_priority_valid(priority_str, expected_int):
    """
    Тест: parse_priority() правильно обробляє валідні значення.

    Для чого:
        Перевіряємо, що текстові пріоритети перетворюються на числа.

    Очікувана логіка:
        "low"    -> 1
        "medium" -> 2
        "high"   -> 3
        "urgent" -> 4

    Також перевіряємо:
        - регістр не має значення: "Low", "LOW";
        - зайві пробіли прибираються: "  urgent  ".
    """

    # Arrange
    # priority_str і expected_int приходять із parametrize.
    # Наприклад:
    # priority_str = "LOW"
    # expected_int = 1

    # Act
    result = parse_priority(priority_str)

    # Assert
    assert result == expected_int


@pytest.mark.parametrize("invalid_value", [
    "extreme",
    "5",
    "",
    "критичний",
])
def test_parse_priority_invalid(invalid_value):
    """
    Тест: parse_priority() кидає ValueError для невалідних значень.

    Для чого:
        Перевіряємо, що функція не приймає невідомі пріоритети.

    Невалідні кейси:
        "extreme"   — такого пріоритету немає в mapping;
        "5"         — число як текст не підтримується;
        ""          — порожній рядок;
        "критичний" — український текст не входить у mapping.

    Очікування:
        Для кожного такого значення має виникнути ValueError.
    """

    # Arrange
    # invalid_value приходить із parametrize.
    # Кожне значення — окремий запуск тесту.

    # Act + Assert
    with pytest.raises(ValueError) as error:
        parse_priority(invalid_value)

    # Assert
    # Додатково перевіряємо, що повідомлення помилки містить текст Unknown priority.
    assert "Unknown priority" in str(error.value)


# ─────────────────────────────────────────────────────────────────────────────
# PARAMETRIZE З pytest.param
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("value,min_v,max_v,expected", [
    pytest.param(5, 0, 10, 5, id="within_range"),
    pytest.param(-5, 0, 10, 0, id="below_min"),
    pytest.param(15, 0, 10, 10, id="above_max"),
    pytest.param(0, 0, 10, 0, id="exactly_min"),
    pytest.param(10, 0, 10, 10, id="exactly_max"),
    pytest.param(5, 5, 5, 5, id="single_point_range"),
])
def test_clamp(value, min_v, max_v, expected):
    """
    Тест: clamp() обмежує значення в заданому діапазоні.

    Для чого:
        Перевіряємо різні сценарії роботи функції clamp().

    Що таке pytest.param:
        pytest.param дозволяє описати кожен кейс окремо
        і дати йому власний id.

    Кейси:
        within_range:
            value = 5, min = 0, max = 10
            5 уже всередині діапазону.
            Очікуємо 5.

        below_min:
            value = -5, min = 0, max = 10
            -5 менше мінімуму.
            Очікуємо 0.

        above_max:
            value = 15, min = 0, max = 10
            15 більше максимуму.
            Очікуємо 10.

        exactly_min:
            value = 0, min = 0, max = 10
            value дорівнює мінімуму.
            Очікуємо 0.

        exactly_max:
            value = 10, min = 0, max = 10
            value дорівнює максимуму.
            Очікуємо 10.

        single_point_range:
            value = 5, min = 5, max = 5
            мінімум і максимум однакові.
            Очікуємо 5.
    """

    # Arrange
    # value, min_v, max_v і expected приходять із parametrize.
    # Наприклад:
    # value = -5
    # min_v = 0
    # max_v = 10
    # expected = 0

    # Act
    result = clamp(value, min_v, max_v)

    # Assert
    assert result == expected


# ─────────────────────────────────────────────────────────────────────────────
# ПОРІВНЯННЯ: БЕЗ PARAMETRIZE І З PARAMETRIZE
# ─────────────────────────────────────────────────────────────────────────────

# НЕПРАВИЛЬНО — дублювання коду:
#
# def test_grade_95():
#     assert grade(95) == "A"
#
# def test_grade_75():
#     assert grade(75) == "B"
#
# def test_grade_60():
#     assert grade(60) == "C"
#
# def test_grade_50():
#     assert grade(50) == "D"
#
# def test_grade_30():
#     assert grade(30) == "F"
#
#
# ПРОБЛЕМА:
#     Ми повторюємо одну й ту саму структуру тесту багато разів.
#     Змінюються тільки вхідні дані і очікуваний результат.
#
#
# ПРАВИЛЬНО — використовувати parametrize:
#
# @pytest.mark.parametrize("score,expected", [
#     (95, "A"),
#     (75, "B"),
#     (60, "C"),
#     (50, "D"),
#     (30, "F"),
# ])
# def test_grade(score, expected):
#     assert grade(score) == expected
#
#
# ПЕРЕВАГА:
#     Один тест.
#     Багато наборів даних.
#     Менше дублювання.
#     Кращий pytest-вивід.