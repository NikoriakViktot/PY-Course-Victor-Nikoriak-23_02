# Selenium WebDriver: автоматизація браузера від першого скрипту до Django E2E

> Цей файл — самодостатній довідник по Selenium Python.
> Від встановлення і першого `driver.get()` до Django `StaticLiveServerTestCase`,
> session cookie trick і Remote WebDriver на GitHub Actions.
> Весь код прив'язаний до реального `test_selenium.py` у нашому проєкті.

📖 Офіційна документація: https://selenium.dev/selenium/docs/api/py
📖 API Reference: https://selenium.dev/selenium/docs/api/py/api.html
📖 GitHub: https://github.com/SeleniumHQ/Selenium

---

## Зміст

**Концепції**
- [1. Навіщо Selenium — що він робить, чого не вміє Test Client](#1-навіщо-selenium)
- [2. Ментальна модель — WebDriver, Driver, Browser](#2-ментальна-модель)
- [3. Selenium Manager — автоматичне керування драйверами](#3-selenium-manager)

**Перші кроки**
- [4. Встановлення](#4-встановлення)
- [5. Перший скрипт — 8 базових компонентів](#5-перший-скрипт--8-базових-компонентів)
- [6. Браузери і headless режим](#6-браузери-і-headless-режим)

**Пошук і взаємодія**
- [7. Пошук елементів — By стратегії](#7-пошук-елементів--by-стратегії)
- [8. Взаємодія з елементами](#8-взаємодія-з-елементами)
- [9. Очікування — implicitly_wait і WebDriverWait](#9-очікування--implicitly_wait-і-webdriverwait)

**Selenium у тестах**
- [10. Selenium + unittest](#10-selenium--unittest)
- [11. Selenium + pytest](#11-selenium--pytest)
- [12. Django + Selenium — StaticLiveServerTestCase](#12-django--selenium--staticliveservertestcase)
- [13. Session Cookie Trick — логін без форми](#13-session-cookie-trick--логін-без-форми)
- [14. Remote WebDriver і Selenium Grid](#14-remote-webdriver-і-selenium-grid)

**Наш проєкт**
- [15. _make_headless_driver() — як це влаштовано у нас](#15-_make_headless_driver--як-це-влаштовано-у-нас)
- [16. Розбір test_selenium.py по класах](#16-розбір-test_seleniumpy-по-класах)

**Довідник**
- [17. Типові помилки та як їх читати](#17-типові-помилки-та-як-їх-читати)
- [18. Антипатерни](#18-антипатерни)
- [19. Питання для самоперевірки](#19-питання-для-самоперевірки)

---

## 1. Навіщо Selenium

### Проблема, яку він вирішує

Django Test Client перевіряє HTTP. Але між HTTP і тим, що бачить користувач, є ще один шар.

```
Django Test Client перевіряє:

  Python ──► Django middleware ──► view ──► HTTP response (bytes)
             ↑ тут все автоматизовано, без браузера


Selenium перевіряє:

  Python ──► chromedriver ──► Chrome ──► HTTP ──► Django server ──► HTML
                                 ↑
                              рендер HTML + CSS
                              виконання JavaScript
                              кліки, форми, навігація
                              все що бачить юзер у браузері
```

### Що Test Client не може перевірити

| Ситуація | Test Client | Selenium |
|----------|-------------|---------|
| `@login_required` захищає URL | ✓ | ✓ |
| Redirect після POST | ✓ | ✓ |
| Текст в HTML відповіді | ✓ | ✓ |
| JavaScript показує/ховає елемент | ✗ | ✓ |
| CSS ламає відображення форми | ✗ | ✓ |
| Кнопка реально клікається | ✗ | ✓ |
| Поле має правильний `placeholder` | ✗ | ✓ |
| Реальний redirect ланцюг у браузері | ✗ | ✓ |
| Форма не надсилається без обов'язкового поля | ✗ | ✓ |

### Коли Selenium потрібен, а коли зайвий

Selenium потрібен:
- Критичний user flow (login → create → see result)
- Форми з JavaScript-валідацією
- Single Page Application (React, Vue)
- Перевірка що CSS не ламає Layout

Selenium зайвий:
- Перевірка бізнес-логіки (це для unit тестів)
- Перевірка `status_code` і `redirect` (це для integration тестів)
- Все що можна перевірити без браузера

Правило: якщо тест можна написати через `self.client` — пиши через `self.client`. Selenium — тільки для того, що вимагає справжнього браузера.

---

## 2. Ментальна модель

### Три компоненти

```
твій Python код
      │
      │  selenium package (pip install selenium)
      │  відправляє команди через WebDriver Protocol (HTTP/JSON)
      ▼
chromedriver / geckodriver        ← драйвер: переводить WebDriver команди
      │                              у нативні команди браузера
      │
      ▼
Chrome / Firefox                  ← справжній браузер,
                                     відкриває сторінки, виконує JS
```

Твій Python код ніколи не "керує" браузером напряму. Він відправляє JSON команди до драйвера (по протоколу W3C WebDriver). Драйвер перекладає їх у нативний API браузера.

### WebDriver Protocol

Кожна команда — це HTTP запит до локального драйвера:

```
Python: driver.find_element(By.ID, "username")
            │
            ▼
POST http://localhost:9515/session/abc123/element
{"using": "id", "value": "username"}
            │
            ▼
chromedriver: CDP команда до Chrome → знайти елемент
            │
            ▼
Chrome: повертає element reference → id=XYZ
```

Саме тому Selenium повільніший за Test Client — кожна дія це реальний HTTP round-trip до драйвера.

---

## 3. Selenium Manager

У старих версіях Selenium (до 4.6) потрібно було вручну:
1. Завантажити `chromedriver.exe` / `geckodriver`
2. Покласти у PATH або вказати шлях у коді
3. Слідкувати за версіями — версія Chrome ≠ версія chromedriver → помилка

Починаючи з Selenium 4.6, є **Selenium Manager** — вбудований менеджер драйверів:

```python
# СТАРИЙ СПОСІБ (до Selenium 4.6):
from selenium.webdriver.chrome.service import Service
driver = webdriver.Chrome(service=Service('/usr/local/bin/chromedriver'))

# НОВИЙ СПОСІБ (Selenium 4.6+):
driver = webdriver.Chrome()   # Selenium Manager знайде і завантажить chromedriver сам
```

Selenium Manager:
1. Визначає встановлену версію Chrome
2. Знаходить відповідний chromedriver у кеші або завантажує
3. Запускає chromedriver автоматично

Для GitHub Actions це особливо зручно: `ubuntu-latest` включає Chrome, Selenium Manager завантажить відповідний chromedriver без додаткових кроків у workflow.

📖 [Selenium Manager документація](https://www.selenium.dev/documentation/selenium_manager/)

---

## 4. Встановлення

```bash
# Остання стабільна версія
pip install -U selenium

# Перевірити встановлену версію
python -c "import selenium; print(selenium.__version__)"
```

Підтримувані Python версії: **3.10+**

Підтримувані браузери: Chrome, Edge, Firefox, Safari, WebKitGTK, WPEWebKit

Після встановлення chromedriver не потрібно завантажувати окремо — Selenium Manager зробить це автоматично при першому запуску.

Для нашого проєкту selenium вже є у `requirements.txt`:

```
# requirements.txt
selenium>=4.16
```

---

## 5. Перший скрипт — 8 базових компонентів

Кожне Selenium взаємодія складається з 8 базових операцій. Ось вони всі разом:

```python
from selenium import webdriver
from selenium.webdriver.common.by import By

# 1. Старт сесії — відкрити браузер
driver = webdriver.Chrome()

# 2. Дія на браузер — відкрити URL
driver.get("https://www.selenium.dev/selenium/web/web-form.html")

# 3. Запит інформації про браузер
title = driver.title   # → "Web form"

# 4. Стратегія очікування
driver.implicitly_wait(0.5)   # чекати до 0.5 секунди на появу елементу

# 5. Пошук елементів
text_box     = driver.find_element(by=By.NAME,         value="my-text")
submit_button = driver.find_element(by=By.CSS_SELECTOR, value="button")

# 6. Взаємодія з елементами
text_box.send_keys("Selenium")
submit_button.click()

# 7. Запит інформації про елемент
message = driver.find_element(by=By.ID, value="message")
text = message.text   # → "Received!"

# 8. Завершення сесії — закрити браузер
driver.quit()
```

### Що відбувається на кожному кроці

| Крок | Метод | Що робить |
|------|-------|-----------|
| 1 | `webdriver.Chrome()` | Запускає Chrome і chromedriver, відкриває порожнє вікно |
| 2 | `driver.get(url)` | Навігація до URL, чекає поки сторінка завантажиться |
| 3 | `driver.title` | Повертає `<title>` поточної сторінки |
| 4 | `driver.implicitly_wait(n)` | Глобальне очікування для `find_element` (раз на сесію) |
| 5 | `driver.find_element(By.X, "val")` | Знаходить перший відповідний елемент у DOM |
| 6 | `.send_keys()` / `.click()` | Друкує текст / клікає |
| 7 | `.text` | Повертає видимий текст елементу |
| 8 | `driver.quit()` | Зупиняє driver процес, закриває браузер |

### Різниця між quit() і close()

```python
driver.close()  # Закриває поточну вкладку. Driver процес продовжує працювати.
driver.quit()   # Зупиняє driver процес і закриває всі вкладки. ЗАВЖДИ викликай в tearDown.
```

Якщо не викликати `driver.quit()` — chromedriver процес залишається у пам'яті. Після кількох тестів накопичується кілька zombie-процесів.

---

## 6. Браузери і headless режим

### Запуск різних браузерів

```python
from selenium import webdriver

driver = webdriver.Chrome()    # Chrome (найпопулярніший у CI)
driver = webdriver.Firefox()   # Firefox (geckodriver)
driver = webdriver.Edge()      # Microsoft Edge
driver = webdriver.Safari()    # Safari (тільки macOS)
```

### Headless режим — без GUI вікна

Headless = браузер виконує всі дії без графічного інтерфейсу. Потрібно для:
- CI/CD серверів (GitHub Actions, Jenkins) — там немає дисплею
- Швидкість — не витрачати ресурси на рендер пікселів
- Docker контейнери — зазвичай немає display server

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless=new')          # headless режим (Chrome 112+)
options.add_argument('--no-sandbox')            # потрібно в Docker / CI
options.add_argument('--disable-dev-shm-usage') # уникаємо проблем shared memory в Docker

driver = webdriver.Chrome(options=options)
# driver відкриває сторінки в пам'яті, без вікна на екрані
```

### Firefox headless

```python
from selenium.webdriver.firefox.options import Options

options = Options()
options.add_argument('--headless')

driver = webdriver.Firefox(options=options)
```

### Корисні options для Chrome

```python
options = Options()
options.add_argument('--window-size=1920,1080')     # розмір вікна
options.add_argument('--disable-extensions')         # вимкнути розширення
options.add_argument('--disable-gpu')               # потрібно у деяких середовищах
options.add_argument('--lang=uk')                   # мова браузера
options.add_experimental_option('prefs', {
    'profile.default_content_setting_values.notifications': 2  # вимкнути сповіщення
})
```

---

## 7. Пошук елементів — By стратегії

`find_element()` повертає перший знайдений елемент.
`find_elements()` повертає список усіх знайдених елементів (порожній список якщо нічого не знайдено).

### Усі стратегії By

```python
from selenium.webdriver.common.by import By

# За HTML атрибутом id="username"
elem = driver.find_element(By.ID, "username")

# За HTML атрибутом name="password"
elem = driver.find_element(By.NAME, "password")

# За CSS селектором
elem = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
elem = driver.find_element(By.CSS_SELECTOR, ".btn-primary")
elem = driver.find_element(By.CSS_SELECTOR, "#note-form button")

# За XPath
elem = driver.find_element(By.XPATH, "//button[@type='submit']")
elem = driver.find_element(By.XPATH, "//h1[contains(text(), 'Нотатки')]")

# За назвою HTML тегу
elems = driver.find_elements(By.TAG_NAME, "input")

# За CSS класом
elem = driver.find_element(By.CLASS_NAME, "btn")

# За текстом посилання <a>
elem = driver.find_element(By.LINK_TEXT, "Увійти")

# За частковим текстом посилання
elem = driver.find_element(By.PARTIAL_LINK_TEXT, "Вий")
```

### Яку стратегію обирати

| Стратегія | Коли обирати | Плюси | Мінуси |
|-----------|-------------|-------|--------|
| `By.ID` | Є унікальний id | Найшвидший, стабільний | id не завжди є |
| `By.NAME` | Форми — поля мають name | Зручно для input | Може бути не унікальний |
| `By.CSS_SELECTOR` | Гнучкий вибір | Читабельний, потужний | Потребує знання CSS |
| `By.XPATH` | Складна структура DOM | Найпотужніший | Ламкий при рефакторингу HTML |
| `By.CLASS_NAME` | CSS клас | Простий | Ненадійний (клас може повторюватись) |
| `By.TAG_NAME` | Всі елементи тегу | Для `find_elements` | Ненадійний як єдиний критерій |

Рекомендований порядок: `By.ID` → `By.NAME` → `By.CSS_SELECTOR` → `By.XPATH`.

### Пошук всередині елементу

```python
# find_element можна викликати не тільки на driver, а й на знайденому елементі
form = driver.find_element(By.TAG_NAME, 'form')
submit = form.find_element(By.CSS_SELECTOR, '[type="submit"]')
# Шукає submit тільки всередині form, не по всій сторінці
```

### NoSuchElementException

```python
from selenium.common.exceptions import NoSuchElementException

try:
    elem = driver.find_element(By.ID, "nonexistent")
except NoSuchElementException:
    print("Елемент не знайдений")
```

Якщо `find_element` не знаходить елемент — кидає `NoSuchElementException`, не повертає `None`.

---

## 8. Взаємодія з елементами

### Текстові поля

```python
field = driver.find_element(By.NAME, "title")

field.send_keys("Моя нотатка")          # ввести текст (додає до поточного)
field.clear()                           # очистити поле
field.clear()
field.send_keys("Нова нотатка")         # очистити і ввести нове
```

### Кліки

```python
button = driver.find_element(By.CSS_SELECTOR, '[type="submit"]')
button.click()

# Або знайти і клікнути одразу
driver.find_element(By.LINK_TEXT, "Додати нотатку").click()
```

### Отримання інформації про елемент

```python
elem = driver.find_element(By.ID, "message")

elem.text                           # видимий текст елементу
elem.get_attribute("href")          # значення HTML атрибуту
elem.get_attribute("class")         # CSS класи елементу
elem.get_attribute("value")         # value поля input
elem.is_displayed()                 # True якщо видимий (display: block)
elem.is_enabled()                   # True якщо не disabled
elem.is_selected()                  # True для checkbox/radio якщо вибраний
```

### Спеціальні клавіші

```python
from selenium.webdriver.common.keys import Keys

field.send_keys(Keys.RETURN)        # Enter
field.send_keys(Keys.TAB)          # Tab
field.send_keys(Keys.ESCAPE)       # Escape
field.send_keys(Keys.BACKSPACE)    # Backspace
field.send_keys(Keys.CONTROL, 'a') # Ctrl+A (виділити все)
field.send_keys(Keys.CONTROL, 'c') # Ctrl+C (скопіювати)
```

### Dropdown (Select)

```python
from selenium.webdriver.support.ui import Select

select = Select(driver.find_element(By.NAME, "priority"))
select.select_by_value("2")            # за value атрибутом
select.select_by_visible_text("High")  # за видимим текстом
select.select_by_index(0)             # за порядковим номером

# Отримати вибраний option
current = select.first_selected_option.text
```

### Інформація про браузер і сторінку

```python
driver.title             # <title> поточної сторінки
driver.current_url       # поточний URL
driver.page_source       # повний HTML сторінки (рядок)
driver.get_cookies()     # список cookies
driver.get_cookie('sessionid')  # конкретний cookie

# Виконати JavaScript
driver.execute_script("return document.title")
driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
```

---

## 9. Очікування — implicitly_wait і WebDriverWait

### Проблема без очікувань

```python
driver.get("http://localhost:8000/notes/new/")
driver.find_element(By.NAME, 'title')  # ← МОЖЕ ВПАСТИ!
# Якщо сторінка ще не завантажилась повністю — елементу нема в DOM
```

Браузер асинхронний. `driver.get()` повертається коли отримав відповідь, але DOM може ще не бути повністю побудованим.

### implicitly_wait — глобальне очікування

```python
driver.implicitly_wait(5)
# Тепер кожен find_element чекає до 5 секунд перш ніж кинути NoSuchElementException
```

Встановлюється один раз на сесію (зазвичай у `setUpClass`). При кожному `find_element`:
- Якщо елемент є — повертає одразу
- Якщо немає — чекає, перевіряє знову, до таймауту
- Якщо за 5 секунд так і не знайшов — `NoSuchElementException`

```python
# Наш проєкт: test_selenium.py
@classmethod
def setUpClass(cls):
    super().setUpClass()
    cls.driver = _make_headless_driver()
    cls.driver.implicitly_wait(5)   # ← встановлюємо один раз для всього класу
```

### WebDriverWait — явне очікування конкретної умови

`implicitly_wait` чекає тільки появи елементу. Але іноді потрібно чекати іншої умови: зміни URL, тексту, видимості.

```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

wait = WebDriverWait(driver, timeout=5)

# Чекати поки URL зміниться
wait.until(EC.url_changes("http://localhost:8000/accounts/login/"))

# Чекати поки елемент стане клікабельним
wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[type="submit"]')))

# Чекати поки елемент стане видимим
wait.until(EC.visibility_of_element_located((By.ID, "message")))

# Чекати поки текст з'явиться в елементі
wait.until(EC.text_to_be_present_in_element((By.ID, "status"), "Saved"))

# Чекати поки елемент зникне
wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "loading")))
```

### Поширені expected_conditions

| Умова | Що перевіряє |
|-------|-------------|
| `url_changes(url)` | Поточний URL відрізняється від заданого |
| `url_contains("path")` | URL містить підрядок |
| `title_contains("text")` | `<title>` містить текст |
| `element_to_be_clickable(locator)` | Елемент є і клікабельний |
| `visibility_of_element_located(locator)` | Елемент є і видимий |
| `invisibility_of_element_located(locator)` | Елемент невидимий або відсутній |
| `text_to_be_present_in_element(locator, text)` | Текст є у елементі |
| `staleness_of(element)` | Старий елемент зник з DOM (після перезавантаження) |

### Коли що обирати

```
implicitly_wait(n):
  + Простий, встановлюється раз
  + Автоматично для всіх find_element
  - Чекає тільки появи елементу в DOM
  - Не перевіряє видимість або клікабельність

WebDriverWait + EC:
  + Гнучкий — будь-яка умова
  + Можна задати різний таймаут для різних ситуацій
  - Більше коду
```

В нашому проєкті: `implicitly_wait(5)` для загального пошуку, `WebDriverWait(driver, 5).until(EC.url_changes(...))` після кліку Submit (бо треба чекати redirect, а не появи елементу).

---

## 10. Selenium + unittest

Класичний спосіб — через `unittest.TestCase`:

```python
import unittest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class SeleniumTestCase(unittest.TestCase):

    def setUp(self):
        """Запускається перед кожним тестом — відкриває новий браузер."""
        options = Options()
        options.add_argument('--headless=new')
        self.driver = webdriver.Chrome(options=options)
        self.addCleanup(self.driver.quit)  # ← quit() навіть якщо тест впав

    def test_page_title(self):
        self.driver.get("https://selenium.dev")
        self.assertIn("Selenium", self.driver.title)

    def test_find_element(self):
        self.driver.get("https://www.selenium.dev/selenium/web/web-form.html")
        field = self.driver.find_element(By.NAME, "my-text")
        self.assertIsNotNone(field)
```

`self.addCleanup(self.driver.quit)` — гарантує що `quit()` викличеться навіть якщо тест кидає виняток. Це краще ніж `tearDown` бо `tearDown` не викликається при виключеннях у `setUp`.

### setUpClass — один driver на всі тести класу (швидше)

```python
class SeleniumTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Запускається раз перед усіма тестами класу."""
        super().setUpClass()
        options = Options()
        options.add_argument('--headless=new')
        cls.driver = webdriver.Chrome(options=options)
        cls.driver.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        """Запускається раз після всіх тестів класу."""
        cls.driver.quit()
        super().tearDownClass()

    def test_page_one(self):
        self.driver.get("https://selenium.dev")
        # ...

    def test_page_two(self):
        self.driver.get("https://selenium.dev/documentation")
        # ...
```

**Важливо:** при `setUpClass` всі тести класу ділять один driver. Якщо тест залишає браузер у незрозумілому стані (cookies, open dialogs) — наступний тест може впасти. В нашому проєкті ми обходимо це через session cookie trick (заходимо кожного разу через `setUp`).

---

## 11. Selenium + pytest

```python
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


@pytest.fixture
def driver():
    """Fixture — відкриває driver перед тестом, закриває після."""
    options = Options()
    options.add_argument('--headless=new')
    d = webdriver.Chrome(options=options)
    d.implicitly_wait(5)
    yield d        # ← тест виконується тут
    d.quit()       # ← завжди викликається після тесту (навіть при помилці)


def test_page_title(driver):
    driver.get("https://selenium.dev")
    assert "Selenium" in driver.title


def test_form(driver):
    from selenium.webdriver.common.by import By
    driver.get("https://www.selenium.dev/selenium/web/web-form.html")
    driver.find_element(By.NAME, "my-text").send_keys("pytest test")
    driver.find_element(By.CSS_SELECTOR, "button").click()
    message = driver.find_element(By.ID, "message")
    assert message.text == "Received!"
```

### scope="session" — один driver на всі тести

```python
@pytest.fixture(scope="session")
def driver():
    """Один driver на всю тестову сесію pytest."""
    options = Options()
    options.add_argument('--headless=new')
    d = webdriver.Chrome(options=options)
    yield d
    d.quit()
```

`scope="session"` запускає fixture один раз. Швидше, але тести ділять стан браузера.

Для Django краще використовувати `django.test.TestCase` + `StaticLiveServerTestCase`, а не pytest fixtures — вони інтегруються з тестовою БД Django.

---

## 12. Django + Selenium — StaticLiveServerTestCase

### Проблема звичайного TestCase

Selenium відкриває реальний браузер, який робить HTTP запити. Звичайний Django `TestCase` не запускає HTTP сервер — він симулює запити всередині процесу. Selenium не може підключитись.

### StaticLiveServerTestCase — реальний HTTP сервер

```python
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
```

`StaticLiveServerTestCase`:
1. Запускає реальний Django HTTP сервер у окремому потоці
2. Сервер запускається на випадковому порту: `http://127.0.0.1:XXXXX`
3. `self.live_server_url` містить цю адресу
4. Кожен тест має ізольовану тестову БД (з rollback — як у `TestCase`)
5. Додатково: serve static files (CSS, JS) — тому "Static" у назві

```python
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.common.by import By


class MyDjangoSeleniumTest(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Запустити headless Chrome один раз для всіх тестів класу
        options = ChromeOptions()
        options.add_argument('--headless=new')
        cls.driver = webdriver.Chrome(options=options)
        cls.driver.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        # Створити тестового юзера в тестовій БД
        self.user = User.objects.create_user('alice', password='pass')

    def test_login_flow(self):
        # self.live_server_url → "http://127.0.0.1:38471" (випадковий порт)
        self.driver.get(f'{self.live_server_url}/accounts/login/')
        self.driver.find_element(By.NAME, 'username').send_keys('alice')
        self.driver.find_element(By.NAME, 'password').send_keys('pass')
        self.driver.find_element(By.CSS_SELECTOR, '[type="submit"]').click()
        self.assertIn('/notes/', self.driver.current_url)
```

### LiveServerTestCase vs StaticLiveServerTestCase

```python
from django.test import LiveServerTestCase              # не serve static files
from django.contrib.staticfiles.testing import StaticLiveServerTestCase  # ← використовуй це
```

Для більшості тестів потрібен `StaticLiveServerTestCase` — бо якщо Bootstrap CSS не завантажується, деякі елементи можуть бути hidden і Selenium їх не клікає.

---

## 13. Session Cookie Trick — логін без форми

### Проблема з логіном через форму в E2E тестах

Найочевидніший спосіб авторизуватись у Selenium тесті:

```python
# НЕСТАБІЛЬНИЙ СПОСІБ — через форму
def login_via_form(driver, url, username, password):
    driver.get(f'{url}/accounts/login/')
    driver.find_element(By.NAME, 'username').send_keys(username)
    driver.find_element(By.NAME, 'password').send_keys(password)
    driver.find_element(By.CSS_SELECTOR, '[type="submit"]').click()
```

**Проблеми:**
- Якщо форма має CSRF перевірку з JavaScript — тест може залежнути від порядку завантаження
- Якщо layout форми зміниться (перейменування CSS класів) — тест впаде з причин, не пов'язаних з логікою
- Якщо додати recaptcha — тест повністю зламається
- Повільно: кожен тест робить повний round-trip через форму

### Рішення: session cookie

```python
def _login_via_cookie(self):
    """
    Стандартна техніка E2E логіну через session cookie:
    1. Django Test Client входить у систему (без браузера, миттєво)
    2. Отримуємо session cookie
    3. Передаємо cookie до Selenium driver
    4. Driver авторизований — без заповнення форми
    """
    # Крок 1: Test Client логіниться
    self.client.force_login(self.user)

    # Крок 2: Отримати session cookie
    session_cookie = self.client.cookies['sessionid']

    # Крок 3: Відкрити будь-яку сторінку того ж домену
    # (браузер не дозволяє встановлювати cookies без активного домену)
    self.driver.get(f'{self.live_server_url}/')

    # Крок 4: Додати cookie до driver
    self.driver.add_cookie({
        'name':  'sessionid',
        'value': session_cookie.value,
        'path':  '/',
    })

    # Тепер driver авторизований. Наступний get() піде вже як залогінений юзер.
```

### Чому `force_login` а не `login`

```python
# force_login — встановлює session без аутентифікації (тільки для тестів)
self.client.force_login(self.user)   # ← швидко, без перевірки пароля

# login — повна аутентифікація з перевіркою пароля
self.client.login(username='alice', password='pass')  # ← повільніше, для тестів логіну
```

У session cookie trick ми тестуємо не логін — ми тестуємо функціональність після логіну. Тому `force_login` правильний вибір.

### Повний патерн з session cookie в тесті

```python
class SeleniumNoteFlowTest(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.driver = _make_headless_driver()
        cls.driver.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        # Тестова БД чиста (rollback між тестами)
        self.user = User.objects.create_user('alice', password='pass')
        self._login_via_cookie()   # ← логін через cookie перед КОЖНИМ тестом

    def _login_via_cookie(self):
        self.client.force_login(self.user)
        session_cookie = self.client.cookies['sessionid']
        self.driver.get(f'{self.live_server_url}/')
        self.driver.add_cookie({'name': 'sessionid', 'value': session_cookie.value, 'path': '/'})

    def test_create_note(self):
        # Тут driver вже авторизований як alice
        self.driver.get(f'{self.live_server_url}/notes/new/')
        self.driver.find_element(By.NAME, 'title').send_keys('My Note')
        self.driver.find_element(By.CSS_SELECTOR, '[type="submit"]').click()
        # ...
```

---

## 14. Remote WebDriver і Selenium Grid

### Коли потрібен Remote WebDriver

Local WebDriver: Driver і браузер на тій самій машині.

Remote WebDriver: Driver на одній машині, браузер — на іншій (у Docker, у хмарі).

Використання:
- Selenium Grid — запускати тести паралельно на кількох браузерах
- Docker — запускати Chrome у контейнері
- BrowserStack, Sauce Labs — хмарне тестування на реальних пристроях

### Selenium Grid + Docker

```bash
# Запустити Selenium standalone-chrome у Docker
docker run -d -p 4444:4444 selenium/standalone-chrome:latest
```

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
driver = webdriver.Remote(
    command_executor="http://localhost:4444/wd/hub",  # адреса Grid
    options=options,
)
driver.get("https://selenium.dev")
```

### Наш `_make_headless_driver()` — динамічний вибір

У `test_selenium.py` є змінна середовища `SELENIUM_REMOTE_URL`. Якщо вона є — Remote WebDriver, якщо ні — локальний Chrome:

```python
SELENIUM_REMOTE_URL = os.environ.get("SELENIUM_REMOTE_URL")

def _make_headless_driver():
    options = ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    if SELENIUM_REMOTE_URL:
        # CI з окремим Selenium контейнером
        return webdriver.Remote(
            command_executor=SELENIUM_REMOTE_URL,
            options=options,
        )

    # Локально або GitHub Actions без контейнера
    options.add_argument('--headless=new')
    return webdriver.Chrome(options=options)
```

Це дозволяє запускати ОДИН файл тестів в обох середовищах.

📖 [Remote WebDriver документація](https://selenium.dev/documentation/webdriver/drivers/remote_webdriver/)

---

## 15. _make_headless_driver() — як це влаштовано у нас

Подивімось на повний `_make_headless_driver()` з нашого проєкту і розберемо кожен аргумент:

```python
def _make_headless_driver():
    options = ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    if SELENIUM_REMOTE_URL:
        return webdriver.Remote(
            command_executor=SELENIUM_REMOTE_URL,
            options=options,
        )

    options.add_argument('--headless=new')
    return webdriver.Chrome(options=options)
```

| Аргумент | Пояснення |
|----------|-----------|
| `--no-sandbox` | Chrome sandbox ізолює процеси. У Docker і GitHub Actions runner це конфліктує з namespace ізоляцією контейнера. Вимикаємо. |
| `--disable-dev-shm-usage` | Chrome за замовчуванням пише у `/dev/shm` (shared memory). У Docker це обмежено 64MB → Chrome crashне. Цей флаг заставляє Chrome писати у `/tmp`. |
| `--headless=new` | Новий headless режим (Chrome 112+). Старий `--headless` залишений для сумісності. |

### Чому GitHub Actions не використовує service container

У зразку `crispy_notes_project/.github/.../django-tests.yml` є `services: selenium: image: selenium/standalone-chrome`. Але реальний workflow у `.github/workflows/django-tests.yml` його не використовує.

```
Проблема:
  Selenium container відкриває http://localhost:PORT
  ALE його localhost ≠ localhost runner-а
  → Chrome у контейнері не може підключитись до Django server на runner

Рішення:
  Chrome і Django server на одній машині (runner)
  → localhost є спільним
  → все працює
```

Тому в реальному workflow Selenium тести запускаються без service container — Chrome вже є на `ubuntu-latest`, а Selenium Manager завантажує відповідний chromedriver.

---

## 16. Розбір test_selenium.py по класах

### Клас SeleniumLoginFlowTest

```
Тестує:  Login flow через реальний браузер
Метод:   Заповнення форми (не session cookie)
Тести:
  test_login_page_renders         — форма є в DOM
  test_valid_login_redirects_to_notes — правильний пароль → redirect
  test_invalid_login_shows_error  — неправильний пароль → залишаємось на login
```

Ключовий момент: `test_valid_login_redirects_to_notes` використовує `WebDriverWait(driver, 5).until(EC.url_changes(login_url))` — чекає поки Chrome завершить redirect після POST.

```python
def test_valid_login_redirects_to_notes(self):
    login_url = f'{self.live_server_url}/accounts/login/'
    self.driver.get(login_url)

    self.driver.find_element(By.NAME, 'username').send_keys('seleniumuser')
    self.driver.find_element(By.NAME, 'password').send_keys('testpass123')
    self.driver.find_element(By.CSS_SELECTOR, '[type="submit"]').click()

    # Без цього wait: current_url перевіряється до redirect
    WebDriverWait(self.driver, 5).until(EC.url_changes(login_url))

    self.assertIn('/notes/', self.driver.current_url)
```

---

### Клас SeleniumNoteFlowTest

```
Тестує:  Note workflow: перегляд і створення
Метод:   Session cookie trick для логіну
Тести:
  test_note_list_page_loads   — сторінка /notes/ завантажилась
  test_create_note_via_form   — форма створення нотатки відпрацьовує
  test_created_note_appears_in_list — нотатка видна у списку
```

`test_created_note_appears_in_list` не заповнює форму — він створює нотатку через ORM і перевіряє що `page_source` містить її заголовок:

```python
def test_created_note_appears_in_list(self):
    Note.objects.create(user=self.user, title='Visible Note', content='Test')
    self.driver.get(f'{self.live_server_url}/notes/')
    self.assertIn('Visible Note', self.driver.page_source)
```

Це перевіряє не бізнес-логіку (яка перевірена у unit тестах), а що **шаблон правильно рендерить дані** — `{% for note in notes %}` відображає `note.title`.

---

## 17. Типові помилки та як їх читати

### NoSuchElementException — елемент не знайдений

```
selenium.common.exceptions.NoSuchElementException:
Message: no such element: Unable to locate element: {"method":"css selector","selector":"[type='submit']"}

Причини:
  1. Елементу ще немає в DOM (сторінка не завантажилась)
     → Збільш implicitly_wait або додай WebDriverWait
  2. Неправильний селектор
     → Відкрий браузер DevTools (F12), перевір селектор у консолі: document.querySelector('[type="submit"]')
  3. Елемент у іншому iframe
     → driver.switch_to.frame("frame_name") перед find_element
```

### StaleElementReferenceException — застарілий елемент

```
selenium.common.exceptions.StaleElementReferenceException:
Message: stale element reference: stale element not found in the current frame

Причина:
  Ти знайшов елемент, потім сторінка оновилась (або JS перебудував DOM),
  і той самий element reference більше недійсний.

Рішення:
  # НЕПРАВИЛЬНО:
  button = driver.find_element(By.ID, "submit")
  do_something_that_reloads_page()
  button.click()   # ← StaleElementReferenceException!

  # ПРАВИЛЬНО:
  do_something_that_reloads_page()
  driver.find_element(By.ID, "submit").click()  # ← знаходимо знову
```

### TimeoutException — WebDriverWait вичерпав час

```
selenium.common.exceptions.TimeoutException

Причина:
  WebDriverWait(driver, 5).until(EC.url_changes(...)) не дочекався за 5 секунд.

Дії:
  1. Збільш timeout: WebDriverWait(driver, 10)
  2. Перевір що умова взагалі може спрацювати
  3. Додай screenshot для діагностики:
     driver.save_screenshot('/tmp/debug.png')
     # Подивись що відображається в момент timeout
```

### ElementNotInteractableException — не можна взаємодіяти

```
selenium.common.exceptions.ElementNotInteractableException:
Message: element not interactable

Причина:
  Елемент є в DOM, але hidden (display:none) або перекритий іншим елементом.

Рішення:
  # Перевірити видимість
  if elem.is_displayed():
      elem.click()
  else:
      # Прокрутити до елементу
      driver.execute_script("arguments[0].scrollIntoView(true);", elem)
      elem.click()
```

### WebDriverException — driver не запустився

```
selenium.common.exceptions.WebDriverException:
Message: 'chromedriver' executable needs to be in PATH

Причина (стара версія Selenium < 4.6):
  chromedriver не в PATH і не знайдений Selenium Manager.

Для нових версій (4.6+):
  Selenium Manager має автоматично завантажити chromedriver.
  Якщо не вийшло: перевір що Chrome встановлений у системі.
  chrome --version  (або google-chrome --version)
```

---

## 18. Антипатерни

### Антипатерн 1: time.sleep замість wait

```python
# ПОГАНО — нестабільно і повільно
driver.find_element(By.ID, "submit").click()
time.sleep(3)   # чекати 3 секунди "щоб точно завантажилось"
assert "Success" in driver.page_source

# ДОБРЕ — чекати конкретної умови
driver.find_element(By.ID, "submit").click()
WebDriverWait(driver, 5).until(
    EC.text_to_be_present_in_element((By.ID, "message"), "Success")
)
assert "Success" in driver.page_source
```

`time.sleep(3)` завжди чекає 3 секунди навіть якщо сторінка завантажилась за 0.1s. `WebDriverWait` чекає максимум 5 секунд і повертається як тільки умова виконана.

### Антипатерн 2: Selenium для того що Test Client робить краще

```python
# ПОГАНО — Selenium для перевірки HTTP статусу
def test_unauthenticated_redirect(self):
    self.driver.get(f'{self.live_server_url}/notes/')
    self.assertIn('/accounts/login/', self.driver.current_url)

# ДОБРЕ — для цього є integration тест
def test_unauthenticated_redirect(self):
    response = self.client.get('/notes/')
    self.assertEqual(response.status_code, 302)
    self.assertIn('/accounts/login/', response['Location'])
```

Перевірка `@login_required` — це integration тест. Selenium потрібен тільки якщо треба перевірити що redirect відбувається у реальному браузері з навігацією.

### Антипатерн 3: відкривати новий driver у кожному тесті

```python
# ПОГАНО — 100 тестів × 3 секунди запуску Chrome = 5 хвилин зайвого часу
class BadTest(TestCase):
    def setUp(self):
        self.driver = webdriver.Chrome()   # кожен тест запускає новий Chrome

    def tearDown(self):
        self.driver.quit()

# ДОБРЕ — один driver на клас
class GoodTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = webdriver.Chrome()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
```

### Антипатерн 4: ламкі XPath

```python
# ПОГАНО — ламається при будь-якій зміні структури HTML
elem = driver.find_element(By.XPATH, "/html/body/div[2]/main/div[1]/form/div[3]/button")

# ДОБРЕ — стабільний CSS або data атрибут
elem = driver.find_element(By.CSS_SELECTOR, '[type="submit"]')
# або додати data-testid до HTML:
# <button data-testid="submit-note" type="submit">
elem = driver.find_element(By.CSS_SELECTOR, '[data-testid="submit-note"]')
```

### Антипатерн 5: Selenium тести для кожної дрібниці

```
Unit test: 0.01s  × 100 = 1 секунда
Selenium:  10s    × 100 = 16 хвилин

+ Selenium тести крихкі (зміна CSS ламає тест)
+ Потребують browserdriver, версій, конфігурації

Правило: Selenium тільки для критичних user flows.
         Все що можна перевірити через Test Client — перевіряй через Test Client.
```

---

## 19. Питання для самоперевірки

1. Чим Selenium відрізняється від Django Test Client? Що кожен з них перевіряє?
2. Що таке WebDriver Protocol і чому Selenium повільніший за Test Client?
3. Яку проблему вирішує Selenium Manager і з якої версії він з'явився?
4. Яка різниця між `driver.close()` і `driver.quit()`?
5. Яку стратегію пошуку обрати якщо у елементу є `id`? Якщо тільки CSS клас?
6. Чим `implicitly_wait` відрізняється від `WebDriverWait`? Коли що використовувати?
7. Чому після `submit_button.click()` потрібно `WebDriverWait(...).until(EC.url_changes(...))`?
8. Що таке `StaticLiveServerTestCase` і чому він потрібен для Selenium тестів Django?
9. Поясни session cookie trick: які 4 кроки виконуємо і навіщо це краще ніж заповнення форми логіну?
10. Чому в `setUpClass` один `driver` для всього класу, але в `setUp` кожен раз викликаємо `_login_via_cookie()`?
11. Що таке `StaleElementReferenceException` і як його уникнути?
12. Коли Remote WebDriver потрібний, а коли можна обійтись локальним?
13. Чому реальний workflow не використовує `selenium/standalone-chrome` як service container?
14. Навіщо `--no-sandbox` і `--disable-dev-shm-usage` у GitHub Actions / Docker?
15. В яких випадках краще написати integration тест, а не Selenium?

---

## Посилання

| Ресурс | Посилання |
|--------|-----------|
| Selenium Python Docs | https://selenium.dev/selenium/docs/api/py |
| Selenium Python API Reference | https://selenium.dev/selenium/docs/api/py/api.html |
| Selenium GitHub | https://github.com/SeleniumHQ/Selenium |
| PyPI: selenium | https://pypi.org/project/selenium |
| Selenium Manager | https://www.selenium.dev/documentation/selenium_manager/ |
| Write your first Selenium script | https://selenium.dev/documentation/webdriver/getting_started/first_script/ |
| WebDriver — all browsers | https://selenium.dev/documentation/webdriver/browsers/ |
| Locator strategies | https://selenium.dev/documentation/webdriver/elements/locators/ |
| Interacting with elements | https://selenium.dev/documentation/webdriver/elements/interactions/ |
| Waiting strategies | https://selenium.dev/documentation/webdriver/waits/ |
| Expected conditions | https://selenium.dev/selenium/docs/api/py/webdriver_support/selenium.webdriver.support.expected_conditions.html |
| Remote WebDriver | https://selenium.dev/documentation/webdriver/drivers/remote_webdriver/ |
| Selenium Grid | https://selenium.dev/documentation/grid/ |
| Django StaticLiveServerTestCase | https://docs.djangoproject.com/en/5.2/topics/testing/tools/#django.test.LiveServerTestCase |
| chromedriver | https://developer.chrome.com/docs/chromedriver |
| geckodriver (Firefox) | https://github.com/mozilla/geckodriver |
