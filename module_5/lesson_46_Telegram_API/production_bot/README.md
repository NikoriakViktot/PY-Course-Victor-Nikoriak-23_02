# Production Telegram Platform — Урок 46 (Advanced ⭐⭐⭐)

FastAPI + aiogram + PostgreSQL + Redis + JWT + Webhook + Docker

---

## Архітектура системи

```
Internet
    │
  Nginx (SSL, port 443)
    │ proxy_pass
  FastAPI (uvicorn, 4 workers)
    ├── POST /webhook/{SECRET}  ← Telegram Updates → aiogram Dispatcher
    ├── POST /admin/auth/token  ← JWT логін
    ├── GET  /admin/users/      ← Список users (JWT required)
    ├── POST /admin/users/block ← Заблокувати user
    └── GET  /health            ← Health check
         │
    ┌────▼─────────────────────────────────┐
    │           Шари додатку               │
    │  Handler → Service → Repository → DB │
    └──────────────────────────────────────┘
         │              │
    PostgreSQL        Redis
    (users, subs,    (cache, rate limit,
     payments,       FSM storage)
     messages,
     referrals,
     audit_logs)
```

---

## Чому такий стек?

| Рішення | Причина |
|---------|---------|
| **Webhook** замість Polling | Миттєва доставка, горизонтальне масштабування |
| **FastAPI** окремо від aiogram | Swagger, Admin API, health check — aiogram це не дає |
| **SQLAlchemy async + asyncpg** | Не блокує Event Loop під час DB-запитів |
| **Connection Pool** (pool_size=10) | Повторне використання з'єднань без overhead |
| **JWT stateless** | Горизонтальне масштабування без shared session storage |
| **Alembic** | Версіонований DB schema як код |
| **AuditLog** | Відповідальність за дії адміністраторів |
| **BlockCheck Middleware** | Зупиняємо заблокованих users до будь-якого Handler |

---

## Шари додатку

```
Handler (bot/handlers/)
  ↓ використовує
Service (services/)         ← бізнес-логіка, оркестрація
  ↓ використовує
Repository (repositories/)  ← SQL-запити, ізоляція від Handler
  ↓ використовує
Model (models/)             ← SQLAlchemy ORM таблиці
  ↓ зберігає в
PostgreSQL
```

**Правило:** Handler ніколи не пише SQL напряму. Repository ніколи не знає про HTTP.

---

## Розгортання

```bash
# 1. Підготовка
cp .env.example .env
# Заповнити: BOT_TOKEN, WEBHOOK_SECRET, WEBHOOK_HOST, JWT_SECRET, DATABASE_URL

# 2. Старт (автоматично виконає міграції через сервіс migrate)
docker compose up --build -d

# 3. Перевірка
curl https://your-domain.com/health

# 4. Логи
docker compose logs -f bot
```

---

## Admin API

```bash
# Логін (отримати JWT)
curl -X POST https://your-domain.com/admin/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'
# → {"access_token": "eyJ...", "token_type": "bearer"}

# Список users
curl https://your-domain.com/admin/users/ \
  -H "Authorization: Bearer eyJ..."

# Заблокувати user
curl -X POST https://your-domain.com/admin/users/block \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"tg_id": 123456789, "reason": "Спам"}'

# Аналітика
curl https://your-domain.com/admin/analytics/overview \
  -H "Authorization: Bearer eyJ..."
```

---

## Alembic міграції

```bash
# Нова міграція (після зміни моделей)
alembic revision --autogenerate -m "add_new_column"

# Застосувати всі міграції
alembic upgrade head

# Відкат на одну міграцію назад
alembic downgrade -1

# Поточний стан
alembic current
```

---

## DB Schema

```
users ──────────┐
  id (PK)       │
  tg_id (BIGINT)│ ← BigInteger! Нові Telegram ID > 32-bit Integer
  username      │
  is_blocked    │
  is_admin      │
                │
subscriptions   │
  user_id (FK)──┤
  tier          │  'free' | 'basic' | 'premium'
  requests_limit│
  expires_at    │
                │
payments        │
  user_id (FK)──┤
  provider      │  'stars' | 'stripe'
  amount        │
  currency      │  'XTR' (Stars) або 'USD'
                │
messages        │
  user_id (FK)──┤
  content_type  │  для аналітики
  created_at    │  indexed
                │
referrals       │
  referrer_id──┐│
  referred_id──┘│
                │
audit_logs      │
  admin_username│  хто зробив дію
  action        │
  target_user_id│
```

---

## Scaling Strategy

```
1 VPS (< 10k users/day):
  docker compose up (1 bot instance)

10 VPS (< 100k users/day):
  Nginx → [bot:8001, bot:8002, ..., bot:8010]
  Shared PostgreSQL + Redis

Kubernetes (> 1M users/day):
  Deployment: bot (replicas=20)
  Service: ClusterIP → Ingress → Nginx
  StatefulSet: PostgreSQL (pg-HA) + Redis Cluster
  HorizontalPodAutoscaler: CPU > 70% → scale up
```
