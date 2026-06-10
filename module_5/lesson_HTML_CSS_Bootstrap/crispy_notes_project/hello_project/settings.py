"""
Django settings for crispy_notes_project.

Що нового порівняно з notes_project (lesson_Django_ORM_Database):
  + crispy_forms      → FormHelper + Layout замість raw widget attrs
  + crispy_bootstrap5 → Bootstrap5 template pack для crispy
  - unfold            → прибрано (акцент цього проєкту — фронтенд, не адмін)
  - django_bootstrap5 → прибрано (crispy заміняє його для форм)

TEMPLATES → DIRS: [BASE_DIR / "templates"]
  → дозволяє шаблонам в templates/ (layouts/, components/) знаходитись поза apps
  → APP_DIRS: True → hello_app/templates/ теж шукається автоматично
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
