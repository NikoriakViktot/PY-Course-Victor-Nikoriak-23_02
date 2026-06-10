"""
backend/core/database.py — Async SQLAlchemy 2.0 + asyncpg.

РОЛЬ У АРХІТЕКТУРІ:
    Цей файл — Database Layer. Надає:
    - engine: пул асинхронних з'єднань до PostgreSQL
    - AsyncSessionFactory: фабрика сесій для репозиторіїв
    - Base: базовий клас для всіх ORM-моделей
    - get_db(): FastAPI Depends() — видає сесію на час HTTP-запиту

ЧОМУ ASYNC ENGINE, А НЕ SYNC?
    FastAPI + uvicorn використовують asyncio Event Loop.
    Якщо виконати sync I/O (psycopg2) у async context:

        async def handler():
            users = db.query(User).all()  # SYNC! Блокує весь Event Loop
            # Поки чекаємо PostgreSQL — жоден інший запит не обробляється!

    asyncpg + AsyncSession → кожен await db.execute() звільняє Event Loop:

        async def handler():
            users = await db.execute(select(User))  # ASYNC! Не блокує
            # Поки чекаємо PostgreSQL — Event Loop обробляє інші запити

CONNECTION POOL (пул з'єднань):
    Відкрити з'єднання до PostgreSQL = ~5-20 мс (TCP handshake + auth).
    Якщо відкривати нове з'єднання на кожен запит — занадто повільно.

    Connection Pool вирішує: підтримує постійно відкриті з'єднання.

    pool_size=10:
        10 постійно відкритих з'єднань до PostgreSQL.
        Готові до роботи без затримки на підключення.
        Підходить для ~100-500 RPS залежно від складності запитів.

    max_overflow=20:
        При пікових навантаженнях — до 20 додаткових тимчасових з'єднань.
        Тобто максимум: 10 + 20 = 30 одночасних з'єднань.
        Тимчасові з'єднання закриваються після завершення запиту.

    pool_pre_ping=True:
        Перед видачею з'єднання з пулу — перевіряє чи воно "живе".
        PostgreSQL може закрити idle з'єднання (налаштування tcp_keepalive).
        Без pre_ping: отримаємо "застале" з'єднання → помилка в рантаймі.
        З pre_ping: SQLAlchemy видасть нове з'єднання замість застарілого.

    echo=settings.DEBUG:
        True → SQLAlchemy логує всі SQL-запити у stdout (для дебагу).
        False → тихий режим (production).

SESSION FACTORY:
    async_sessionmaker — фабрика що створює AsyncSession об'єкти.

    expire_on_commit=False:
        За замовчуванням True: після commit() всі атрибути об'єкта
        стають "expired" — при наступному зверненні SQLAlchemy робить SELECT.
        False: атрибути залишаються доступні після commit() без нового запиту.
        Чому False? У async context після commit сесія може бути вже закрита.

    autoflush=False:
        За замовчуванням True: перед кожним SELECT SQLAlchemy робить flush()
        (відправляє pending INSERT/UPDATE у БД).
        False: контролюємо flush() вручну у репозиторіях.
        Це важливо щоб не відправляти неповні дані у БД.

BASE CLASS:
    DeclarativeBase — базовий клас для всіх ORM-моделей.
    Зберігає registry моделей → Alembic автоматично бачить всі таблиці.

GET_DB():
    FastAPI Depends() pattern — видає сесію і автоматично закриває.

    Схема:
        Request → Depends(get_db) → видає session → Handler виконується
        → session.commit() → Handler повертає response → session.close()

    При помилці:
        Exception → session.rollback() → Exception піднімається далі
        → FastAPI повертає 500 → session.close()

    Ключова властивість: кожен HTTP-запит отримує СВОЮ окрему сесію.
    Транзакції не перемішуються між запитами.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.core.config import settings

# ── Engine (пул з'єднань до PostgreSQL) ────────────────────────────────────
# create_async_engine — створює asyncpg-based connection pool.
# DATABASE_URL формат: postgresql+asyncpg://user:pass@host:port/dbname
# "+asyncpg" — вказує SQLAlchemy використовувати asyncpg driver.
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,        # постійно відкриті з'єднання
    max_overflow=20,     # максимум тимчасових при перевантаженні
    pool_pre_ping=True,  # перевірка "живості" перед видачею з'єднання
    echo=settings.DEBUG, # логувати SQL у DEBUG режимі
)

# ── Session Factory ─────────────────────────────────────────────────────────
# async_sessionmaker — фабрика AsyncSession.
# Репозиторії приймають session і виконують запити через неї.
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # атрибути доступні після commit без нового SELECT
    autoflush=False,         # ручний контроль flush у репозиторіях
)


class Base(DeclarativeBase):
    """
    Базовий клас для всіх ORM-моделей.

    Всі моделі успадковують від Base:
        class User(Base):
            __tablename__ = "users"
            ...

    Base.metadata зберігає реєстр всіх таблиць.
    Alembic використовує Base.metadata для генерації міграцій:
        target_metadata = Base.metadata  (у migrations/env.py)
    """
    pass


async def get_db() -> AsyncSession:
    """
    FastAPI Depends() — генератор сесії для HTTP-запиту.

    Використання у handlers:
        @router.get("/users")
        async def list_users(session: AsyncSession = Depends(get_db)):
            repo = UserRepository(session)
            return await repo.get_all()

    Або через проміжну dep (backend/api/deps.py):
        async def get_session(session: AsyncSession = Depends(get_db)):
            return session

    Схема автоматичного управління транзакцією:

        HTTP Request
            │
            ▼
        async with AsyncSessionFactory() as session:
            │
            ├── try:
            │     yield session          ← Handler виконується тут
            │     await session.commit() ← Успішно: зберігаємо зміни
            │
            └── except:
                  await session.rollback() ← Помилка: відкочуємо зміни
                  raise                    ← FastAPI повертає 500

    Після виходу з async with: session.close() викликається автоматично.

    Важливо: yield робить цей async def — генератором.
    FastAPI викликає його як dependency injection.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
