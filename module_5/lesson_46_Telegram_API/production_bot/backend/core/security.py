"""
backend/core/security.py — JWT-автентифікація та хешування паролів.

РОЛЬ У АРХІТЕКТУРІ:
    Security Layer — обробляє всю криптографію:
    - Хешування паролів (bcrypt)
    - Видача JWT access token
    - Верифікація JWT token

    Використовується у:
    - backend/api/admin/auth.py → login endpoint видає token
    - backend/api/deps.py → get_current_admin перевіряє token

JWT (JSON WEB TOKEN) — ЩО ЦЕ?
    JWT = base64(header) + "." + base64(payload) + "." + signature

    Приклад payload:
        {
            "sub": "admin",        ← subject (ім'я юзера)
            "role": "admin",       ← кастомне поле (роль)
            "exp": 1735689600      ← expiry (Unix timestamp)
        }

    Підпис (signature):
        HMAC-SHA256(base64(header) + "." + base64(payload), JWT_SECRET)

    Сервер не зберігає сесії — перевіряє підпис при кожному запиті.
    Якщо підпис валідний і exp не минув → токен дійсний.

ЧОМУ JWT, А НЕ SESSIONS?
    Сесії (традиційний підхід):
        - Сервер зберігає session_id → user_data у Redis/БД
        - При горизонтальному масштабуванні (кілька серверів):
          запит може потрапити на інший сервер, де немає сесії!
        - Потрібен "sticky sessions" або shared session storage

    JWT (stateless):
        - Сервер не зберігає нічого — вся інформація у токені
        - Будь-який сервер може верифікувати токен знаючи JWT_SECRET
        - Ідеально для горизонтального масштабування через Nginx LB

BCRYPT ДЛЯ ПАРОЛІВ:
    Чому не MD5/SHA256?
        MD5/SHA256 — дуже швидкі (мільярди хешів/секунду на GPU).
        Attackers можуть brute-force усі можливі паролі.

    Bcrypt — навмисно ПОВІЛЬНИЙ (cost factor = 12 ітерацій):
        ~100 мс на хеш → brute-force практично неможливий.
        Автоматично додає salt (унікальний для кожного пароля).
        → Два однакових паролі мають різні хеші.

    CryptContext(deprecated="auto"):
        При зміні алгоритму (bcrypt → argon2) — автоматично
        перехешовує старі паролі при наступному логіні.

ПОТІК АВТЕНТИФІКАЦІЇ:
    POST /admin/auth/token
        body: {username: "admin", password: "secret"}
        ↓
        verify_password("secret", stored_bcrypt_hash)
        ↓ (якщо True)
        create_access_token({"sub": "admin", "role": "admin"})
        ↓
        response: {access_token: "eyJ...", token_type: "bearer"}

    GET /admin/users (захищений endpoint)
        Authorization: Bearer eyJ...
        ↓
        bearer_scheme.credentials = "eyJ..."
        ↓
        decode_token("eyJ...") → {"sub": "admin", "role": "admin"}
        ↓ (якщо role == "admin")
        Handler виконується
"""
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from backend.core.config import settings

# ── Bcrypt контекст для хешування паролів ──────────────────────────────────
# schemes=["bcrypt"]: використовуємо bcrypt алгоритм.
# deprecated="auto": автоматично позначає старі хеші як deprecated
# і перехешовує при наступному verify_password().
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Хешує пароль за допомогою bcrypt.

    Алгоритм:
        1. Генерує випадковий salt (22 символи)
        2. Виконує 2^12 (4096) ітерацій bcrypt з salt
        3. Повертає рядок: $2b$12$<salt><hash>

    Приклад:
        hash_password("secret123")
        → "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"

    Цей хеш можна безпечно зберігати у БД.
    Навіть маючи хеш — відновити пароль практично неможливо.

    Використання:
        _ADMIN_PASSWORD_HASH = hash_password(settings.ADMIN_PASSWORD)
        (виконується один раз при завантаженні модуля)
    """
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Перевіряє чи відповідає пароль хешу.

    Алгоритм:
        1. Витягує salt з hashed рядка
        2. Хешує plain + salt
        3. Порівнює результат з hashed (constant-time comparison)

    Constant-time comparison:
        Звичайне == може "витікати" час якщо порівнювати побайтово.
        passlib використовує hmac.compare_digest() — завжди однаковий час.
        Захист від timing attacks.

    Повертає:
        True — пароль правильний
        False — пароль неправильний
    """
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict[str, Any]) -> str:
    """
    Створює підписаний JWT access token.

    Параметри:
        data: словник з payload (наприклад {"sub": "admin", "role": "admin"})

    Що відбувається:
        1. Копіюємо data (щоб не мутувати оригінал)
        2. Додаємо "exp" (expiry) = поточний час + JWT_EXPIRE_MINUTES
        3. Підписуємо payload за допомогою JWT_SECRET і HS256
        4. Повертаємо compact representation: header.payload.signature

    Приклад:
        token = create_access_token({"sub": "admin", "role": "admin"})
        # token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTczNTY4OTYwMH0.xxx"

    timezone.utc:
        Завжди використовуємо UTC для exp.
        Сервер може бути в іншому timezone ніж клієнт.
        UTC = universal reference point.
    """
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload["exp"] = expire
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Декодує та верифікує JWT токен.

    Що перевіряється автоматично:
        - Підпис (signature) — чи токен не підроблений
        - Час дії (exp) — чи токен не прострочений

    При помилках кидає:
        jwt.ExpiredSignatureError — токен прострочений (exp < now)
        jwt.InvalidTokenError    — підпис неправильний або токен пошкоджений

    Ці винятки перехоплюються у deps.py:
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    Повертає:
        dict з payload: {"sub": "admin", "role": "admin", "exp": 1735689600}
    """
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
