"""
app/services/user_service.py — Сервіс для відстеження користувачів.

РОЛЬ У АРХІТЕКТУРІ:
    Service Layer містить бізнес-логіку, яка не залежить від Telegram.
    Handler (start.py) не знає ЯК відстежуються користувачі —
    він просто викликає register_user() і отримує результат.

    Це патерн розподілу відповідальностей (Separation of Concerns):
        Handler   → Telegram I/O (приймати/відправляти повідомлення)
        Service   → Бізнес-логіка (хто є новим? скільки всього?)
        Repository → Зберігання (де і як зберігати)

ПОТОЧНА РЕАЛІЗАЦІЯ (In-Memory):
    Використовуємо Python set() для зберігання ID користувачів у пам'яті.

    ✅ Переваги:
        - Нуль залежностей (не потрібен Redis/PostgreSQL)
        - Блискавично швидко (O(1) для in/add операцій)
        - Ідеально для навчального бота

    ❌ Обмеження:
        - Скидається при кожному рестарті бота
        - Не масштабується (лише один процес бачить ці дані)
        - Не підходить для production

PRODUCTION ВАРІАНТ:
    Замінити на PostgreSQL репозиторій:

        class UserRepository:
            def __init__(self, db: AsyncSession):
                self._db = db

            async def register(self, user_id: int, username: str | None) -> bool:
                existing = await self._db.get(User, user_id)
                if existing:
                    return False  # вже існує
                self._db.add(User(id=user_id, username=username))
                await self._db.commit()
                return True  # новий

    Handler при цьому НЕ зміниться — він досі викликає register_user().
    Тільки реалізація всередині сервісу змінюється.
    Це і є суть Dependency Inversion.

ЧОМУ SET, А НЕ LIST:
    list: user_id in _seen_users → O(n) — лінійний пошук
    set:  user_id in _seen_users → O(1) — хеш-таблиця

    При мільйоні користувачів різниця відчутна.
    set.add() — O(1), автоматично дедуплікує (повторне add не додає дублікат).
"""
import logging

# Logger для цього сервісу
# У логах: "app.services.user_service | INFO | ..."
logger = logging.getLogger(__name__)

# =========================================================
# IN-MEMORY СХОВИЩЕ
# =========================================================
# _seen_users — множина (set) Telegram user_id, яких бот вже бачив.
#
# Починається з порожнього set() при кожному старті бота.
# Зберігається лише в пам'яті процесу — не персистентне.
#
# Підкреслення _ на початку — Python конвенція:
# "приватна" змінна модуля, не призначена для прямого доступу ззовні.
# Інші модулі мають взаємодіяти через функції register_user() та get_total_users().
_seen_users: set[int] = set()


def register_user(user_id: int, username: str | None) -> bool:
    """
    Реєструє користувача і повертає чи він новий.

    Параметри:
        user_id  — Telegram user ID (унікальний int, до 10 цифр)
        username — Telegram username (може бути None, якщо не встановлено)

    Повертає:
        True  — якщо користувач зустрівся ВПЕРШЕ (новий)
        False — якщо вже був раніше (зустрічався у цій сесії)

    Логіка:
        1. Перевіряємо: user_id є у _seen_users?
        2. Якщо НІ → новий користувач:
               Додаємо у set
               Логуємо подію
               Повертаємо True
        3. Якщо ТАК → вже відомий:
               Нічого не робимо
               Повертаємо False

    Використання у handler (start.py):
        is_new = register_user(user.id, user.username)
        if is_new:
            # Відповісти особливим привітанням для нового користувача
            total = get_total_users()
            # "Ти наш 42-й користувач!"

    Чому bool, а не None?
        Явний True/False чіткіше виражає намір.
        Handler може виконати різну логіку залежно від результату.
    """
    # Перевіряємо чи user_id вже у нашій множині
    # `in` для set — O(1) за рахунок хеш-таблиці
    is_new = user_id not in _seen_users

    if is_new:
        # Додаємо нового користувача у множину
        # set.add() ігнорує дублікати — але тут is_new вже гарантує унікальність
        _seen_users.add(user_id)

        # Логуємо тільки нових — щоб не "засмічувати" логи повторними запитами
        # username може бути None (у Telegram username необов'язковий)
        logger.info("Новий користувач: id=%s username=%s", user_id, username)

    return is_new


def get_total_users() -> int:
    """
    Повертає загальну кількість унікальних користувачів.

    Рахує кількість елементів у _seen_users.
    len() для set — O(1) (розмір зберігається як атрибут).

    Обмеження: рахує лише користувачів ПОТОЧНОЇ сесії.
    При рестарті бота лічильник обнуляється.

    У production потрібен SELECT COUNT(*) FROM users у БД.
    """
    return len(_seen_users)
