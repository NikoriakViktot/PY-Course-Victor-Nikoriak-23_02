"""
wsgi.py — Синхронний шлюз між веб-сервером та Django.

РОЛЬ У АРХІТЕКТУРІ:
    WSGI (Web Server Gateway Interface) — стандартний протокол з'єднання
    веб-сервера (Gunicorn/Nginx) з Python-застосунком (Django).

    Схема:          Nginx → Gunicorn → wsgi.py → Django
    Що відбувається: HTTP байти перетворюються на Python-словник environ
                     і передаються до Django для обробки.

У РОЗРОБЦІ:
    python manage.py runserver  → запускає вбудований сервер (теж через WSGI)

У ПРОДАКШЕНІ:
    gunicorn news_portal.wsgi:application --workers 4
    (Gunicorn читає об'єкт 'application' з цього файлу)

АНАЛОГІЯ: Перекладач між мовою HTTP і мовою Python.
"""

import os
from django.core.wsgi import get_wsgi_application

# Вказуємо Django де знаходяться налаштування
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news_portal.settings')

# get_wsgi_application() — повертає callable об'єкт Django-застосунку
# Gunicorn викликає його для кожного HTTP-запиту
application = get_wsgi_application()
