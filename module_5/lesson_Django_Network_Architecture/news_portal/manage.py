#!/usr/bin/env python
"""
manage.py — Оркестратор командного рядка Django.

РОЛЬ У АРХІТЕКТУРІ:
    Це точка входу для всіх адміністративних команд.
    Він НЕ обробляє живий вебтрафік — лише команди розробника.

    Приклади команд:
        python manage.py runserver        ← запустити локальний сервер
        python manage.py makemigrations   ← зафіксувати зміни моделей
        python manage.py migrate          ← застосувати міграції до БД
        python manage.py createsuperuser  ← створити адміністратора
        python manage.py parse_rbc        ← наша кастомна команда парсингу

ЯК ЦЕ ПРАЦЮЄ:
    1. Встановлює змінну оточення DJANGO_SETTINGS_MODULE
       → Django знає, де шукати settings.py
    2. Викликає execute_from_command_line()
       → Django парсить аргументи і запускає відповідну команду

АНАЛОГІЯ: Виконроб на будівництві — ти віддаєш команди, він делегує фреймворку.
"""

import os
import sys


def main():
    """Точка входу: налаштовує Django і виконує команду."""

    # Вказуємо Django де знаходиться файл налаштувань.
    # 'news_portal.settings' означає файл news_portal/settings.py
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news_portal.settings')

    try:
        # Імпортуємо функцію виконання команд Django
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Якщо Django не встановлений — підказуємо що робити
        raise ImportError(
            "Не вдалося імпортувати Django. Переконайся, що:\n"
            "1. Django встановлений: pip install django\n"
            "2. Активовано правильне virtual environment\n"
            "3. Змінна DJANGO_SETTINGS_MODULE встановлена правильно."
        ) from exc

    # Передаємо аргументи командного рядка в Django
    # sys.argv = ['manage.py', 'runserver'] або ['manage.py', 'migrate'] тощо
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
