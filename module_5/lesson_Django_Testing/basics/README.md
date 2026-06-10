# basics/ — Основи тестування на чистому Python

> Ці файли **не потребують Django**. Запускаються через `pytest` або `python`.  
> Починай звідси, якщо ще не писав тести.

## Як запустити

```bash
# Встановити pytest (один раз)
pip install pytest

# Перебуваючи в цій директорії:
python -m pytest . -v

# Або один файл:
python -m pytest 01_first_test.py -v
```

## Файли

| Файл | Що навчишся |
|------|-------------|
| `01_first_test.py` | `assert`, `def test_`, запуск pytest |
| `02_unittest_testcase.py` | `TestCase`, `setUp`, `tearDown`, `assertEqual` |
| `03_assertions.py` | Усі корисні методи `assert*` з прикладами |
| `04_pytest_fixtures.py` | `@pytest.fixture`, scope, yield-фікстури |
| `05_parametrize.py` | `@pytest.mark.parametrize` — один тест, багато даних |

## Результат успішного запуску

```
collected 25 items

01_first_test.py::test_add_two_numbers PASSED
01_first_test.py::test_string_upper PASSED
01_first_test.py::test_list_contains PASSED
...
25 passed in 0.12s
```
