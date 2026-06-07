"""
test_selenium.py — E2E тести через реальний браузер (Selenium)

РІВЕНЬ ТЕСТУВАННЯ:
  Unit       → функція Python, без HTTP
  Integration → Django Test Client, симульований HTTP
  E2E (цей файл) → реальний браузер Firefox/Chrome, справжній HTTP

ЧИМ ВІДРІЗНЯЄТЬСЯ ВІД INTEGRATION ТЕСТІВ (test_views.py):
  Integration: self.client.get('/notes/') → Django обробляє всередині процесу
  Selenium:    driver.get('http://127.0.0.1:PORT/notes/') → реальний браузер,
               реальний HTTP запит, рендер HTML, JavaScript виконується

ЩО ТЕСТУЄ SELENIUM ДОДАТКОВО:
  - HTML форми заповнюються реальними keystroke
  - Кнопки клікаються через DOM
  - JavaScript (якщо є) виконується
  - CSS rendering не ламає форми
  - URL навігація через браузер (redirect ланцюги видимі)

КОЛИ НЕ ЗАПУСКАТИ SELENIUM:
  - Якщо geckodriver / chromedriver не встановлені → тести будуть SKIPPED
  - Для CI/CD без дисплею → використовувати headless mode (увімкнений за замовчуванням)

ЯК ЗАПУСТИТИ:
  # 1. Встановити selenium (Selenium Manager автоматично завантажить chromedriver):
  pip install selenium

  # 2. Запустити — chromedriver завантажиться автоматично:
  python manage.py test hello_app.tests.test_selenium -v 2

  # Якщо selenium не встановлений — тести будуть skipped (s), не впадуть.

ТРЮК: SESSION COOKIE
  Замість того щоб заповнювати login форму в браузері,
  ми копіюємо session cookie з Django Test Client до Selenium driver.
  Це швидше і надійніше — тест не залежить від стану login форми.
"""

import os
import unittest

# Selenium може не бути встановленим — graceful fallback
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from hello_app.models import Note

# Якщо встановлена ця змінна → запускаємо через Remote WebDriver (GitHub Actions / Docker)
# Якщо не встановлена → локальний headless Chrome
SELENIUM_REMOTE_URL = os.environ.get("SELENIUM_REMOTE_URL")


def _make_headless_driver():
    """
    Повертає WebDriver залежно від середовища:

    - Локально (SELENIUM_REMOTE_URL не встановлена):
        headless Chrome через Selenium Manager (автоматично завантажує chromedriver)

    - GitHub Actions / Docker (SELENIUM_REMOTE_URL встановлена):
        Remote WebDriver → selenium/standalone-chrome контейнер

    Це дозволяє використовувати ОДИН файл тестів в обох середовищах.
    """
    options = ChromeOptions()
    options.add_argument('--no-sandbox')            # потрібно в Docker / CI
    options.add_argument('--disable-dev-shm-usage') # уникаємо проблем shared memory

    if SELENIUM_REMOTE_URL:
        # GitHub Actions: selenium/standalone-chrome вже запущений як сервіс
        return webdriver.Remote(
            command_executor=SELENIUM_REMOTE_URL,
            options=options,
        )

    # Локально: headless Chrome (Selenium Manager завантажить chromedriver)
    options.add_argument('--headless=new')
    return webdriver.Chrome(options=options)


# ─────────────────────────────────────────────────────────────────────────────
# 1. LOGIN FLOW — форма входу через браузер
# ─────────────────────────────────────────────────────────────────────────────

@unittest.skipUnless(SELENIUM_AVAILABLE, "selenium not installed — pip install selenium")
class SeleniumLoginFlowTest(StaticLiveServerTestCase):
    """
    Тестуємо login flow через реальний браузер.

    StaticLiveServerTestCase:
      - Запускає реальний Django HTTP сервер на тимчасовому порту
      - self.live_server_url → 'http://127.0.0.1:XXXXX'
      - Кожен тест має ізольовану тестову БД (rollback як у звичайному TestCase)

    implicitly_wait(5):
      Selenium чекає до 5 секунд на появу елементу в DOM.
      Потрібно бо сторінки завантажуються з мережевою затримкою.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if SELENIUM_AVAILABLE:
            cls.driver = _make_headless_driver()
            cls.driver.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        if SELENIUM_AVAILABLE:
            cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        # Кожен тест отримує свіжого юзера (тестова БД з rollback)
        self.user = User.objects.create_user(
            username='seleniumuser', password='testpass123'
        )

    def test_login_page_renders(self):
        """
        Відкриваємо /accounts/login/ → сторінка завантажилась,
        форма присутня в DOM.

        find_element(By.TAG_NAME, 'form') кидає NoSuchElementException якщо нема.
        """
        self.driver.get(f'{self.live_server_url}/accounts/login/')
        form = self.driver.find_element(By.TAG_NAME, 'form')
        self.assertIsNotNone(form)

    def test_valid_login_redirects_to_notes(self):
        """
        Заповнюємо форму логіну валідними даними, клікаємо Submit.
        Очікуємо redirect на /notes/ (LOGIN_REDIRECT_URL = '/notes/').

        WebDriverWait: click() запускає навігацію асинхронно.
        Без wait — current_url перевіряється до того як Chrome завершив redirect.
        """
        login_url = f'{self.live_server_url}/accounts/login/'
        self.driver.get(login_url)

        self.driver.find_element(By.NAME, 'username').send_keys('seleniumuser')
        self.driver.find_element(By.NAME, 'password').send_keys('testpass123')
        self.driver.find_element(By.CSS_SELECTOR, '[type="submit"]').click()

        # Чекаємо поки URL зміниться — redirect може зайняти частку секунди
        WebDriverWait(self.driver, 5).until(
            EC.url_changes(login_url)
        )

        self.assertIn('/notes/', self.driver.current_url)

    def test_invalid_login_shows_error(self):
        """
        Неправильний пароль → залишаємось на login сторінці (немає redirect).

        current_url не змінюється + форма видима.
        """
        self.driver.get(f'{self.live_server_url}/accounts/login/')

        self.driver.find_element(By.NAME, 'username').send_keys('seleniumuser')
        self.driver.find_element(By.NAME, 'password').send_keys('wrongpassword')
        self.driver.find_element(By.CSS_SELECTOR, '[type="submit"]').click()

        # Залишаємось на сторінці логіну — redirect не відбувся
        self.assertIn('login', self.driver.current_url)


# ─────────────────────────────────────────────────────────────────────────────
# 2. NOTE WORKFLOW — створення нотатки через браузер
# ─────────────────────────────────────────────────────────────────────────────

@unittest.skipUnless(SELENIUM_AVAILABLE, "selenium not installed — pip install selenium")
class SeleniumNoteFlowTest(StaticLiveServerTestCase):
    """
    Тестуємо user workflow: перегляд списку нотаток і створення нотатки.

    SESSION COOKIE TRICK:
      Замість заповнення форми логіну в браузері, ми:
      1. Логінимось через Django Test Client (швидко, без браузера)
      2. Копіюємо session cookie до Selenium WebDriver
      3. Selenium тепер авторизований без повторного логіну

      Це стандартна техніка для E2E тестів — швидше і надійніше.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if SELENIUM_AVAILABLE:
            cls.driver = _make_headless_driver()
            cls.driver.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        if SELENIUM_AVAILABLE:
            cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(
            username='noteuser', password='testpass123'
        )
        self._login_via_cookie()

    def _login_via_cookie(self):
        """
        SESSION COOKIE TRICK:
        1. Test Client логіниться → Django видає session_id cookie
        2. Ми копіюємо цей cookie до Selenium driver
        3. Selenium тепер авторизований

        Навіщо: уникаємо залежності E2E тесту від стану login форми.
        Логін форма може мати CSRF, рекапчу, JS валідацію — все це ламає тести.
        """
        # 1. Залогінитись через Test Client
        self.client.force_login(self.user)

        # 2. Отримати session cookie
        session_cookie = self.client.cookies['sessionid']

        # 3. Спочатку відкрити будь-яку сторінку того самого домену
        #    (browser потребує сторінку відкритою щоб встановити cookie)
        self.driver.get(f'{self.live_server_url}/')

        # 4. Передати session cookie до Selenium
        self.driver.add_cookie({
            'name':   'sessionid',
            'value':  session_cookie.value,
            'path':   '/',
        })

    def test_note_list_page_loads(self):
        """
        Авторизований юзер відкриває /notes/ → сторінка завантажилась (200).
        Заголовок або heading містить відповідний текст.
        """
        self.driver.get(f'{self.live_server_url}/notes/')
        # Сторінка завантажилась — немає redirect на login
        self.assertIn('/notes/', self.driver.current_url)

    def test_create_note_via_form(self):
        """
        E2E тест: відкрити /notes/new/, заповнити форму, натиснути Submit.
        Результат: redirect на note_detail або note_list.

        Використовуємо submit_button.click() замість Keys.RETURN:
        Keys.RETURN може не спрацювати якщо форма має JavaScript-валідацію.

        WebDriverWait: redirect відбувається асинхронно після POST.
        """
        new_note_url = f'{self.live_server_url}/notes/new/'
        self.driver.get(new_note_url)

        self.driver.find_element(By.NAME, 'title').send_keys('My Selenium Note')

        # Знаходимо і клікаємо submit button (кнопка типу submit у формі)
        self.driver.find_element(By.CSS_SELECTOR, '[type="submit"]').click()

        # Чекаємо поки URL зміниться — POST → redirect займає час
        WebDriverWait(self.driver, 5).until(
            EC.url_changes(new_note_url)
        )

        self.assertNotIn('/notes/new/', self.driver.current_url)

    def test_created_note_appears_in_list(self):
        """
        Створюємо нотатку через ORM (не через форму) і перевіряємо
        що вона видна в DOM списку нотаток.

        Навіщо: перевіряємо що шаблон правильно рендерить дані з БД.
        Якщо template bug (наприклад {% for %} без note.title) → цей тест впаде.
        """
        Note.objects.create(user=self.user, title='Visible Note', content='Test')

        self.driver.get(f'{self.live_server_url}/notes/')

        # Перевіряємо що текст нотатки видний у HTML сторінки
        self.assertIn('Visible Note', self.driver.page_source)
