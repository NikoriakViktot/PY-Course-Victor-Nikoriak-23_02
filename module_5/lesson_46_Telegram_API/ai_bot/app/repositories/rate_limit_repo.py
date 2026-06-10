"""
app/repositories/rate_limit_repo.py — Redis-репозиторій для rate limiting.

РОЛЬ У АРХІТЕКТУРІ:
    RateLimitRepository інкапсулює логіку обмеження частоти запитів.
    Middleware (rate_limit.py) використовує його без знання деталей Redis.

АЛГОРИТМ: SLIDING WINDOW COUNTER (через Redis INCR + EXPIRE)

    Чому Redis, а не in-memory (звичайний dict)?
        In-memory: скидається при рестарті. Один процес.
        Redis: зберігається між рестартами. Підтримує кілька процесів/воркерів.

    Чому INCR, а не GET + SET?
        INCR — атомарна операція Redis.
        GET + порівняння + SET — НЕ атомарно: race condition між двома запитами!

        Race condition без атомарності:
            User A і User B одночасно надсилають повідомлення:
            A: GET rate:123 → 4
            B: GET rate:123 → 4  (ще не побачив запис A)
            A: SET rate:123 5    → збережено
            B: SET rate:123 5    → А МАЛО БУТИ 6! Race condition.

        З INCR (атомарно):
            A: INCR rate:123 → 5  ← атомарно: read + increment + write
            B: INCR rate:123 → 6  ← атомарно: теж правильно

ЧОМУ EXPIRE ТІЛЬКИ ПРИ count == 1:
    При першому запиті (count=1) встановлюємо TTL.
    При наступних (count=2,3,...) TTL вже встановлений, не чіпаємо.
    Якщо викликати EXPIRE при кожному INCR — "вікно" буде постійно подовжуватись.
    Ми хочемо фіксоване вікно: 5 запитів за 60 секунд з початку вікна.

    Таймлайн:
        t=0  → count=1, EXPIRE 60  (вікно починається)
        t=10 → count=2             (EXPIRE не чіпаємо)
        t=20 → count=3
        t=60 → ключ видаляється (TTL спрацював)
        t=60 → count=1, EXPIRE 60  (нове вікно починається)

ЯК ПРОЧИТАТИ TTL:
    Redis TTL команда повертає:
        -2 — ключ не існує
        -1 — ключ без TTL (без expire)
        N  — секунд до видалення (де N > 0)
    Ми повертаємо max(ttl, 0) — щоб не показувати від'ємні значення.
"""
import redis.asyncio as aioredis

from app.config import config


class RateLimitRepository:
    """
    Репозиторій для rate limiting через Redis атомарні операції.

    Stateless: зберігає лише посилання на Redis клієнт.
    Один екземпляр на весь Dispatcher.
    """

    def __init__(self, redis_client: aioredis.Redis) -> None:
        """Зберігає Redis клієнт."""
        self._redis = redis_client

    def _key(self, user_id: int) -> str:
        """
        Генерує ключ Redis для лічильника користувача.

        Шаблон: "rate:{user_id}"
        Приклад: "rate:123456789"
        """
        return f"rate:{user_id}"

    async def check_and_increment(self, user_id: int) -> tuple[bool, int]:
        """
        Атомарно збільшує лічильник і перевіряє ліміт.

        Повертає:
            (is_allowed, current_count)
            is_allowed=True  → запит дозволений (ліміт не перевищено)
            is_allowed=False → запит заблокований (ліміт вичерпано)

        Чому повертаємо count разом з is_allowed?
            Для логування у middleware: "Rate limit: user_id=X count=Y".
            Знаємо скільки запитів зробив користувач.
        """
        key = self._key(user_id)

        # INCR: атомарно збільшує значення ключа на 1.
        # Якщо ключ не існує — створює зі значенням 0, потім збільшує до 1.
        # Повертає нове значення (після збільшення).
        count = await self._redis.incr(key)

        # ── Встановлення TTL ───────────────────────────────────────────
        # count == 1: це ПЕРШИЙ запит у вікні → встановлюємо TTL.
        # Якщо б ключ вже існував з TTL — INCR лише збільшив би значення,
        # TTL залишився б незмінним (це потрібна нам поведінка).
        if count == 1:
            # EXPIRE: встановлює TTL для ключа у секундах.
            # Після RATE_LIMIT_WINDOW секунд ключ автоматично видаляється.
            await self._redis.expire(key, config.RATE_LIMIT_WINDOW)

        # ── Перевірка ліміту ───────────────────────────────────────────
        # config.RATE_LIMIT_REQUESTS: максимальна кількість запитів у вікні.
        # Якщо count перевищив ліміт — is_allowed = False.
        is_allowed = count <= config.RATE_LIMIT_REQUESTS

        return is_allowed, count

    async def get_ttl(self, user_id: int) -> int:
        """
        Повертає кількість секунд до скидання лічильника.

        Використовується у повідомленні: "Зачекайте N секунд."

        Redis TTL повертає:
            -2 → ключ не існує (вже видалений або ніколи не створювався)
            -1 → ключ без expire (не повинно траплятися — ми завжди ставимо TTL)
            N  → секунд до видалення (те що нам треба)

        max(ttl, 0): якщо раптом -1 або -2 → повертаємо 0 (безпечне значення).
        """
        ttl = await self._redis.ttl(self._key(user_id))
        return max(ttl, 0)
