"""
app/repositories/history_repo.py — Redis-репозиторій для историї розмов.

РОЛЬ У АРХІТЕКТУРІ:
    HistoryRepository інкапсулює всю логіку зберігання розмов у Redis.
    Handler (chat.py, commands.py) не знає:
        - де зберігаються дані (Redis? PostgreSQL? Memory?)
        - який формат (JSON? pickle? protobuf?)
        - який ключ використовується ("history:{id}"? "conv:{id}"?)

    Якщо завтра замінити Redis на PostgreSQL — handler не зміниться.
    Потрібно лише написати новий клас з тими самими методами.
    Це і є патерн Repository.

ЯК ЗБЕРІГАЄТЬСЯ ИСТОРИЯ У REDIS:
    Ключ: "history:{user_id}"   (наприклад: "history:123456789")
    Значення: JSON-рядок списку повідомлень
    TTL: 86400 секунд (24 години)

    Приклад значення у Redis:
        [
            {"role": "user",      "content": "Привіт! Як справи?"},
            {"role": "assistant", "content": "Добре, дякую! Чим можу допомогти?"},
            {"role": "user",      "content": "Поясни мені asyncio"},
            {"role": "assistant", "content": "asyncio — це..."}
        ]

ЧОМУ JSON, А НЕ PICKLE:
    pickle: бінарний Python-специфічний формат.
    JSON: текстовий, читабельний, сумісний між мовами.
    Redis часто переглядають через redis-cli — JSON читається одразу.

SLIDING WINDOW ДЛЯ ПАМ'ЯТІ:
    Якщо history > HISTORY_MAX_MESSAGES:
        history = history[-HISTORY_MAX_MESSAGES:]
    Зберігаємо лише ОСТАННІ N повідомлень.
    Старі зрізаються — AI "забуває" давні частини розмови.
    Це баланс між якістю контексту і витратами квоти API.

ЧОМУ TTL СКИДАЄТЬСЯ ПРИ КОЖНОМУ ЗАПИТІ:
    setex() встановлює нове TTL при кожному append().
    Якщо користувач активний — историія ніколи не видалиться.
    Якщо 24 години мовчання — историія видаляється автоматично.
    Redis сам прибирає старі ключі — не потрібен окремий cron job.
"""
import json
import logging
import redis.asyncio as aioredis

from app.config import config

# Logger для цього модуля
logger = logging.getLogger(__name__)

# TTL для ключів историї у Redis (24 години у секундах)
# 86400 = 60 * 60 * 24
HISTORY_TTL = 86400


class HistoryRepository:
    """
    Репозиторій для зберігання историї розмов у Redis.

    Створюється один раз у bot.py і передається через InjectMiddleware.
    Stateless: зберігає лише посилання на Redis клієнт (не стан).
    """

    def __init__(self, redis_client: aioredis.Redis) -> None:
        """
        Зберігає Redis клієнт для подальшого використання у методах.

        redis_client — асинхронний клієнт aioredis.
        Всі операції (get, set, delete) — корутини (await).
        """
        # Підкреслення _ — convention для "private" атрибутів
        self._redis = redis_client

    def _key(self, user_id: int) -> str:
        """
        Генерує ключ Redis для конкретного користувача.

        Шаблон: "history:{user_id}"
        Приклад: "history:123456789"

        Чому окремий метод?
            Якщо формат ключа зміниться — правимо в одному місці.
            Нема дублювання рядка "history:{}" по всіх методах.
        """
        return f"history:{user_id}"

    async def get(self, user_id: int) -> list[dict]:
        """
        Повертає список повідомлень у историї користувача.

        Якщо ключ не існує (нова розмова або після clear) → порожній список [].

        Процес:
            Redis.get("history:{id}") → JSON-рядок або None
            json.loads(raw) → Python список [{role, content}, ...]
        """
        # Читаємо рядок JSON з Redis
        raw = await self._redis.get(self._key(user_id))

        # Якщо ключ не існує — Redis повертає None
        # Повертаємо порожній список (не None) — щоб код виклику міг безпечно ітерувати
        if not raw:
            return []

        # Десеріалізуємо JSON-рядок у Python об'єкт (список словників)
        return json.loads(raw)

    async def append(self, user_id: int, role: str, content: str) -> None:
        """
        Додає нове повідомлення до историї і зберігає у Redis.

        Параметри:
            user_id — Telegram user ID (int, до 10 цифр)
            role    — "user" або "assistant" (відповідно до AI API конвенції)
            content — текст повідомлення

        Процес:
            1. Зчитати поточну историю з Redis
            2. Додати нове повідомлення у кінець списку
            3. Обрізати до HISTORY_MAX_MESSAGES (зберігаємо останні N)
            4. Зберегти оновлений JSON назад у Redis з TTL
        """
        # Зчитуємо поточну историю (або [] якщо перше повідомлення)
        history = await self.get(user_id)

        # Додаємо нове повідомлення у кінець
        history.append({"role": role, "content": content})

        # ── Sliding Window ────────────────────────────────────────────
        # Якщо историія перевищує ліміт — обрізаємо найстаріші повідомлення.
        # history[-N:] → зберігаємо ОСТАННІ N елементів.
        # Наприклад, при N=20 і len=21: залишаємо елементи [1..20], видаляємо [0].
        if len(history) > config.HISTORY_MAX_MESSAGES:
            history = history[-config.HISTORY_MAX_MESSAGES:]

        # ── Збереження у Redis ─────────────────────────────────────────
        # setex(key, ttl, value):
        #   - Встановлює значення ключа
        #   - Одразу задає TTL (time-to-live) у секундах
        #   - Атомарна операція (SET + EXPIRE за один раз)
        #
        # ensure_ascii=False:
        #   Зберігаємо Unicode символи як є (не екрануємо а тощо).
        #   Дозволяє зберігати кирилицю, емоджі тощо у читабельному вигляді.
        await self._redis.setex(
            self._key(user_id),
            HISTORY_TTL,
            json.dumps(history, ensure_ascii=False),
        )

    async def clear(self, user_id: int) -> None:
        """
        Видаляє всю историю користувача з Redis.

        Redis.delete(key):
            Видаляє ключ і значення. Якщо ключа немає — нічого не робить (безпечно).

        Використовується при:
            /start — починаємо нову розмову
            /reset — скидаємо контекст на прохання користувача
        """
        await self._redis.delete(self._key(user_id))
        logger.info("Історія скинута для user_id=%s", user_id)

    async def count(self, user_id: int) -> int:
        """
        Повертає кількість повідомлень у историї.

        Використовується у /stats для показу: "5 / 20 повідомлень у пам'яті".

        Читає і десеріалізує весь JSON для підрахунку довжини.
        Для великих историй це незначні витрати (JSON невеликий).
        """
        history = await self.get(user_id)
        return len(history)
