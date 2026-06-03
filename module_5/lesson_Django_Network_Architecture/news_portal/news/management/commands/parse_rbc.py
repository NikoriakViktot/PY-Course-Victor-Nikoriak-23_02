"""
parse_rbc.py — Management command для парсингу новин з rbc.ua.

РОЛЬ У АРХІТЕКТУРІ:
    Management command = кастомна CLI-команда Django.
    Запуск: python manage.py parse_rbc
    Опційно: python manage.py parse_rbc --limit 50 --publish

    Django автоматично знаходить цю команду тому що:
    1. Файл знаходиться в news/management/commands/
    2. Клас називається Command і наслідує BaseCommand
    3. Ім'я файлу = ім'я команди ('parse_rbc')

ЩО РОБИТЬ ЦЯ КОМАНДА:
    1. Завантажує HTML-сторінки rbc.ua (requests)
    2. Парсить заголовки і посилання (BeautifulSoup)
    3. Визначає категорію з URL (map словник)
    4. Зберігає нові статті в PostgreSQL (Django ORM)
       - Перевіряє дублікати по source_url
       - Автоматично створює категорії якщо вони не існують

СТРУКТУРА:
    Command
      ├── add_arguments()     ← аргументи командного рядка
      ├── handle()            ← точка входу команди
      ├── _fetch_page()       ← HTTP-запит + HTML
      ├── _parse_page()       ← HTML → список словників
      └── _save_articles()    ← запис в БД

АНАЛОГІЯ: Журналіст-кур'єр — обходить сайти, збирає новини,
          несе до редакції (БД) і реєструє їх.
"""

import re
import time

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from news.models import Article, Category


# ── Константи ──────────────────────────────────────────────────────────────────

# User-Agent щоб сервер не блокував запит як бота
# (освітній бот — вказуємо чесно)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; EduScraper/1.0; +educational)',
    'Accept-Language': 'uk,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml',
}

# Список сторінок rbc.ua для парсингу
PAGES = [
    'https://www.rbc.ua/',
    'https://www.rbc.ua/rus/news/',
    'https://www.rbc.ua/rus/economic/',
    'https://www.rbc.ua/rus/politics/',
    'https://www.rbc.ua/rus/society/',
    'https://www.rbc.ua/ukr/news/',
    'https://www.rbc.ua/ukr/economic/',
]

# Словник відповідності slug-секції URL → назва категорії в БД
CATEGORY_MAP = {
    'news':       'Новини',
    'economic':   'Економіка',
    'economics':  'Економіка',
    'politics':   'Політика',
    'society':    'Суспільство',
    'sport':      'Спорт',
    'world':      'Світ',
    'technology': 'Технології',
}


# ── Клас команди ───────────────────────────────────────────────────────────────

class Command(BaseCommand):
    """
    Django management command: python manage.py parse_rbc

    BaseCommand надає:
        self.stdout.write()   → виведення в консоль
        self.style.SUCCESS()  → зелений текст
        self.style.ERROR()    → червоний текст
        self.style.WARNING()  → жовтий текст
    """

    # Опис команди — відображається при: python manage.py parse_rbc --help
    help = 'Парсить новини з rbc.ua і зберігає в базу даних'

    def add_arguments(self, parser):
        """
        Визначає аргументи командного рядка.

        python manage.py parse_rbc --limit 30 --publish
        """

        # --limit: максимальна кількість статей для збереження
        # type=int → Django конвертує рядок в int автоматично
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Максимальна кількість статей (за замовчуванням: 100)'
        )

        # --publish: одразу публікувати статті (без ручної модерації)
        # action='store_true' → якщо прапор є → True, немає → False
        parser.add_argument(
            '--publish',
            action='store_true',
            default=False,
            help='Одразу публікувати статті (без модерації)'
        )

    def handle(self, *args, **options):
        """
        Точка входу команди. Django викликає цей метод при запуску.

        options['limit']   → значення --limit аргументу
        options['publish'] → True якщо передано --publish
        """
        limit = options['limit']
        publish = options['publish']

        self.stdout.write(
            self.style.SUCCESS(f'Починаємо парсинг rbc.ua...')
        )
        self.stdout.write(f'Ліміт: {limit} статей | Автопублікація: {publish}')
        self.stdout.write('─' * 50)

        # Збираємо всі статті з усіх сторінок
        all_items = []

        for page_url in PAGES:
            self.stdout.write(f'Завантаження: {page_url}')

            # Завантажуємо HTML сторінки
            html = self._fetch_page(page_url)
            if html is None:
                # _fetch_page() повернула None → помилка (вже виведена)
                continue

            # Парсимо HTML → список словників з даними статей
            items = self._parse_page(html, page_url)
            self.stdout.write(f'  Знайдено: {len(items)} новин')
            all_items.extend(items)

            # Невелика пауза між запитами — щоб не перевантажувати сервер
            time.sleep(0.5)

        # Видаляємо дублікати по URL (одна новина може з'явитись на кількох сторінках)
        unique_items = self._deduplicate(all_items)
        self.stdout.write(f'\nВсього унікальних новин: {len(unique_items)}')

        # Обмежуємо кількість якщо потрібно
        if limit:
            unique_items = unique_items[:limit]

        # Зберігаємо в БД
        saved, skipped = self._save_articles(unique_items, publish=publish)

        # Підсумок
        self.stdout.write('─' * 50)
        self.stdout.write(
            self.style.SUCCESS(
                f'Готово! Збережено: {saved} | Пропущено (дублікати): {skipped}'
            )
        )

    # ── Приватні методи ────────────────────────────────────────────────────────

    def _fetch_page(self, url: str) -> str | None:
        """
        Завантажує HTML сторінки по URL.

        Повертає: HTML рядок або None якщо помилка.
        timeout=15 → максимум 15 секунд очікування відповіді.
        """
        try:
            # requests.get() — синхронний HTTP GET запит
            # Це блокуючий виклик: Python чекає поки сервер відповість
            response = requests.get(url, headers=HEADERS, timeout=15)

            # raise_for_status() → піднімає виняток якщо HTTP статус 4xx або 5xx
            # Наприклад: 403 Forbidden, 404 Not Found, 500 Server Error
            response.raise_for_status()

            # Явно встановлюємо UTF-8 кодування (rbc.ua може повертати помилкове)
            response.encoding = 'utf-8'
            return response.text

        except requests.exceptions.Timeout:
            self.stdout.write(
                self.style.WARNING(f'  Тайм-аут: {url}')
            )
            return None

        except requests.exceptions.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'  Помилка запиту: {url} → {e}')
            )
            return None

    def _parse_page(self, html: str, base_url: str) -> list[dict]:
        """
        Парсить HTML сторінки rbc.ua і витягує дані новин.

        Аргументи:
            html     — HTML-рядок сторінки
            base_url — URL сторінки (для визначення категорії)

        Повертає список словників:
            [{'title': '...', 'url': '...', 'category_name': '...', 'source_name': '...'}, ...]

        СТРУКТУРА rbc.ua (2024+):
            <div class="newsline">
                <div class="item">
                    <a href="/ukr/news/12345.html">19:45Заголовок</a>
                </div>
            </div>
        """
        # BeautifulSoup парсить HTML рядок у дерево об'єктів
        # 'lxml' — швидкий C-бібліотечний парсер (краще ніж вбудований html.parser)
        soup = BeautifulSoup(html, 'lxml')
        items = []

        # ── Пошук контейнерів новин ────────────────────────────────────────────
        # rbc.ua може змінювати CSS-класи, тому пробуємо кілька варіантів

        # Список пар (тег HTML, CSS-клас) для пошуку
        selectors = [
            ('div', 'newsline__item'),
            ('li',  'newsline__item'),
            ('div', 'news-feed__item'),
            ('div', 'news-item'),
            ('article', 'news-item'),
        ]

        containers = []
        for tag, css_class in selectors:
            found = soup.find_all(tag, class_=css_class)
            if found:
                containers = found
                break  # Знайшли → зупиняємось

        if not containers:
            # Фолбек: rbc.ua 2024+ використовує div.item всередині div.newsline
            containers = soup.find_all('div', class_='item')

        if not containers:
            # Останній фолбек: будь-які article теги або div з 'news' в класі
            containers = (
                soup.find_all('article') or
                soup.find_all('div', class_=re.compile(r'news|article'))
            )

        # ── Обробка кожного контейнера ─────────────────────────────────────────
        for container in containers:
            # Шукаємо тег <a href="..."> всередині контейнера
            link = container.find('a', href=True)
            if not link:
                continue  # Немає посилання → пропускаємо

            # Отримуємо текст посилання (без HTML тегів)
            raw_text = link.get_text(strip=True)

            # ── Обробка формату rbc.ua: "19:45Заголовок новини" ────────────────
            # Часто час зліплений із заголовком без пробілу
            # Regex: ^\d{2}:\d{2} → перевіряємо чи є "ЧЧ:ХХ" на початку
            if re.match(r'^\d{2}:\d{2}', raw_text):
                # Відрізаємо перші 5 символів часу ("19:45")
                title = raw_text[5:].strip()
            else:
                title = raw_text

            # Пропускаємо занадто короткі тексти (навігаційні посилання, кнопки)
            if len(title) < 10:
                continue

            # ── Нормалізація URL ───────────────────────────────────────────────
            url = link.get('href', '')

            if not url:
                continue  # Немає href → пропускаємо

            # Відносні URL перетворюємо в абсолютні
            # '/ukr/news/12345.html' → 'https://www.rbc.ua/ukr/news/12345.html'
            if url.startswith('/'):
                url = 'https://www.rbc.ua' + url
            elif not url.startswith('http'):
                continue  # Якийсь інший формат — пропускаємо

            # ── Визначення категорії з URL ─────────────────────────────────────
            # URL: 'https://www.rbc.ua/ukr/news/12345.html'
            # Після видалення домену: '/ukr/news/12345.html'
            # Частини: ['ukr', 'news', '12345.html']
            url_path = url.replace('https://www.rbc.ua', '')
            url_parts = [p for p in url_path.split('/') if p]

            # Категорія — зазвичай другий сегмент URL (індекс 1)
            # 'ukr/news' → url_parts[1] = 'news'
            # 'rus/economic' → url_parts[1] = 'economic'
            raw_category = ''
            if len(url_parts) > 1:
                raw_category = url_parts[1]
            elif len(url_parts) > 0:
                raw_category = url_parts[0]

            # Перекладаємо slug → людську назву по словнику
            category_name = CATEGORY_MAP.get(
                raw_category,
                raw_category.capitalize() if raw_category else 'Загальні'
            )

            items.append({
                'title': title,
                'url': url,
                'category_name': category_name,
                'source_name': 'rbc.ua',
            })

        return items

    def _deduplicate(self, items: list[dict]) -> list[dict]:
        """
        Видаляє дублікати зі списку — одна URL може з'явитись на кількох сторінках.

        Зберігає порядок (перше входження URL залишається).
        """
        seen_urls = set()  # set → O(1) пошук (швидше ніж list)
        unique = []

        for item in items:
            if item['url'] not in seen_urls:
                seen_urls.add(item['url'])
                unique.append(item)

        return unique

    def _save_articles(self, items: list[dict], publish: bool = False) -> tuple[int, int]:
        """
        Зберігає спарсені статті в PostgreSQL.

        Повертає: (кількість_збережених, кількість_пропущених_дублікатів)

        СТРАТЕГІЯ: get_or_create() для уникнення дублікатів
            - Якщо стаття з таким URL вже є → пропускаємо
            - Якщо нема → створюємо нову

        ТРАНЗАКЦІЯ: весь процес загорнуто в atomic()
            - Якщо щось пішло не так → всі зміни відкочуються
            - Або все зберігається, або нічого
        """
        saved = 0
        skipped = 0

        # Кеш категорій: {'Економіка': <Category obj>, ...}
        # Щоб не робити SELECT запит для КОЖНОЇ статті — завантажуємо всі категорії один раз
        category_cache: dict[str, Category] = {}

        # transaction.atomic() → атомарна транзакція
        # Якщо виникне виняток — всі зміни в БД відкотяться автоматично
        with transaction.atomic():
            for item in items:
                # ── Отримуємо або створюємо категорію ─────────────────────────
                category_name = item['category_name']

                if category_name not in category_cache:
                    # get_or_create() → один SQL запит:
                    #   SELECT ... WHERE name=? LIMIT 1
                    #   Якщо не знайдено: INSERT INTO ...
                    # Повертає (об'єкт, created_bool)
                    category, created = Category.objects.get_or_create(
                        name=category_name
                    )
                    category_cache[category_name] = category

                    if created:
                        self.stdout.write(
                            f'  Нова категорія: {category_name}'
                        )

                category = category_cache[category_name]

                # ── Перевіряємо чи стаття вже є в БД ─────────────────────────
                # exists() → SELECT 1 FROM ... LIMIT 1 — найефективніший спосіб перевірки
                if Article.objects.filter(source_url=item['url']).exists():
                    skipped += 1
                    continue  # Дублікат → пропускаємо

                # ── Зберігаємо нову статтю ─────────────────────────────────────
                Article.objects.create(
                    title=item['title'],
                    source_url=item['url'],
                    source_name=item['source_name'],
                    category=category,
                    content='',            # Контент порожній — парсимо тільки заголовки
                    is_published=publish,  # True якщо --publish, False (чернетка) за замовчуванням
                )
                saved += 1

        return saved, skipped
