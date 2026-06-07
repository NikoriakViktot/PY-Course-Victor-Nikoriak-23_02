"""
Django settings — lesson_Django_authentication_and_security

Новий урок додає до crispy_notes_project:
  + password reset/change flows   → EMAIL_BACKEND (console), /accounts/password_*/
  + security settings block       → SESSION_COOKIE_HTTPONLY, X_FRAME_OPTIONS, ...
  + Group-based sharing           → Django built-in Group model used in Note/ShoppingList
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-crispy-notes-dev-key-change-in-production"

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # ── Crispy Forms ────────────────────────────────────────────────────────────
    "crispy_forms",       # core: FormHelper, Layout objects
    "crispy_bootstrap5",  # Bootstrap5 template pack
    # ── Debug ────────────────────────────────────────────────────────────────────
    "debug_toolbar",
    # ── Our app ──────────────────────────────────────────────────────────────────
    "hello_app",
]

# ── Crispy Forms Config ──────────────────────────────────────────────────────────
# Tells crispy-forms which HTML/CSS to generate
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

INTERNAL_IPS = ["127.0.0.1"]

ROOT_URLCONF = "hello_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # ── DIRS: project-level templates (base.html, layouts/, components/) ──
        # Without this, {% extends 'layouts/dashboard.html' %} would fail!
        # APP_DIRS only searches <app>/templates/, not project root templates/
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,   # also searches hello_app/templates/hello_app/
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Sidebar: notebooks + tags available in every template
                "hello_app.context_processors.sidebar_context",
            ],
        },
    },
]

WSGI_APPLICATION = "hello_project.wsgi.application"

# ── Messages → Bootstrap alert variants ─────────────────────────────────────────
from django.contrib.messages import constants as messages_constants
MESSAGE_TAGS = {
    messages_constants.DEBUG:   'secondary',
    messages_constants.INFO:    'info',
    messages_constants.SUCCESS: 'success',
    messages_constants.WARNING: 'warning',
    messages_constants.ERROR:   'danger',
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "uk"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ── Static files ─────────────────────────────────────────────────────────────────
STATIC_URL = "/static/"
# STATICFILES_DIRS: project-level static/ (custom CSS overrides)
# hello_app/static/ is found automatically via APP_DIRS
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Auth redirects
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/notes/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

# ── Email (password reset) ────────────────────────────────────────────────────
# console → лист виводиться в термінал, не надсилається реально.
# В production: django.core.mail.backends.smtp.EmailBackend + SMTP config.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ── Web Security ──────────────────────────────────────────────────────────────
# AuthenticationMiddleware: JS не може прочитати session cookie через document.cookie
SESSION_COOKIE_HTTPONLY = True

# CSRF cookie читається JS (потрібно для fetch/axios з CSRF header).
# Якщо не використовуєш JS fetch — постав True для строгого захисту.
CSRF_COOKIE_HTTPONLY = False

# SameSite=Lax: cookie надсилається тільки з того самого сайту.
# Захищає від CSRF-атак через cross-site форми.
SESSION_COOKIE_SAMESITE = "Lax"

# X-Frame-Options: браузер блокує вставку сторінки в <iframe>.
# Захищає від clickjacking-атак.
X_FRAME_OPTIONS = "DENY"

# Content-Type sniffing: браузер не вгадує тип файлу, якщо сервер не вказав.
# Захищає від XSS через завантажені файли.
SECURE_CONTENT_TYPE_NOSNIFF = True

# ── Production HTTPS (розкоментувати на сервері з SSL) ───────────────────────
# SESSION_COOKIE_SECURE = True    # cookie тільки через HTTPS
# CSRF_COOKIE_SECURE = True       # CSRF cookie тільки через HTTPS
# SECURE_SSL_REDIRECT = True      # HTTP → 301 → HTTPS
# SECURE_HSTS_SECONDS = 31536000  # браузер запам'ятовує HTTPS на 1 рік
