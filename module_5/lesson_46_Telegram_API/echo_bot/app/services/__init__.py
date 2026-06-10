"""
app/services/ — Пакет сервісів (бізнес-логіки) бота.

Сервіс — це клас або модуль з бізнес-логікою,
що НЕ залежить від Telegram (aiogram, HTTP тощо).

Модулі:
    user_service.py — відстеження унікальних користувачів (in-memory set)

Production розширення:
    Замінити in-memory сховище на PostgreSQL/Redis репозиторії.
    Handlers при цьому не змінюються (DI принцип).
"""
