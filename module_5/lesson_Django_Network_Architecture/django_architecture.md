# Django Architecture — від запиту до відповіді

> Django — це не просто "фреймворк". Це частина мережевого стеку.
> Цей документ — загальний огляд Django-архітектури. Для детального вивчення кожного компонента дивись розширену документацію нижче.

---

## Навігація по документації

| Тема | Файл | Що всередині |
|------|------|--------------|
| Мережевий фундамент | [network_foundation.md](network_foundation.md) | IP, DNS, TCP, HTTP, HTTPS, sockets, REST |
| Мережеві схеми | [network_mermaid.md](network_mermaid.md) | 11 Mermaid-діаграм мережевого стеку |
| Структура проєкту | [DJANGO_PROJECT_STRUCTURE.md](DJANGO_PROJECT_STRUCTURE.md) | Кожен файл Django з роллю та помилками |
| Команди Django | [DJANGO_COMMAND_SYSTEM.md](DJANGO_COMMAND_SYSTEM.md) | Таблиця всіх команд + lifecycle |
| Міграції | [DJANGO_MIGRATIONS.md](DJANGO_MIGRATIONS.md) | makemigrations, migrate, граф залежностей |
| ORM та БД | [Django_ORM.md](Django_ORM.md) | QuerySet API, N+1, транзакції, MVCC |
| URL Routing | [Django_URL_Routing.md](Django_URL_Routing.md) | path(), include(), GET/POST, Forms |
| Views | [Django_Views.md](Django_Views.md) | FBV, CBV, Generic Views, lifecycle |
| Templates | [Django_Templates.md](Django_Templates.md) | DTL, context, security, inheritance |
| Django схеми | [django_mermaid.md](django_mermaid.md) | 15 Mermaid-діаграм архітектури Django |
| **Services** | [DJANGO_SERVICES.md](DJANGO_SERVICES.md) | Бізнес-логіка: stateless функції, транзакції, on_commit |
| **Selectors** | [DJANGO_SELECTORS.md](DJANGO_SELECTORS.md) | Читання даних: named queries, N+1, CQRS-light |
| **Serializers** | [DJANGO_SERIALIZERS.md](DJANGO_SERIALIZERS.md) | Transport layer: InputSerializer, OutputSerializer |
| **Tasks** | [DJANGO_TASKS.md](DJANGO_TASKS.md) | Celery: broker, retry, on_commit, ідемпотентність |
| Повна картина | [DJANGO_SERVICES_SELECTORS.md](DJANGO_SERVICES_SELECTORS.md) | Services + Selectors + Serializers разом |

---

## 1. Що таке Django і чому це framework

**Framework** — це не бібліотека. Бібліотека дає тобі інструменти, які ти викликаєш.
Framework **викликає твій код** за встановленими правилами (Inversion of Control).

Django надає:
- готову обробку HTTP-запитів
- ORM для роботи з базою даних
- систему аутентифікації
- адмін-панель з коробки
- захист від XSS, CSRF, SQL injection
- систему міграцій

Ти пишеш: **models** (схема БД), **views** (HTTP-оркестрація), **templates** (HTML), **services** (бізнес-логіка), **selectors** (читання даних). Всю решту Django робить сам.

### Django vs Flask vs FastAPI

| Параметр | Django | Flask | FastAPI |
|----------|--------|-------|---------|
| Розмір | Великий | Мікро | Середній |
| Батарейки | Включені (ORM, auth, admin) | Мінімум | Залежності |
| Async | Django 3.1+ (частково) | Quart | Нативно |
| Швидкість розробки | Висока | Середня | Висока |
| Підходить для | Повноцінні веб-додатки | Мікросервіси | API-сервіси |

---

## 2. MVT архітектура

Django використовує **MVT (Model-View-Template)** — варіант класичного MVC.

| Компонент | Роль | Аналог MVC |
|-----------|------|-----------|
| **Model** | Схема БД, відносини, ORM — без бізнес-логіки | Model |
| **View** | HTTP-оркестратор: валідує запит, делегує в service/selector, повертає Response | Controller |
| **Template** | HTML-шаблон для рендерингу | View |

> **У production-архітектурі** бізнес-логіка живе в `services.py`, читання — у `selectors.py`. MVT описує стандартний Django; для API-backend зазвичай Templates замінюються на DRF Serializers.

> **Ключова ідея:** View — це не "візуальний інтерфейс". View — це Python-функція або клас, що обробляє запит.

### Чому не MVC?

У Django "View" відповідає за логіку (як Controller у MVC), а "Template" відповідає за представлення (як View у MVC). Назви різні, суть та сама.

---

## 3. Структура Django-проєкту

```
myproject/                    ← корінь проєкту
├── manage.py                 ← CLI інструмент
├── myproject/                ← пакет конфігурації
│   ├── __init__.py
│   ├── settings.py           ← всі налаштування
│   ├── urls.py               ← кореневий URL-роутер
│   ├── wsgi.py               ← WSGI entry point
│   └── asgi.py               ← ASGI entry point
└── myapp/                    ← Django-застосунок (bounded context)
    ├── models.py             ← Схема БД (тільки структура, без бізнес-логіки)
    ├── services.py           ← Бізнес-логіка (мутації, транзакції, side effects)
    ├── selectors.py          ← Читання даних (named queries, ORM-оптимізації)
    ├── serializers.py        ← Transport layer (InputSerializer, OutputSerializer)
    ├── views.py              ← HTTP-оркестратор (тонкий, делегує у services/selectors)
    ├── urls.py               ← URL-маршрути застосунку
    ├── tasks.py              ← Celery tasks (транспорт, не логіка)
    ├── filters.py            ← django-filter
    ├── permissions.py        ← DRF permissions
    ├── admin.py              ← реєстрація моделей в адмін
    ├── apps.py               ← конфіг застосунку
    ├── templates/            ← HTML-шаблони (для SSR)
    ├── static/               ← CSS, JS, зображення
    ├── tests/                ← тести
    └── migrations/           ← файли міграцій БД
```

---

## 4. Django Request Lifecycle — крок за кроком

Ось що відбувається, коли запит `GET /books/42/` досягає Django:

### Крок 1: WSGI/ASGI отримує запит

Nginx передає HTTP-байти в uWSGI або Gunicorn. Сервер перетворює їх у Python-словник:

```python
# WSGI environ — що отримує Django
{
    'REQUEST_METHOD': 'GET',
    'PATH_INFO': '/books/42/',
    'HTTP_HOST': 'example.com',
    'HTTP_COOKIE': 'sessionid=abc123',
    'wsgi.input': <BytesIO>,  # тіло запиту
    ...
}
```

### Крок 2: Middleware (вхідний шлях — зверху вниз)

Уявіть, що міделвер (middleware) — це **серія пропускних пунктів** (або шарів), які послідовно проходить кожен запит від користувача перед тим, як потрапити до вашої основної програми.

Порядок цих пунктів має критичне значення, оскільки один пункт зазвичай залежить від результатів роботи попереднього.

Ось як це працює:
1. **`SessionMiddleware`** — це ніби охоронець, який перевіряє користувача і дістає його "ідентифікаційний номерок" (дані сесії).
2. **`AuthenticationMiddleware`** — це адміністратор, який бере цей номерок, шукає його в базі і визначає, **хто саме** до нас прийшов (авторизує користувача).

Якщо адміністратор (`AuthenticationMiddleware`) спробує розпізнати користувача *до того*, як охоронець (`SessionMiddleware`) видасть йому номерок, він просто не знатиме, кого шукати. Тому робота з сесіями завжди має стояти вище у списку.

Це налаштовується у головному файлі конфігурації вашого проєкту — `settings.py`. У цьому файлі є спеціальний список під назвою `MIDDLEWARE`. Щоб додати, видалити або змінити порядок міделверів, ви просто редагуєте цей список, розміщуючи текстові шляхи до них у потрібній послідовності зверху вниз.

```python
# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',      # HTTPS redirect, HSTS
    'django.contrib.sessions.middleware.SessionMiddleware', # читає session cookie
    'django.middleware.common.CommonMiddleware',           # нормалізує URL
    'django.middleware.csrf.CsrfViewMiddleware',           # CSRF захист
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # request.user
    'django.contrib.messages.middleware.MessageMiddleware',
]
```

Кожен middleware отримує `request`, може його змінити або повернути `HttpResponse` одразу (перервати ланцюг). Порядок **критичний**: `AuthenticationMiddleware` повинен іти ПІСЛЯ `SessionMiddleware`, бо читає дані сесії.

### Крок 3: URL Dispatcher

Уявіть, що **URL Dispatcher (маршрутизатор)** — це **головне відділення сортування пошти**.

Коли користувач вводить адресу (наприклад, `/books/42/`), цей "лист" (запит) проходить такі етапи сортування:

1. **Головний центр (`include`)**: Спочатку запит потрапляє у ваш головний файл `myproject/urls.py`. "Сортувальник" бачить частину `books/` і каже: "Ага, це до відділу книг!", перенаправляючи запит для подальшої обробки у файл `books.urls`.
2. **Відділ книг (`<int:pk>`)**: Файл `books.urls` дивиться на залишок адреси — `42/`. Вираз `<int:pk>` працює як розумний сканер: він розуміє, що `42` — це числове значення (первинний ключ або ID книги), "захоплює" його і передає безпосередньо функції `BookDetailView`, щоб вона дістала з бази даних саме 42-гу книгу.

**Чому порядок такий важливий?**
Маршрутизатор читає ваш список `urlpatterns` суворо зверху вниз і припиняє пошук на **першому ж збігу**, який відповідає правилу. Якщо він доходить до кінця списку і жоден рядок не підійшов, він повертає відповідь `404 Not Found` (сторінка не знайдена).


```python
# myproject/urls.py
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('books/', include('books.urls')),
]

# books/urls.py
urlpatterns = [
    path('', BookListView.as_view(), name='book-list'),
    path('<int:pk>/', BookDetailView.as_view(), name='book-detail'),  # ← pk=42
]
```

Django перебирає `urlpatterns` зверху вниз. Перший збіг — виклик відповідного View. Якщо збігів немає — `404 Not Found`.

> **Увага:** Django не шукає "найкращий" збіг — він бере **перший**.

### Крок 4: View — серце логіки

Уявіть, що **View (представлення)** — це **шеф-кухар** у ресторані, який отримав ваше замовлення від диспетчера.

Ось що відбувається у цьому коді крок за кроком:

1. **Отримання замовлення (`request, pk`):** "Кухар" отримує об'єкт запиту та конкретний номер потрібної книги (наприклад, 42), який щойно "захопив" і передав йому маршрутизатор.
2. **Звернення до бази даних (`get_object_or_404`):** Функція просить ORM знайти книгу №42 у базі даних. Якщо такої книги не існує, функція миттєво повертає помилку `404 Not Found` (Сторінка не знайдена) замість того, щоб зламати програму через відсутність даних.
3. **Формування відповіді (`render`):** Кухар бере знайдену книгу та інформацію про поточного користувача (яку на першому етапі дбайливо додав міделвер `AuthenticationMiddleware`). Він пакує їх у словник і передає HTML-шаблону (`detail.html`) для остаточного оформлення сторінки.

```python
# books/views.py
from django.shortcuts import render, get_object_or_404
from .models import Book

def book_detail(request, pk):
    # ORM: SELECT * FROM books_book WHERE id=42
    book = get_object_or_404(Book, pk=pk)
    
    # Template rendering
    return render(request, 'books/detail.html', {
        'book': book,
        'user': request.user,  # доданий AuthenticationMiddleware
    })
```

### Крок 5: ORM → База даних

Уявіть, що **ORM** — це ваш особистий **перекладач-асистент**.

Ви даєте йому вказівку простою мовою Python (`Book.objects.get(pk=42)`), а він миттєво перекладає її на мову бази даних — SQL.

Ось як це працює зсередини:
1. **`Book.objects`** — ви звертаєтесь до бази даних, саме до таблиці з книгами.
2. **`get(...)`** — ви даєте команду знайти суворо *тільки один* конкретний запис.
3. **`pk=42`** — `pk` означає "primary key" (первинний ключ). ORM розуміє, що треба шукати книгу, у якої унікальний ідентифікатор (`id`) дорівнює 42.

База даних знаходить потрібний рядок і віддає його назад. Далі ORM автоматично запаковує цей рядок у зручний Python-об'єкт `book`. Тепер ваш View має всі дані про книгу і може передати їх для відображення на сторінці.


```python
book = Book.objects.get(pk=42)
# Генерує: SELECT "books_book"."id", "books_book"."title", ... 
#           FROM "books_book" WHERE "books_book"."id" = 42 LIMIT 1
```

### Крок 6: Template рендеринг

Уявіть, що **Template (Шаблон)** — це **красиве сервірування страви** перед подачею клієнту.

View (шеф-кухар) передав сюди "сирі" дані (об'єкти `book` та `user`), а шаблонізатор просто підставляє їх у HTML-каркас. 

Ось що саме тут відбувається:

1. **`{{ book.title }}` (Змінні):** Подвійні фігурні дужки означають "виведи сюди дані". Django автоматично замінить це на реальну назву книги.
2. **`{{ book.author.name }}` та пастка "N+1":** Цей рядок звертається до пов'язаного об'єкта (автора). Якщо ваш View раніше не "витягнув" автора з бази разом із книгою (за допомогою оптимізації `select_related`), ця малесенька строчка змусить Django *непомітно зробити ще один окремий запит до бази даних*, щоб дізнатися його ім'я. Якщо ви виводите список зі 100 книг, Django зробить 100 зайвих запитів (це і є відома проблема "N+1").
3. **`{% if user.is_authenticated %}` (Теги логіки):** Це вбудована логіка шаблону. Він перевіряє статус користувача (так-так, того самого, якого розпізнав наш адміністратор `AuthenticationMiddleware` на першому кроці).
4. **`{% url 'add-to-cart' book.pk %}`:** Замість того, щоб жорстко прописувати посилання (наприклад, `/cart/add/42`), цей тег сам генерує правильний шлях на основі імені маршруту з вашого `urls.py`. Це захищає сайт: якщо ви колись зміните структуру адрес у налаштуваннях, усі посилання в шаблонах оновляться автоматично.

Після цього кроку повністю сформований HTML-код пакується у відповідь і відправляється назад у браузер користувача.


```html
<!-- books/templates/books/detail.html -->
<h1>{{ book.title }}</h1>
<p>Автор: {{ book.author.name }}</p>  {# УВАГА: це може бути N+1 запит! #}
{% if user.is_authenticated %}
    <a href="{% url 'add-to-cart' book.pk %}">Купити</a>
{% endif %}
```

Django Template Engine підставляє значення, автоматично екранує HTML (захист від XSS).

### Крок 7: Middleware (вихідний шлях — знизу вгору)
Уявіть, що наша готова страва (веб-сторінка) тепер повертається до клієнта. Вона має пройти через ті самі **пропускні пункти (міделвери), але вже у зворотному порядку**.

На цьому етапі міделвери діють як «служба пакування» перед остаточною відправкою:

1. **Пакують у вакуум (GZip):** Стискають готову сторінку, щоб вона передалася через інтернет набагато швидше.
2. **Чіпляють ярлики (`Content-Length`):** Рахують точний розмір сторінки та додають цей заголовок, щоб браузер користувача розумів, скільки саме даних йому потрібно завантажити.
3. **Ставлять печатку (Cookies/Session):** Якщо під час обробки запиту щось змінилося (наприклад, користувач авторизувався), міделвер закріплює ці зміни і просить браузер зберегти оновлені дані сесії або файли cookie.

Після проходження останнього міделвера (найвищого у списку) повністю сформована та запакована відповідь передається веб-серверу, який віддає її браузеру.

> Ось ми й пройшли весь життєвий цикл запиту в Django!

---

## 5. Models та ORM

Уявіть, що **Модель (Model)** — це креслення таблиці бази даних, а **ORM** — ваш особистий перекладач, який перетворює код Python на SQL-запити. Один клас дорівнює одній таблиці.

Ось що насправді відбувається під капотом вашого коду:

**1. Типи полів (Fields)**
Кожен атрибут класу — це колонка в таблиці бази даних.
*   `CharField` та `EmailField`: Створюють текстові колонки. `EmailField` додатково перевіряє, чи є текст валідною електронною поштою, а `unique=True` гарантує, що в базі не буде двох авторів з однаковим email.
*   `DateTimeField(auto_now_add=True)`: Django автоматично запише точний час і дату в момент створення запису, цей параметр не потрібно передавати вручну.
*   `DecimalField`: Спеціальне поле для фінансових даних (цін), яке зберігає точність математичних операцій, на відміну від звичайних дробів.

**2. Зв'язки між таблицями (ForeignKey)**
Рядок `author = models.ForeignKey(...)` створює зв'язок "один до багатьох" — один автор може мати багато книг.
*   `on_delete=models.CASCADE`: Захищає цілісність бази даних. Якщо ви видалите автора, Django автоматично (каскадно) видалить усі його книги, щоб вони не "зависли" без власника.
*   `related_name='books'`: Це магія зворотного пошуку. Завдяки цьому ви можете взяти об'єкт автора і написати `author.books.all()`, щоб миттєво отримати список усіх його творів.

**3. Метадані (Клас Meta)**
Клас `Meta` містить налаштування моделі, які не є полями таблиці.
*   `ordering = ['name']`: Вказує базі даних за замовчуванням завжди повертати список авторів відсортованим за алфавітом.
*   `db_table = 'library_authors'`: За замовчуванням Django назвав би таблицю `назвадодатку_author`. Цей параметр дозволяє жорстко задати власну назву таблиці безпосередньо в СУБД.

**4. Метод `__str__`**
Замість того, щоб в панелі адміністратора показувати системне та незрозуміле `<Author object (1)>`, цей метод вказує Django відображати об'єкт у зручному для людини вигляді — просто виводячи ім'я автора.

### Визначення моделі

```python
from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        db_table = 'library_authors'  # явна назва таблиці
    
    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=300)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')
    published = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
```

### ORM QuerySet API
Уявіть, що **QuerySet** — це розумний список інструкцій для бази даних, який Django збирає, але не виконує до останнього моменту. 

Ось глибокий розбір кожного етапу з вашого коду:

**1. CREATE (Створення)**
Метод `create()` — це зручний скорочений варіант. Замість того, щоб створювати об'єкт у пам'яті, а потім окремо викликати для нього `save()`, `create()` робить це за один крок, миттєво виконуючи SQL-команду `INSERT`.

**2. READ (Читання) та "Лінива" оцінка (Lazy Evaluation)**
Коли ви пишете `Book.objects.filter(...)`, Django взагалі не звертається до бази даних. QuerySets є "лінивими" (lazy): вони лише накопичують ваші фільтри та умови. Переклад у SQL і реальне звернення до бази (`SELECT`) відбувається лише тоді, коли ви починаєте перебирати результати, наприклад, у циклі `for book in books:`.

**3. Оптимізація та `select_related`**
За замовчуванням, якщо ви викличете `book.author.name` у циклі зі 100 книг, Django зробить 100 додаткових запитів, щоб знайти автора кожної книги (це відома проблема N+1). Метод `select_related('author')` вирішує це, використовуючи SQL-операцію `JOIN`. Він витягує і книгу, і її автора за один єдиний складний запит, значно підвищуючи продуктивність. Цей метод ідеально підходить для зв'язків за зовнішнім ключем (ForeignKey).

**4. UPDATE (Масове оновлення)**
Метод `update()` перетворюється безпосередньо на SQL-команду `UPDATE` і застосовується миттєво до всіх відфільтрованих записів. Це дуже ефективний підхід, оскільки Django оновлює дані напряму в базі і не завантажує ці об'єкти в оперативну пам'ять Python.

**5. DELETE (Видалення)**
Виклик `delete()` миттєво виконує SQL-запит `DELETE`. Важливий нюанс архітектури: якщо ви видаляєте об'єкт (наприклад, Автора), Django за замовчуванням використовує поведінку `CASCADE` і автоматично видаляє всі пов'язані з ним об'єкти (його Книги), щоб у базі не залишилося "осиротілих" даних.

**6. AGGREGATE (Агрегація)**
Замість того, щоб завантажувати всі книги в Python і рахувати середню ціну вручну циклом, `aggregate()` змушує саму базу даних (яка оптимізована для цього) виконати цю математику. На відміну від `filter()`, який повертає QuerySet, `aggregate()` є кінцевою (термінальною) операцією, яка одразу повертає звичайний Python-словник (dictionary) з обчисленими результатами.

```python
# CREATE
author = Author.objects.create(name="Frank Herbert", email="frank@dune.com")

# READ — lazy! База ще не запитана
books = Book.objects.filter(is_active=True)  
books = books.select_related('author')  # JOIN — уникає N+1

# База запитується тут (ітерація)
for book in books:
    print(f"{book.title} by {book.author.name}")  # author вже завантажений!

# UPDATE
Book.objects.filter(author=author).update(is_active=False)

# DELETE
Book.objects.get(pk=42).delete()

# AGGREGATE
from django.db.models import Avg, Count
stats = Book.objects.aggregate(avg_price=Avg('price'), total=Count('id'))
```

### N+1 проблема — найчастіша помилка ORM

```python
# ПОГАНО: N+1 queries — 1 запит на книги + N запитів на авторів
books = Book.objects.all()
for book in books:
    print(book.author.name)  # кожен раз — SQL запит!

# ДОБРЕ: 2 запити (JOIN або IN)
books = Book.objects.select_related('author').all()  # для ForeignKey
books = Book.objects.prefetch_related('tags').all()  # для ManyToMany
```

---

## 6. Middleware — цибулина запиту

### Як написати власний middleware

```python
class LoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # --- ДО View ---
        print(f"→ {request.method} {request.path}")
        
        response = self.get_response(request)  # весь Django всередині
        
        # --- ПІСЛЯ View ---
        print(f"← {response.status_code}")
        response['X-Processing-Time'] = '42ms'
        
        return response
```

### Де middleware корисний

| Задача | Middleware |
|--------|------------|
| Rate limiting (захист від DDoS) | Власний або `django-ratelimit` |
| JWT автентифікація | Власний + `djangorestframework-simplejwt` |
| Логування запитів | Власний або `django-request` |
| CORS заголовки | `django-cors-headers` |
| Компресія GZip | `GZipMiddleware` (вбудований) |

---

## 7. Authentication та Sessions

### Як Django зберігає сесію

1. Після логіну Django створює запис у таблиці `django_session`:
   ```
   session_key: "abc123xyz"
   session_data: {base64-encoded: {"_auth_user_id": "42", "_auth_user_backend": "..."}}
   expire_date: 2025-06-01 10:00:00
   ```
2. Відправляє клієнту cookie: `Set-Cookie: sessionid=abc123xyz; HttpOnly; Secure`
3. При наступних запитах `SessionMiddleware` читає `sessionid` з cookie
4. `AuthenticationMiddleware` завантажує юзера: `request.user = User.objects.get(id=42)`

### Login/Logout

```python
from django.contrib.auth import authenticate, login, logout

def login_view(request):
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user:
            login(request, user)           # створює сесію
            return redirect('dashboard')
        return render(request, 'login.html', {'error': 'Невірні дані'})
    return render(request, 'login.html')

def logout_view(request):
    logout(request)                        # видаляє сесію з БД
    return redirect('home')
```

### Захист view від анонімних користувачів

```python
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

@login_required                    # → перенаправляє на /accounts/login/
def my_profile(request):
    return render(request, 'profile.html')

class DashboardView(LoginRequiredMixin, View):
    login_url = '/login/'
    def get(self, request):
        return render(request, 'dashboard.html')
```

---

## 8. WSGI vs ASGI

### WSGI (синхронний, традиційний)

```
Браузер → Nginx → Gunicorn (8 workers) → Django WSGI App
```

- Кожен worker — окремий Python-процес
- Worker обробляє 1 запит одночасно
- Якщо view робить `time.sleep(5)` — worker заблокований на 5 секунд
- 8 workers = максимум 8 одночасних запитів

```python
# wsgi.py
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
application = get_wsgi_application()
```

### ASGI (асинхронний, сучасний)

```
Браузер → Nginx → Uvicorn (8 workers з event loop) → Django ASGI App
```

- Кожен worker — event loop (asyncio)
- Worker може обробляти **тисячі** одночасних з'єднань
- Під час `await db.query()` worker обробляє інші запити
- Підтримка WebSockets, Server-Sent Events

```python
# asgi.py
import os
from django.core.asgi import get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
application = get_asgi_application()
```

```python
# Async view (Django 3.1+)
from django.http import JsonResponse
import asyncio

async def async_view(request):
    await asyncio.sleep(1)         # не блокує сервер!
    return JsonResponse({'status': 'ok'})
```

### Коли що використовувати

| Сценарій | Рекомендація |
|----------|-------------|
| Традиційний веб-сайт | WSGI + Gunicorn |
| REST API (багато запитів) | ASGI + Uvicorn |
| WebSockets (чат, real-time) | ASGI + Django Channels |
| Міксований (і те, і інше) | Gunicorn + Uvicorn workers |

---

## 9. Migrations — еволюція схеми БД

Уявіть, що **Міграції** — це **система контролю версій (як Git), але для вашої бази даних**.

Django не вимагає від вас писати SQL-запити вручну для створення чи зміни таблиць. Замість цього ви змінюєте Python-класи (моделі), а Django бере на себе всю роботу з базою даних.

Ось як виглядає повний робочий цикл:

**1. Зміна коду (models.py)**
Ви додаєте, видаляєте або змінюєте поля у ваших моделях. 

**2. Фіксація змін (`makemigrations`)**
Команда `python manage.py makemigrations` сканує ваші моделі, знаходить зміни і створює новий файл міграції (наприклад, `0002_book_add_isbn.py`). Цей файл — це просто "креслення" або запис того, *що саме* змінилося. Сама база даних на цьому етапі ще не зачеплена.

**3. Застосування змін (`migrate`)**
Команда `python manage.py migrate` читає ці створені креслення і виконує реальні SQL-команди, щоб змінити структуру бази даних (створити нову колонку, таблицю тощо). Django веде спеціальну службову таблицю (`django_migrations`), щоб пам'ятати, які міграції вже застосовані, а які — ні.

**Додаткові корисні команди:**

*   **`python manage.py showmigrations`**: Показує список усіх існуючих міграцій у вашому проекті. Ті, що вже були успішно застосовані до бази даних, позначаються хрестиком `[X]`.
*   **`python manage.py sqlmigrate назва_додатку номер_міграції`**: Показує "сирий" SQL-код, який Django планує виконати. Ця команда нічого не змінює в базі, але дуже корисна, якщо ви хочете перевірити, що саме відбудеться під капотом.



```bash
# Після зміни models.py — генерує файл міграції
python manage.py makemigrations

# Застосовує міграції до БД
python manage.py migrate

# Перегляд SQL що буде виконано
python manage.py sqlmigrate myapp 0002
```

**Файл міграції** — Python-код, що описує зміни схеми:

```python
# migrations/0002_book_add_isbn.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('books', '0001_initial')]
    
    operations = [
        migrations.AddField(
            model_name='book',
            name='isbn',
            field=models.CharField(max_length=13, blank=True),
        ),
    ]
```

> Ніколи не редагуй файли міграцій вручну якщо вони вже застосовані до продакшн-БД.

**Чому не можна редагувати застосовані файли міграцій?**
Оскільки Django чітко відстежує історію, ручне втручання у старі файли призведе до того, що реальна структура бази даних розсинхронізується з вашим Python-кодом, і наступні спроби оновити базу даних будуть видавати помилки.

---

## 10. Static Files та Media

```python
# settings.py
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'   # куди collectstatic збирає файли
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'          # де зберігаються uploaded файли
```

```bash
# Збирає всі static з додатків в STATIC_ROOT (для продакшну)
python manage.py collectstatic
```

**Продакшн:** Nginx роздає static напряму, минаючи Python:
```nginx
location /static/ {
    alias /app/staticfiles/;
}
location /media/ {
    alias /app/media/;
}
```

---

## 11. Продакшн: Nginx + Gunicorn + Django + PostgreSQL + Redis

### Запуск Gunicorn

```bash
# Синхронний (WSGI)
gunicorn myproject.wsgi:application \
    --workers 4 \
    --bind unix:/run/django.sock \
    --timeout 30

# Асинхронний (ASGI з Uvicorn workers)
gunicorn myproject.asgi:application \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind unix:/run/django.sock
```

### Nginx конфігурація

```nginx
upstream django {
    server unix:/run/django.sock;
}

server {
    listen 443 ssl;
    server_name example.com;
    
    ssl_certificate /etc/ssl/certs/example.com.crt;
    ssl_certificate_key /etc/ssl/private/example.com.key;
    
    # Static files — Django не задіяний
    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
    }
    
    # Dynamic requests → Gunicorn → Django
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Docker Compose

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: myapp
      POSTGRES_PASSWORD: secret
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  web:
    build: .
    command: gunicorn myproject.asgi:application --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      - db
      - redis

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      - web

  celery:
    build: .
    command: celery -A myproject worker -l info
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

---

## 12. Celery — фонові задачі

```python
# tasks.py — task тільки транспортує виклик у service
from celery import shared_task

@shared_task
def send_welcome_email_task(user_id: int) -> None:
    from .selectors import user_get_by_id
    from .services import user_send_welcome_email

    user = user_get_by_id(user_id=user_id)
    user_send_welcome_email(user=user)   # логіка — у service


# services.py — логіка тут, не в task
from django.db import transaction

@transaction.atomic
def user_register(*, email: str, password: str):
    user = User(email=email)
    user.set_password(password)
    user.full_clean()
    user.save()
    # task запускається ПІСЛЯ commit — безпечно
    transaction.on_commit(lambda: send_welcome_email_task.delay(user.id))
    return user


# views.py — тонка, делегує в service
def register_view(request):
    serializer = UserRegisterInputSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = user_register(**serializer.validated_data)
    return Response({'id': user.id}, status=201)
```

---

## 13. Типові помилки та як їх уникнути

### N+1 запити

```python
# ПОГАНО
for book in Book.objects.all():  # 1 запит
    print(book.author.name)      # N запитів

# ДОБРЕ  
for book in Book.objects.select_related('author'):  # 1 JOIN-запит
    print(book.author.name)
```

### Блокуючі запити у view

```python
# ПОГАНО: блокує весь WSGI worker
import time
def slow_view(request):
    time.sleep(10)  # 10 секунд — worker недоступний
    return HttpResponse("done")

# ДОБРЕ: async view
async def slow_view(request):
    await asyncio.sleep(10)  # event loop вільний для інших запитів
    return HttpResponse("done")
```

### Логіка у Templates

```html
<!-- ПОГАНО: бізнес-логіка в шаблоні -->
{% if user.subscription.expires_at > now and user.subscription.plan.price > 0 %}

<!-- ДОБРЕ: логіка у View або Model -->
{% if user.has_active_paid_subscription %}
```

### Неправильний порядок Middleware

```python
# ПОГАНО: AuthenticationMiddleware перед SessionMiddleware
MIDDLEWARE = [
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # ← ПОМИЛКА!
    'django.contrib.sessions.middleware.SessionMiddleware',
]

# ДОБРЕ
MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',     # спочатку сесія
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # потім auth
]
```

### Помилки з static files у продакшні

```python
# ПОГАНО: Django роздає static у продакшні (повільно, небезпечно)
# DEBUG = True в продакшні

# ДОБРЕ
# DEBUG = False
# python manage.py collectstatic
# Nginx роздає /static/ напряму
```

---

## Питання для самоперевірки

1. Яка різниця між `select_related` і `prefetch_related` і коли кожен застосовувати?
2. Що відбудеться якщо поставити `AuthenticationMiddleware` вище `SessionMiddleware`?
3. Навіщо потрібен `collectstatic` і чому Django не повинен роздавати статику у продакшні?
4. В чому різниця між WSGI і ASGI з точки зору обробки 1000 одночасних запитів?
5. Що таке "lazy QuerySet" і коли насправді виконується SQL-запит?
