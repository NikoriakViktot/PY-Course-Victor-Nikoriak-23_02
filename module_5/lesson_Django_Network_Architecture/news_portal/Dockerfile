# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile — Образ Docker для Django-додатку.
#
# РОЛЬ У АРХІТЕКТУРІ:
#   Dockerfile = рецепт для збірки Docker-образу.
#   Образ = ізольоване середовище з Python, залежностями і нашим кодом.
#
# ЯК ЗІБРАТИ:
#   docker build -t news_portal .
#
# ЯК ЗАПУСТИТИ (без Docker Compose):
#   docker run -p 8000:8000 news_portal
#
# З Docker Compose: docker compose up --build
# ─────────────────────────────────────────────────────────────────────────────

# ── Базовий образ ──────────────────────────────────────────────────────────────
# python:3.12-slim — мінімальна версія Python 3.12 без зайвих пакетів
# slim ≈ 45 MB замість 900 MB у повного образу
FROM python:3.12-slim

# ── Налаштування Python ────────────────────────────────────────────────────────
# PYTHONDONTWRITEBYTECODE=1 → не створювати .pyc файли (зменшує образ)
# PYTHONUNBUFFERED=1 → вивід print() одразу потрапляє в Docker логи
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ── Робоча директорія в контейнері ────────────────────────────────────────────
# Всі наступні команди виконуються відносно /app
WORKDIR /app

# ── Встановлення системних залежностей ────────────────────────────────────────
# libpq-dev → потрібен для компіляції psycopg2 (PostgreSQL адаптер)
# gcc → компілятор для C-розширень Python (lxml, psycopg2)
# && rm -rf /var/lib/apt/lists/* → очищення кешу apt → менший образ
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# ── Встановлення Python залежностей ───────────────────────────────────────────
# СПОЧАТКУ копіюємо тільки requirements.txt (не весь код!)
# Якщо код зміниться але requirements.txt залишиться — Docker використовує кеш цього шару
# → щоразу pip install не запускається якщо залежності не змінились (швидша збірка)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Копіювання коду ────────────────────────────────────────────────────────────
# Копіюємо весь проєкт в /app
COPY . .

# ── Порт ──────────────────────────────────────────────────────────────────────
# Документуємо що контейнер слухає на порті 8000
# EXPOSE не публікує порт — це робить docker-compose.yml (ports: "8000:8000")
EXPOSE 8000

# ── Команда запуску ────────────────────────────────────────────────────────────
# gunicorn — production WSGI сервер
# news_portal.wsgi:application — де знаходиться WSGI application об'єкт
# --bind 0.0.0.0:8000 → слухати на всіх інтерфейсах (щоб Docker зміг пробросити порт)
# --workers 2 → 2 паралельних Python процеси
CMD ["python", "-m", "gunicorn", "news_portal.wsgi:application", \
     "--bind", "0.0.0.0:8000", "--workers", "2"]
