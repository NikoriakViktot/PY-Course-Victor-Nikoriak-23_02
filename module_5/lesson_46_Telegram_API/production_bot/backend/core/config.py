"""
backend/core/config.py — Конфігурація через змінні середовища.

РОЛЬ У АРХІТЕКТУРІ:
    Єдине місце де читаються змінні середовища.
    Весь інший код імпортує `settings` — не читає os.getenv() сам.

    Принцип 12-Factor App (https://12factor.net/config):
    "Конфігурація зберігається у середовищі, а не у коді."

    ┌─────────────────────────────────────────────────────────┐
    │  .env (локально) або Docker environment:                │
    │  BOT_TOKEN=7123456789:AAF...                            │
    │  WEBHOOK_SECRET=my-random-32-char-secret                │
    │  WEBHOOK_HOST=https://mybotdomain.com                   │
    │  DATABASE_URL=postgresql+asyncpg://user:pass@db/botdb   │
    │  JWT_SECRET=another-random-secret-for-jwt               │
    └─────────────────────────────────────────────────────────┘

ЗМІННІ З ЗАМОВЧУВАННЯМИ VS БЕЗ:
    З замовчуванням (os.getenv("KEY", "default")):
        - Необов'язкові налаштування (LOG_LEVEL, DEBUG, ENVIRONMENT)
        - Не критичні при відсутності

    Без замовчування або з порожнім рядком (os.getenv("KEY", "")):
        - BOT_TOKEN, WEBHOOK_SECRET, WEBHOOK_HOST, JWT_SECRET
        - Перевіряються у validate() — застосунок впаде при старті

WEBHOOK_PATH ТА WEBHOOK_URL ЯК @property:
    Ці значення НЕ зберігаються як атрибути класу — вони обчислюються.
    Причина: WEBHOOK_SECRET читається з env при ініціалізації Settings,
    тому WEBHOOK_PATH/URL мають бути property щоб завжди використовувати
    актуальне значення WEBHOOK_SECRET.

    WEBHOOK_HOST = https://mybotdomain.com
    WEBHOOK_PATH = /webhook/my-random-32-char-secret
    WEBHOOK_URL  = https://mybotdomain.com/webhook/my-random-32-char-secret

    Секрет у URL — перша лінія захисту webhook endpoint.

SINGLETON PATTERN:
    settings = Settings()  ← один екземпляр для всього застосунку
    Всі модулі: from backend.core.config import settings
"""
import os
from dotenv import load_dotenv

# Завантажуємо .env файл якщо він існує.
# У Docker-контейнері .env зазвичай відсутній — використовуються
# змінні environment з docker-compose.yml або Kubernetes secrets.
load_dotenv()


class Settings:
    """
    Конфігурація production-боту.

    Читає всі env vars при ініціалізації.
    Методи validate() та @property обчислюються при зверненні.
    """

    # ── Telegram ────────────────────────────────────────────────────────
    # BOT_TOKEN: отримати у @BotFather → /newbot
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

    # WEBHOOK_SECRET: випадковий рядок 32+ символи (UUID без дефісів підходить).
    # Використовується у ДВОХ місцях безпеки:
    #   1. URL path: /webhook/{WEBHOOK_SECRET} — "security through obscurity"
    #   2. Заголовок X-Telegram-Bot-Api-Secret-Token — Telegram підписує кожен запит
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")

    # WEBHOOK_HOST: повний домен БЕЗ слешу на кінці.
    # Приклад: https://mybotdomain.com
    # Вимога Telegram: HTTPS обов'язково (port 443, 80, 88 або 8443)
    WEBHOOK_HOST: str = os.getenv("WEBHOOK_HOST", "")

    @property
    def WEBHOOK_PATH(self) -> str:
        """
        URL path для webhook endpoint.

        Формат: /webhook/{WEBHOOK_SECRET}
        Приклад: /webhook/a3f8b2c1d9e4f705a8b3c2d1e9f40857

        Чому секрет у PATH, а не лише в заголовку?
            X-Telegram-Bot-Api-Secret-Token захищає від Telegram-серверів.
            Але якщо хтось знає URL — він може надіслати будь-що.
            Секрет у path = додатковий захист від сканерів.
        """
        return f"/webhook/{self.WEBHOOK_SECRET}"

    @property
    def WEBHOOK_URL(self) -> str:
        """
        Повний URL який реєструється у Telegram через bot.set_webhook().

        Формат: {WEBHOOK_HOST}{WEBHOOK_PATH}
        Приклад: https://mybotdomain.com/webhook/a3f8b2c1d9e4f705a8b3c2d1e9f40857

        Telegram надсилатиме POST-запити на цей URL при кожному Update.
        """
        return f"{self.WEBHOOK_HOST}{self.WEBHOOK_PATH}"

    # ── База даних ──────────────────────────────────────────────────────
    # asyncpg driver (async) замість psycopg2 (sync).
    # Формат: postgresql+asyncpg://user:password@host:port/dbname
    # У Docker: host = назва сервісу (наприклад "db", "postgres")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://user:password@localhost:5432/botdb",
    )

    # ── Redis ───────────────────────────────────────────────────────────
    # Redis використовується для rate limiting та Circuit Breaker.
    # Формат: redis://host:port/db_number
    # Замовчування /0 — перша база Redis (є 16 баз: /0.../15)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # ── JWT (JSON Web Token) ────────────────────────────────────────────
    # JWT_SECRET: секретний ключ для підпису токенів.
    # НІКОЛИ не залишати "change-me-in-production" у реальному деплої!
    # Генерація: python -c "import secrets; print(secrets.token_hex(32))"
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me-in-production")

    # JWT_ALGORITHM: HS256 = HMAC-SHA256 (симетричний підпис).
    # Альтернатива: RS256 (асиметричний, для мікросервісів).
    # HS256 достатній для одного сервісу.
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

    # JWT_EXPIRE_MINUTES: час життя токена.
    # 60 хвилин = токен треба оновлювати кожну годину.
    # Для адмін-панелі зазвичай достатньо.
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

    # ── Адмін-доступ ────────────────────────────────────────────────────
    # Одиничний адмін-акаунт для Admin API.
    # У production: ЗМІНИТИ замовчування та передати через env!
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "change-me")

    # ── Застосунок ──────────────────────────────────────────────────────
    # DEBUG: якщо True — увімкнено Swagger UI та розширені логи.
    # Отримуємо рядок з env, конвертуємо у bool через порівняння.
    # "true" → True, будь-що інше → False (безпечно за замовчуванням).
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # LOG_LEVEL: рівень логування (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    # У production: INFO (не показує debug-деталі у логах).
    # При дебагуванні: DEBUG (показує SQL-запити якщо echo=True).
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # ENVIRONMENT: мітка для health check та логів.
    # Значення: production, staging, development
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")

    def validate(self) -> None:
        """
        Перевіряє наявність обов'язкових змінних середовища.

        Викликається у create_app() ДО старту uvicorn.
        Якщо будь-яка змінна відсутня — кидає ValueError.
        Застосунок відразу зупиняється з чітким повідомленням.

        Чому краще впасти при старті, а не в рантаймі?
            Рантаймова помилка:
                Бот стартує, приймає Updates, а потім при першому запиті
                падає з криптичним AttributeError → складно дебажити.

            Помилка при старті:
                uvicorn: ValueError: Missing env vars: BOT_TOKEN, JWT_SECRET
                → відразу зрозуміло що виправити.

        Збирає ВСІ відсутні змінні одразу (не зупиняється на першій).
        """
        required = {
            "BOT_TOKEN": self.BOT_TOKEN,
            "WEBHOOK_SECRET": self.WEBHOOK_SECRET,
            "WEBHOOK_HOST": self.WEBHOOK_HOST,
            "JWT_SECRET": self.JWT_SECRET,
        }
        # list comprehension: збираємо ключі де значення порожнє
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise ValueError(f"Missing env vars: {', '.join(missing)}")


# Singleton — один екземпляр для всього застосунку.
# Інші модулі: from backend.core.config import settings
# НЕ створювати Settings() у кожному модулі — зайве читання env.
settings = Settings()
