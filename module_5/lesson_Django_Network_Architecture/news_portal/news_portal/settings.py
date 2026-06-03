"""
settings.py — Центральна конфігурація Django-проєкту.

РОЛЬ У АРХІТЕКТУРІ:
    Це "головний електрощит" всього проєкту.
    Завантажується в пам'ять ОДИН РАЗ при старті сервера.
    Всі інші модулі Django читають налаштування звідси.

ЩО ТУТКИ:
    - Підключення до PostgreSQL
    - Список встановлених додатків (INSTALLED_APPS)
    - Список Middleware (ланцюжок обробки запиту)
    - Шляхи до шаблонів і статики
    - Мова та часовий пояс

БЕЗПЕКА:
    SECRET_KEY та паролі БД зчитуються з файлу .env
    через python-decouple → вони НЕ захардкоджені в коді.

АНАЛОГІЯ: Панель управління всією будівлею — один центр, все звідти.
"""

from pathlib import Path

# python-decouple: зчитує значення з файлу .env
# config('KEY') → значення, config('KEY', default=...) → з дефолтом
from decouple import config

# ── Шляхи ─────────────────────────────────────────────────────────────────────

# BASE_DIR — корінь проєкту (папка де manage.py)
# Path(__file__) = news_portal/settings.py
# .parent = news_portal/
# .parent.parent = project root (де manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent


# ── Безпека ────────────────────────────────────────────────────────────────────

# SECRET_KEY використовується для:
#   - підпису сесійних cookies
#   - генерації CSRF токенів
#   - шифрування паролів скидання
# НІКОЛИ не розкривай цей ключ публічно!
SECRET_KEY = config('SECRET_KEY', default='dev-only-insecure-key-change-in-production')

# DEBUG=True → Django показує детальні сторінки помилок з трасуванням стека
# DEBUG=False → стандартна сторінка 500 (у продакшені ОБОВ'ЯЗКОВО False!)
DEBUG = config('DEBUG', default=True, cast=bool)

# Список хостів/доменів які можуть звертатись до цього сервера
# При DEBUG=False Django відхиляє запити від інших хостів → захист від HTTP Host header attacks
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')


# ── Встановлені додатки ────────────────────────────────────────────────────────

# INSTALLED_APPS = список усіх активних Django-додатків.
# Django завантажує їх при старті:
#   - реєструє моделі (таблиці БД)
#   - реєструє шаблони
#   - реєструє management commands
INSTALLED_APPS = [
    # ── Вбудовані Django-додатки ──────────────────────────────────────
    'django.contrib.admin',       # Адмін-панель (/admin/)
    'django.contrib.auth',        # Система автентифікації (User, Group)
    'django.contrib.contenttypes',# Фреймворк типів контенту (для admin, permissions)
    'django.contrib.sessions',    # Механізм сесій (зберігає стан між запитами)
    'django.contrib.messages',    # Flash-повідомлення (після редиректу)
    'django.contrib.staticfiles', # Обслуговування статичних файлів CSS/JS

    # ── Наші додатки ──────────────────────────────────────────────────
    'news',  # Наш додаток: моделі, вьюшки, шаблони для новин
]


# ── Middleware ─────────────────────────────────────────────────────────────────

# Middleware = ланцюжок "фільтрів" через які проходить КОЖЕН запит і відповідь.
# ПОРЯДОК КРИТИЧНО ВАЖЛИВИЙ! Django виконує їх зверху вниз (запит)
# і знизу вгору (відповідь).
#
# Запит:  SecurityMiddleware → SessionMiddleware → ... → View
# Відповідь: View → ... → SessionMiddleware → SecurityMiddleware
#
# ПРАВИЛО: SessionMiddleware МАЄ бути перед AuthenticationMiddleware
# (Auth читає сесію → сесія має бути ініціалізована першою)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',         # HTTPS, XSS headers
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',  # Ініціалізує сесію
    'django.middleware.common.CommonMiddleware',             # URL normalization
    'django.middleware.csrf.CsrfViewMiddleware',             # Захист від CSRF-атак
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Завантажує request.user
    'django.contrib.messages.middleware.MessageMiddleware',  # Flash-повідомлення
    'django.middleware.clickjacking.XFrameOptionsMiddleware', # Захист від clickjacking
]

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)
# ── URL конфігурація ────────────────────────────────────────────────────────────

# Вказує Django де знаходиться головний файл маршрутів
# 'news_portal.urls' = файл news_portal/urls.py
ROOT_URLCONF = 'news_portal.urls'


# ── Шаблони ────────────────────────────────────────────────────────────────────

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',  # DTL движок

        # DIRS: де Django шукає глобальні шаблони
        # BASE_DIR / 'templates' = папка templates/ в корені проєкту
        'DIRS': [BASE_DIR / 'templates'],

        # APP_DIRS=True: Django також шукає в <app>/templates/ кожного додатка
        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                # Ці функції додають дані в контекст КОЖНОГО шаблону автоматично:
                'django.template.context_processors.debug',    # {{ debug }}
                'django.template.context_processors.request',  # {{ request }}
                'django.contrib.auth.context_processors.auth', # {{ user }}, {{ perms }}
                'django.contrib.messages.context_processors.messages', # {{ messages }}
            ],
        },
    },
]


# ── WSGI ───────────────────────────────────────────────────────────────────────

# Вказує Gunicorn/uWSGI де знаходиться точка входу Django-додатку
# У продакшені: gunicorn news_portal.wsgi:application
WSGI_APPLICATION = 'news_portal.wsgi.application'


# ── База даних ─────────────────────────────────────────────────────────────────

# Django підтримує кілька БД одночасно (ключ 'default' — основна)
# ENGINE вказує який адаптер використовувати:
#   - django.db.backends.postgresql → PostgreSQL
#   - django.db.backends.sqlite3   → SQLite (файл, для прототипів)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='news_portal_db'),
        'USER': config('DB_USER', default='news_user'),
        'PASSWORD': config('DB_PASSWORD', default='news_password'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}


# ── Валідація паролів ──────────────────────────────────────────────────────────

# Django перевіряє паролі за цими правилами при реєстрації/зміні пароля
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ── Локалізація ────────────────────────────────────────────────────────────────

LANGUAGE_CODE = 'uk'       # Мова адмін-панелі і системних повідомлень → українська
TIME_ZONE = 'Europe/Kyiv'  # Часовий пояс для відображення дат
USE_I18N = True            # Увімкнути переклади інтерфейсу
USE_TZ = True              # Зберігати дати в UTC, відображати в TIME_ZONE


# ── Статичні файли ─────────────────────────────────────────────────────────────

# URL-префікс для статичних файлів: http://localhost:8000/static/css/style.css
STATIC_URL = '/static/'

# STATICFILES_DIRS: де Django шукає статику при розробці (runserver)
STATICFILES_DIRS = [BASE_DIR / 'static']

# STATIC_ROOT: куди python manage.py collectstatic збирає всі файли для Nginx
# У продакшені Nginx роздає файли з цієї папки напряму (без Django)
STATIC_ROOT = BASE_DIR / 'staticfiles'


# ── Тип первинного ключа за замовчуванням ─────────────────────────────────────

# Новий Django 3.2+: автоматично використовує BigAutoField (64-bit int)
# замість AutoField (32-bit int) для pk нових моделей
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
