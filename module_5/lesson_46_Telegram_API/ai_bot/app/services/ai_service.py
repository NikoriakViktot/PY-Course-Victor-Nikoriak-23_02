"""
app/services/ai_service.py — Fault-tolerant AI Gateway для Google Gemini.

РОЛЬ У АРХІТЕКТУРІ:
    Цей файл — єдина точка взаємодії бота з Google Gemini API.
    Handler (chat.py) просто викликає ask() і отримує текст відповіді.
    Вся складна логіка надійності прихована тут.

ЧОМУ Gemini А НЕ OpenAI:
    - Безкоштовна квота: Gemini 2.0 Flash → 15 req/min, 1M tokens/day
    - Ключ без кредитної картки: aistudio.google.com → Get API Key
    - Порівнянна якість відповідей

КЛЮЧОВА ПРОБЛЕМА: Gemini SDK є СИНХРОННИМ.
    google-genai SDK НЕ підтримує native async.
    Прямий виклик у async handler:
        ❌ client.models.generate_content(...)  ← блокує Event Loop!

    Це означає: поки виконується запит до Gemini (3-10 сек),
    Event Loop aiogram заморожується і НІХТО інший не отримає відповідь.

    РІШЕННЯ: asyncio.to_thread()
        ✅ await asyncio.to_thread(_call_gemini_sync, model, prompt, sys)
        Запускає синхронний виклик у ThreadPool.
        Event Loop залишається вільним для інших корутин під час HTTP-запиту.

    Порівняння:
        10 одночасних users:
        ❌ Sync: user №10 чекає ~60с (9 × ~6с)
        ✅ asyncio.to_thread: всі 10 отримують відповідь за ~6с

MODEL_POOL — КАСКАДНИЙ FALLBACK:
    Gemini Flash може повертати 503 (Service Unavailable) у пікові години.
    Замість краша бота автоматично переходимо до наступної моделі:

    MODEL_POOL[0] → 503 → MODEL_POOL[1] → 429 → MODEL_POOL[2] → ok ✓

    Порядок: від кращої якості до легшої/дешевшої.

CIRCUIT BREAKER PATTERN (через Redis):
    Проблема: якщо Gemini повністю недоступний, кожне повідомлення
    спробує 4 моделі × timeout = 60+ секунд очікування.
    Telegram відключить бота від polling.

    Рішення — Circuit Breaker:
        5 невдалих спроб підряд → circuit OPEN (TTL 300 сек)
        Поки circuit OPEN → нові запити відразу отримують "сервіс недоступний"
        Через 5 хвилин → ключ видаляється автоматично → circuit AUTO-CLOSE
        Наступний успішний запит → записуємо success → circuit залишається закритим

    Чому Redis, а не in-memory?
        In-memory скидається при рестарті.
        Redis зберігає стан між рестартами і між кількома процесами.

КЛАСИФІКАЦІЯ ПОМИЛОК:
    Різні помилки вимагають різних дій:
        404 (model not found) → пробуємо наступну модель зі списку
        429 (quota exceeded)  → пробуємо наступну (у неї інша квота)
        503 (high demand)     → пробуємо наступну
        timeout              → пробуємо наступну
        unknown              → пробуємо наступну

    Класифікація через рядки помилок (не коди статусу),
    бо google-genai SDK не завжди структурує виняток.
"""
import asyncio
import logging
import time
from typing import Any

from app.config import config

# Logger для цього модуля
logger = logging.getLogger(__name__)

# ── Захищений імпорт SDK ──────────────────────────────────────────────────
# Якщо google-genai не встановлено (pip install google-genai) —
# не падаємо з ImportError при запуску, лише логуємо помилку.
# ask() перевірить _SDK_AVAILABLE і поверне повідомлення про помилку.
try:
    from google import genai
    from google.genai import types as genai_types
    _SDK_AVAILABLE = True  # SDK доступний, можна робити запити
except ImportError:
    genai = None  # type: ignore[assignment]
    _SDK_AVAILABLE = False
    logger.error(
        "google-genai SDK не встановлено. Виконайте: pip install google-genai"
    )

# ── Model Pool ────────────────────────────────────────────────────────────
# Список моделей у порядку пріоритету (перша = найкраща).
# При помилці автоматично переходимо до наступної.
# Різні моделі мають різні квоти — навіть якщо flash-2.5 вичерпав квоту,
# gemini-2.0-flash може ще мати запаси.
MODEL_POOL: list[str] = [
    "gemini-2.5-flash",       # primary — найкраща якість відповідей
    "gemini-2.5-flash-lite",  # швидший і дешевший fallback
    "gemini-2.0-flash",       # старше покоління, окрема квота
    "gemini-2.0-flash-lite",  # найлегший, останній шанс
]

# Timeout для HTTP запиту до Gemini API (у мілісекундах).
# 60 000 мс = 60 секунд.
# Telegram очікує відповідь від бота до ~30 секунд (webhook).
# При polling — необмежено, але 60с — розумний ліміт.
_HTTP_TIMEOUT_MS = 60_000

# ── Сигнали для класифікації помилок ─────────────────────────────────────
# google-genai SDK кидає Exception з текстовим описом помилки.
# Ми шукаємо підрядки у str(exception).lower() для класифікації.
# Це надійніше за перевірку .status_code (яке не завжди доступне).
_SIGNALS_404 = ("404", "not_found", "invalid_argument", "not found", "model not found")
_SIGNALS_429 = ("429", "resource_exhausted", "quota", "rate limit", "too many")
_SIGNALS_503 = ("503", "unavailable", "high demand", "service unavailable")
_SIGNALS_TIMEOUT = ("timeout", "timed out", "deadline", "read timeout")

# ── Redis ключі для Circuit Breaker ──────────────────────────────────────
_CB_FAILURE_KEY = "ai_bot:cb:failures"  # лічильник помилок (int)
_CB_OPEN_KEY = "ai_bot:cb:open"         # прапор "circuit відкритий" (1)
_CIRCUIT_THRESHOLD = 5   # скільки помилок відкривають circuit
_CIRCUIT_TTL = 300       # скільки секунд circuit залишається відкритим (5 хв)


def _classify_error(exc: Exception, model: str) -> dict[str, Any]:
    """
    Класифікує виняток Gemini API за кодом помилки.

    Перетворює будь-який Exception у словник:
        {"model": "...", "status_code": 503, "reason": "high_demand"}

    Чому рядковий пошук, а не isinstance перевірка типів?
        google-genai SDK кидає різні типи винятків (APIError, TimeoutError тощо).
        Рядковий пошук у str(exc) надійніший — підходить для будь-якого типу.

    Параметри:
        exc   — виняток від Gemini SDK
        model — назва моделі (для логу)

    Повертає:
        dict з полями: model, status_code, reason
    """
    # Переводимо опис помилки у нижній регістр для case-insensitive пошуку
    msg = str(exc).lower()

    # Базовий словник (завжди включаємо ім'я моделі)
    base: dict[str, Any] = {"model": model}

    # Перевіряємо сигнали у порядку специфічності
    if any(s in msg for s in _SIGNALS_404):
        # Модель не існує або неправильний запит
        return {**base, "status_code": 404, "reason": "invalid_model"}

    if any(s in msg for s in _SIGNALS_429):
        # Квота вичерпана або занадто багато запитів
        return {**base, "status_code": 429, "reason": "quota_exhausted"}

    if any(s in msg for s in _SIGNALS_503):
        # Сервіс перевантажений або недоступний
        return {**base, "status_code": 503, "reason": "high_demand"}

    if any(s in msg for s in _SIGNALS_TIMEOUT):
        # HTTP таймаут — запит зайняв більше _HTTP_TIMEOUT_MS
        return {**base, "status_code": 408, "reason": "timeout"}

    # Невідома помилка — логуємо і продовжуємо fallback
    return {**base, "status_code": 0, "reason": "unknown"}


async def _circuit_is_open(redis_client) -> bool:
    """
    Перевіряє чи Circuit Breaker відкритий (AI вимкнено).

    Читає ключ _CB_OPEN_KEY з Redis.
    Якщо ключ існує → circuit OPEN → повертаємо True.
    Якщо ключа немає → circuit CLOSED → повертаємо False.

    Обертаємо у try/except: якщо Redis недоступний — вважаємо circuit CLOSED
    і дозволяємо запит до Gemini (fail-open стратегія).
    """
    try:
        # Redis.get() повертає "1" (рядок) або None
        # bool("1") = True, bool(None) = False
        return bool(await redis_client.get(_CB_OPEN_KEY))
    except Exception:
        # Redis недоступний — fail-open: дозволяємо запит
        return False


async def _circuit_record_failure(redis_client) -> None:
    """
    Записує невдалу спробу і відкриває circuit при досягненні порогу.

    Алгоритм:
        1. Читаємо поточний лічильник збоїв (або 0 якщо немає)
        2. Збільшуємо на 1 і зберігаємо з TTL
        3. Якщо лічильник >= CIRCUIT_THRESHOLD → відкриваємо circuit
    """
    try:
        # Читаємо поточне значення (або "0" якщо ключа нема) і збільшуємо
        failures = int(await redis_client.get(_CB_FAILURE_KEY) or 0) + 1

        # Зберігаємо оновлений лічильник з TTL
        # setex(key, ttl, value) — встановити + expire атомарно
        await redis_client.setex(_CB_FAILURE_KEY, _CIRCUIT_TTL, failures)

        # Якщо досягли порогу — відкриваємо circuit
        if failures >= _CIRCUIT_THRESHOLD:
            # Встановлюємо прапор "circuit open" з TTL
            # Через _CIRCUIT_TTL секунд ключ автоматично видалиться → circuit auto-closes
            await redis_client.setex(_CB_OPEN_KEY, _CIRCUIT_TTL, 1)
            logger.error(
                "[CIRCUIT] OPEN після %d помилок — AI вимкнено на %ds",
                failures,
                _CIRCUIT_TTL,
            )
    except Exception as e:
        # Якщо Redis недоступний — не падаємо (деградація graceful)
        logger.warning("[CIRCUIT] Redis помилка при записі failure: %s", e)


async def _circuit_record_success(redis_client) -> None:
    """
    Записує успішний запит — скидає Circuit Breaker.

    При успішній відповіді від Gemini:
        Видаляємо лічильник збоїв і прапор "open".
        Circuit повертається у стан CLOSED.
    """
    try:
        # Видаляємо обидва ключі — circuit повністю скидається
        await redis_client.delete(_CB_FAILURE_KEY)
        await redis_client.delete(_CB_OPEN_KEY)
    except Exception:
        # Якщо Redis недоступний — нічого страшного, запит вже вдався
        pass


def _call_gemini_sync(model: str, prompt: str, system_prompt: str) -> str:
    """
    Синхронний виклик Google Gemini API.

    ВАЖЛИВО: ця функція СИНХРОННА (не async).
    Вона НЕ повинна викликатися напряму з async коду.
    Завжди використовуй: await asyncio.to_thread(_call_gemini_sync, ...)

    Чому синхронна?
        google-genai SDK не підтримує native async.
        asyncio.to_thread() запускає її у ThreadPool → Event Loop вільний.

    Процес:
        1. Створює новий genai.Client з API ключем і timeout
        2. Відправляє HTTP POST до Google AI API
        3. Повертає текст відповіді

    Параметри:
        model         — назва моделі (з MODEL_POOL)
        prompt        — повна история розмови у текстовому форматі
        system_prompt — системний промт (роль/особистість бота)

    Чому створюємо новий Client у кожному виклику?
        google-genai Client не thread-safe.
        asyncio.to_thread() може запускати функцію у різних threads.
        Новий Client на кожен виклик — безпечна стратегія.
    """
    # Створюємо HTTP клієнт з API ключем і timeout
    client = genai.Client(
        api_key=config.GEMINI_API_KEY,
        # HttpOptions: налаштування HTTP транспорту
        # timeout в мілісекундах — обмежує час очікування відповіді
        http_options=genai_types.HttpOptions(timeout=_HTTP_TIMEOUT_MS),
    )

    # Виконуємо синхронний HTTP запит до Gemini API
    response = client.models.generate_content(
        model=model,        # наприклад: "gemini-2.5-flash"
        contents=prompt,    # текст запиту (история розмови)

        # GenerateContentConfig — параметри генерації відповіді
        config=genai_types.GenerateContentConfig(
            # system_instruction — системний промт (роль бота)
            # Передається ОКРЕМО від contents (не як частина розмови)
            system_instruction=system_prompt,

            # max_output_tokens — максимальна кількість токенів у відповіді
            # 1 токен ≈ 4 символи (для англійської), ≈ 2-3 символи (кирилиця)
            max_output_tokens=config.GEMINI_MAX_TOKENS,

            # temperature — "творчість" AI
            # 0.0 = детерміністичний (одна й та сама відповідь завжди)
            # 0.7 = баланс між точністю і різноманітністю
            # 1.0 = максимальна варіативність
            temperature=0.7,
        ),
    )

    # response.text — текст відповіді AI (string)
    return response.text


async def ask(
    messages: list[dict],
    system_prompt: str | None = None,
    redis_client=None,
) -> str | None:
    """
    Головна публічна функція — надсилає историю до Gemini і отримує відповідь.

    Реалізує повний fault-tolerant pipeline:
        1. Перевіряє SDK
        2. Перевіряє Circuit Breaker
        3. Будує prompt з историї
        4. Пробує кожну модель з MODEL_POOL (з логуванням)
        5. При успіху — скидає Circuit Breaker, повертає текст
        6. При повній відмові — записує failure, повертає повідомлення про помилку

    Параметри:
        messages      — список {role, content} — история розмови з Redis
        system_prompt — системний промт (якщо None — з config.SYSTEM_PROMPT)
        redis_client  — Redis клієнт для Circuit Breaker (None = CB вимкнений)

    Повертає:
        str  — текст відповіді AI (успіх)
        str  — повідомлення про помилку (Circuit Breaker OPEN або всі моделі failed)
        None — якщо повернення None очікується вище (не в поточній реалізації)
    """

    # ── Крок 1: Перевірка SDK ─────────────────────────────────────────────
    # Якщо google-genai не встановлено — повертаємо інструкцію одразу
    if not _SDK_AVAILABLE:
        return "⚠️ google-genai SDK не встановлено. Виконайте: pip install google-genai"

    # Використовуємо переданий промт або дефолтний з конфігурації
    sys_prompt = system_prompt or config.SYSTEM_PROMPT

    # ── Крок 2: Перевірка Circuit Breaker ───────────────────────────────
    # Якщо redis_client передано і circuit відкритий — відхиляємо одразу.
    # Не витрачаємо час на спроби підключитись до недоступного Gemini.
    if redis_client and await _circuit_is_open(redis_client):
        logger.warning("[GATEWAY] Circuit OPEN — пропускаємо AI виклики")
        return "🔴 AI сервіс тимчасово недоступний. Спробуйте за 5 хвилин."

    # ── Крок 3: Будуємо prompt з историї розмови ────────────────────────
    # Перетворюємо список [{role, content}, ...] у один текстовий рядок.
    # Gemini отримує весь контекст у одному запиті.
    #
    # Формат:
    #     "Користувач: Привіт!
    #      Асистент: Привіт! Чим можу допомогти?
    #      Користувач: Поясни asyncio"
    conversation = "\n".join(
        f"{'Користувач' if m['role'] == 'user' else 'Асистент'}: {m['content']}"
        for m in messages
    )

    # Список для відстеження всіх спроб (для логу при повній відмові)
    attempts: list[dict] = []

    # ── Крок 4: Каскадний fallback по MODEL_POOL ─────────────────────────
    for idx, model in enumerate(MODEL_POOL, start=1):
        logger.info(
            "[GATEWAY] спроба %d/%d model=%s",
            idx,
            len(MODEL_POOL),
            model,
        )

        # time.monotonic() — монотонний годинник для вимірювання латентності.
        # Не залежить від системного часу (DST, NTP тощо).
        t0 = time.monotonic()

        try:
            # ── Виклик Gemini у ThreadPool ───────────────────────────────
            # asyncio.to_thread():
            #   Запускає синхронну функцію _call_gemini_sync у ThreadPool.
            #   Event Loop aiogram залишається вільним під час HTTP запиту.
            #   Еквівалент: executor.submit(_call_gemini_sync, model, ...).await
            text = await asyncio.to_thread(
                _call_gemini_sync,  # функція для виконання у thread
                model,              # аргументи для цієї функції
                conversation,
                sys_prompt,
            )

            # ── Успіх ───────────────────────────────────────────────────
            # Вимірюємо та логуємо латентність відповіді
            latency = int((time.monotonic() - t0) * 1000)
            logger.info(
                "[GATEWAY] успіх model=%s latency_ms=%d chars=%d",
                model,
                latency,
                len(text),
            )

            attempts.append({
                "model": model,
                "status": "success",
                "latency_ms": latency,
            })

            # Скидаємо Circuit Breaker при успіху
            if redis_client:
                await _circuit_record_success(redis_client)

            # Повертаємо текст відповіді — основний шлях успіху
            return text

        except Exception as exc:
            # ── Помилка — класифікуємо і пробуємо наступну модель ───────
            latency = int((time.monotonic() - t0) * 1000)
            err = _classify_error(exc, model)

            attempts.append({
                "model": model,
                "status": "failed",
                "reason": err["reason"],
                "latency_ms": latency,
            })

            logger.warning(
                "[GATEWAY] %s status=%d reason=%s latency_ms=%d",
                model,
                err["status_code"],
                err["reason"],
                latency,
            )
            # Продовжуємо цикл → наступна модель у MODEL_POOL

    # ── Крок 5: Всі моделі вичерпані ─────────────────────────────────────
    # Сюди потрапляємо лише якщо ВСІ моделі у MODEL_POOL повернули помилку.

    # Записуємо failure у Circuit Breaker (5-й failure відкриє circuit)
    if redis_client:
        await _circuit_record_failure(redis_client)

    logger.error(
        "[GATEWAY] всі %d моделей вичерпано. attempts=%s",
        len(MODEL_POOL),
        attempts,
    )

    # Повертаємо людське повідомлення про помилку (не None, не виняток)
    return (
        "😔 AI сервіс наразі недоступний.\n"
        "Спробуйте ще раз через кілька хвилин або /reset для очищення контексту."
    )
