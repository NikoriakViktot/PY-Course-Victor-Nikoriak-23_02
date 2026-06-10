# Django Architecture — Mermaid-схеми

> Усі схеми — візуалізація концепцій із `django_architecture.md`.

---

## 1. Django Request Lifecycle — загальна схема (MVT)

```mermaid
graph TD
    Browser[🖥️ Браузер] -->|HTTP Request| WebServer[Web Server\nWSGI / ASGI]
    WebServer -->|HttpRequest об'єкт| MW_IN[Middleware 1..N\nвхідний шлях]
    MW_IN -->|Security / Sessions / Auth| URLDisp[URL Dispatcher\nurlresolver]
    URLDisp -->|Знайдено збіг| View((View Function\nабо CBV))
    View <-->|ORM QuerySet → SQL| ORM[ORM Layer]
    ORM <-->|SQL запити| DB[(PostgreSQL)]
    View <-->|context dict| Tmpl[Template Engine\nJinja2 / DTL]
    Tmpl -->|HTML рядок| View
    View -->|HttpResponse об'єкт| MW_OUT[Middleware N..1\nзворотній шлях]
    MW_OUT -->|Заголовки / Cookies| WebServer
    WebServer -->|HTTP Response| Browser

    style Browser fill:#4A90D9,color:#fff
    style WebServer fill:#2C7A2C,color:#fff
    style URLDisp fill:#8B5E3C,color:#fff
    style View fill:#0C4B33,color:#fff
    style DB fill:#336791,color:#fff
```

---

## 2. Браузер → Django → База даних — повний sequence

```mermaid
sequenceDiagram
    participant B as 🖥️ Браузер
    participant N as Nginx
    participant G as Gunicorn/uWSGI
    participant DJ as Django App
    participant DB as PostgreSQL

    B->>N: HTTPS GET /books/42/
    N->>G: Forwarding via Unix Socket
    G->>DJ: WSGI environ dict
    
    Note over DJ: Middleware (вхід):\n1. SecurityMiddleware\n2. SessionMiddleware\n3. AuthMiddleware → request.user
    
    DJ->>DJ: URL Dispatcher: /books/42/ → BookDetailView
    
    Note over DJ: View execution
    DJ->>DB: SELECT * FROM books_book WHERE id=42
    DB-->>DJ: Рядок даних → Python Book об'єкт
    
    DJ->>DJ: Template render: book_detail.html + context
    
    Note over DJ: Middleware (вихід):\nContent-Length header
    
    DJ-->>G: HttpResponse (200 OK, HTML)
    G-->>N: HTTP bytes
    N-->>B: HTTPS 200 OK + HTML
```

---

## 3. URL Dispatcher — логіка маршрутизації

```mermaid
flowchart TD
    Req[HTTP Request\nPATH: /api/books/42/] --> Root[myproject/urls.py]
    
    Root -->|path: admin/| Admin[Django Admin]
    Root -->|path: api/| APIUrls[api/urls.py\ninclude]
    Root -->|path: нічого не збіглось| NotFound[404 Not Found]
    
    APIUrls -->|path: books/| BookUrls[books/urls.py\ninclude]
    APIUrls -->|path: users/| UserUrls[users/urls.py]
    
    BookUrls -->|path: пусто\nGET /api/books/| BookList[BookListView\nСписок книг]
    BookUrls -->|path: int:pk /\n/api/books/42/| BookDetail[BookDetailView\nДеталі книги pk=42]
    BookUrls -->|path: нічого не збіглось| NotFound
    
    style Req fill:#4A90D9,color:#fff
    style BookDetail fill:#0C4B33,color:#fff
    style NotFound fill:#c0392b,color:#fff
```

---

## 4. Middleware Chain — "цибулина" запиту

```mermaid
graph TD
    subgraph Зовнішній шар
        S1[SecurityMiddleware\nHTTPS redirect, HSTS]
    end
    subgraph Шар сесій
        S2[SessionMiddleware\nЧитає sessionid cookie]
    end
    subgraph Шар захисту
        S3[CsrfViewMiddleware\nПеревірка CSRF токену]
    end
    subgraph Шар авторизації
        S4[AuthenticationMiddleware\nrequest.user = User]
    end
    subgraph Центр
        View[🎯 View Function\nБізнес-логіка]
    end

    Request[HTTP Request] --> S1
    S1 --> S2 --> S3 --> S4 --> View

    View --> S4_out[Middleware 4 out]
    S4_out --> S3_out[Middleware 3 out\nContent-Length]
    S3_out --> S2_out[Middleware 2 out\nSet-Cookie session]
    S2_out --> S1_out[Middleware 1 out\nSecurity headers]
    S1_out --> Response[HTTP Response]

    style View fill:#0C4B33,color:#fff
    style Request fill:#4A90D9,color:#fff
    style Response fill:#2C7A2C,color:#fff
```

---

## 5. ORM Architecture — Model → SQL → Python

```mermaid
graph LR
    subgraph Python код
        Model[class Book\nmodels.Model]
        QS[QuerySet\nBook.objects.filter...]
        PO[Python об'єкти\nlist of Book instances]
    end

    subgraph Django ORM
        SQL_GEN[SQL Generator\nDjango DB Backend]
        CONN[Connection Pool\npsycopg2]
    end

    subgraph База даних
        PG[(PostgreSQL\nbooks_book table)]
    end

    Model -->|визначає схему| SQL_GEN
    QS -->|lazy evaluation| SQL_GEN
    SQL_GEN -->|SELECT / INSERT / UPDATE| CONN
    CONN -->|SQL запит| PG
    PG -->|rows| CONN
    CONN -->|raw data| SQL_GEN
    SQL_GEN -->|hydration| PO

    style PG fill:#336791,color:#fff
    style Model fill:#0C4B33,color:#fff
```

---

## 6. Структура Django проєкту

```mermaid
graph TD
    Root[myproject/] --> Manage[manage.py]
    Root --> Config[myproject/\nКонфігурація]
    Root --> App1[books/\nДодаток]
    Root --> App2[users/\nДодаток]

    Config --> Settings[settings.py\nНалаштування]
    Config --> URLs[urls.py\nКореневий роутер]
    Config --> WSGI[wsgi.py]
    Config --> ASGI[asgi.py]

    App1 --> Models[models.py\nBook, Author]
    App1 --> Views[views.py\nBookListView, BookDetailView]
    App1 --> AppURLs[urls.py\nМаршрути]
    App1 --> Templates[templates/books/\n*.html]
    App1 --> Admin_py[admin.py\nАдмін реєстрація]
    App1 --> Migrations[migrations/\n0001_initial.py...]

    style Root fill:#555,color:#fff
    style Config fill:#2C7A2C,color:#fff
    style App1 fill:#4A90D9,color:#fff
    style App2 fill:#4A90D9,color:#fff
```

---

## 7. Authentication Flow — Login/Logout

```mermaid
sequenceDiagram

    participant U as 👤 Користувач
    participant B as 🌍 Браузер
    participant DJ as 🐍 Django Server

    U->>B: Вводить логін і пароль

    B->>DJ: POST /login/

    Note over DJ: authenticate(username, password)\nПеревірка хешу пароля

    alt ✅ Дані правильні

        DJ->>DJ: login(request, user)

        Note over DJ: Створення session\nу django_session

        DJ-->>B: 302 Redirect /dashboard/\nSet-Cookie: sessionid=abc123

        B->>DJ: GET /dashboard/\nCookie: sessionid=abc123

        Note over DJ: SessionMiddleware\nзчитує session

        Note over DJ: AuthMiddleware\nrequest.user = User(id=42)

        DJ-->>B: HTML Dashboard

    else ❌ Невірний пароль

        DJ-->>B: HTML + "Невірні дані"

    end

    U->>B: Натискає "Вийти"

    B->>DJ: POST /logout/

    Note over DJ: logout(request)\nвидаляє session

    DJ-->>B: Redirect /\nочищення session cookie
```

---


```mermaid
flowchart LR

    classDef client fill:#E3F2FD,stroke:#1E88E5,color:#000
    classDef app fill:#E8F5E9,stroke:#43A047,color:#000
    classDef db fill:#FFF3E0,stroke:#FB8C00,color:#000

    User["👤 Користувач"]:::client

    Browser["🌍 Браузер\nsessionid cookie"]:::client

    Django["🐍 Django\nAuth + SessionMiddleware"]:::app

    DB[("🗄️ django_session")]:::db

    User --> Browser

    Browser -->|"POST /login"| Django

    Django -->|"authenticate()"| DB

    Django -->|"створення session"| DB

    Django -->|"Set-Cookie: sessionid"| Browser

    Browser -->|"Cookie: sessionid"| Django

    Django -->|"request.user"| User
```



---


```mermaid
flowchart TB

    Request["HTTP Request"]

    Cookie["sessionid cookie"]

    Session["django_session table"]

    User["Authenticated User"]

    Request --> Cookie

    Cookie --> Session

    Session --> User
```



---

## 8. Session Lifecycle

```mermaid
flowchart LR

    classDef anon fill:#FFCDD2,stroke:#E53935,color:#000
    classDef auth fill:#C8E6C9,stroke:#43A047,color:#000
    classDef process fill:#E3F2FD,stroke:#1E88E5,color:#000

    Anonymous["👤 Анонімний"]:::anon

    Login["POST /login/"]:::process

    Auth["✅ Автентифікований\nsessionid cookie"]:::auth

    Logout["POST /logout/"]:::process

    Expire["Session Expired"]:::process

    Anonymous --> Login

    Login -->|"authenticate() OK"| Auth

    Login -->|"❌ wrong password"| Anonymous

    Auth --> Logout

    Logout --> Anonymous

    Auth --> Expire

    Expire --> Anonymous
```

---

# Session + Cookie Architecture

```mermaid
flowchart TB

    Browser["🌍 Browser"]

    Cookie["sessionid cookie"]

    Django["🐍 Django"]

    SessionDB[("🗄️ django_session")]

    User["request.user"]

    Browser --> Cookie

    Cookie --> Django

    Django --> SessionDB

    SessionDB --> User
```

---

#  Що реально відбувається на кожному request.

```mermaid
sequenceDiagram

    participant B as Browser
    participant D as Django
    participant DB as Session DB

    B->>D: HTTP Request + sessionid cookie

    D->>DB: find session by sessionid

    DB-->>D: session data

    D->>D: request.user restored

    D-->>B: HTTP Response
```

---

## 9. WSGI vs ASGI — модель конкурентності

```mermaid
graph TD
    subgraph WSGI_SYN[WSGI — Синхронна модель]
        W_Nginx[Nginx] --> W_Gunicorn[Gunicorn\n4 workers]
        W_Gunicorn --> W1[Worker 1\n🔒 Зайнятий\nчекає БД 3сек]
        W_Gunicorn --> W2[Worker 2\n🔒 Зайнятий]
        W_Gunicorn --> W3[Worker 3\n✅ Вільний]
        W_Gunicorn --> W4[Worker 4\n✅ Вільний]
        Note1[Максимум 4 паралельні запити]
    end

    subgraph ASGI_ASY[ASGI — Асинхронна модель]
        A_Nginx[Nginx] --> A_Uvicorn[Uvicorn\n4 workers з event loop]
        A_Uvicorn --> EL[Event Loop\nWorker 1]
        EL --> T1[Task 1: await db.query]
        EL --> T2[Task 2: обробляє запит]
        EL --> T3[Task 3: await file.read]
        EL --> T4[Task N: тисячі корутин...]
        Note2[Тисячі паралельних з'єднань]
    end

    style Note1 fill:#c0392b,color:#fff
    style Note2 fill:#2C7A2C,color:#fff
```

---

## 10. Django + PostgreSQL з'єднання

```mermaid
graph TD
    subgraph Django App
        ORM[Django ORM\nQuerySet API]
        Pool[Connection Pool\nDjango DB connections\nmax 10 за замовчуванням]
    end

    subgraph PostgreSQL
        PG_Auth[Auth\nUser: myapp Password: ***]
        PG_Parser[Query Parser\nSQL → Query Plan]
        PG_Exec[Query Executor]
        PG_Storage[(Storage Engine\nHeap / B-Tree Index)]
    end

    ORM -->|Python QuerySet| Pool
    Pool -->|TCP :5432 або Unix Socket\npsycopg2| PG_Auth
    PG_Auth -->|Authenticated| PG_Parser
    PG_Parser -->|Optimized Query Plan| PG_Exec
    PG_Exec -->|Read/Write| PG_Storage
    PG_Storage -->|Rows| PG_Exec
    PG_Exec -->|Result set| Pool
    Pool -->|Python objects| ORM

    style PG_Storage fill:#336791,color:#fff
```

---

## 11. Django + Redis + Celery

```mermaid
graph LR
    User[👤 Користувач] -->|POST /order/| DjangoView[Django View]
    
    DjangoView -->|send_confirmation_email.delay| Redis[(Redis\nBroker Queue)]
    DjangoView -->|HttpResponse 201| User
    Note1[Відповідь миттєва!\nEmail іде фоново]
    
    Redis -->|Task picked up| CeleryW[Celery Worker]
    CeleryW -->|SMTP| Email[📧 Email Server]
    CeleryW -->|Результат| Redis

    subgraph Моніторинг
        Flower[Flower UI\n:5555]
    end
    
    CeleryW --> Flower
    
    style Redis fill:#dc382c,color:#fff
    style Note1 fill:#2C7A2C,color:#fff
```

---

## 12. Production Deployment Architecture (Nginx + Gunicorn + Docker)

```mermaid
graph TD
    Client[Browser / Mobile] -->|HTTPS :443| Nginx[Nginx\nReverse Proxy]
    
    Nginx -->|/static/ /media/\nБез Python| Disk[(📁 Файлова система\nstaticfiles/ media/)]
    
    Nginx -->|Динамічні запити\nUnix Socket| Gunicorn[Gunicorn\nProcess Manager]
    
    subgraph Python Application
        Gunicorn -->|fork| W1[Uvicorn Worker 1]
        Gunicorn -->|fork| W2[Uvicorn Worker 2]
        Gunicorn -->|fork| W3[Uvicorn Worker 3]
        Gunicorn -->|fork| W4[Uvicorn Worker 4]
    end
    
    W1 -->|ASGI| DjApp[Django Application]
    W2 -->|ASGI| DjApp
    W3 -->|ASGI| DjApp
    W4 -->|ASGI| DjApp
    
    DjApp -->|Async ORM| PG[(PostgreSQL :5432)]
    DjApp -->|Cache / Sessions| RedisDB[(Redis :6379)]
    DjApp -->|Tasks| CeleryQ[Celery Workers]
    CeleryQ --> PG
    
    style Client fill:#4A90D9,color:#fff
    style Nginx fill:#2C7A2C,color:#fff
    style DjApp fill:#0C4B33,color:#fff
    style PG fill:#336791,color:#fff
    style RedisDB fill:#dc382c,color:#fff
```

---

## 13. Django Request Lifecycle — детальний sequence

```mermaid
sequenceDiagram
    participant B as 🖥️ Браузер
    participant MW as Middleware (In/Out)
    participant URL as URL Router
    participant V as View
    participant DB as ORM / Database
    participant T as Template Engine

    B->>MW: HTTP GET /books/1/
    Note over MW: Вхідний шлях (зверху вниз):\n1. SecurityMiddleware\n2. SessionMiddleware\n3. AuthMiddleware → request.user

    MW->>URL: HttpRequest (request.user доданий)
    URL->>V: invoke book_detail(request, pk=1)
    
    V->>DB: Book.objects.select_related('author').get(id=1)
    Note over DB: SELECT books_book.*, auth_author.*\nFROM books_book\nJOIN auth_author ON ...\nWHERE books_book.id = 1
    DB-->>V: Python Book об'єкт (з author)
    
    V->>T: render('books/detail.html', {'book': book})
    Note over T: Парсинг шаблону\nПідстановка змінних\nEscape HTML (XSS захист)
    T-->>V: HTML рядок (4.2KB)
    
    V-->>MW: HttpResponse(html, status=200)
    
    Note over MW: Зворотній шлях (знизу вгору):\nContent-Length: 4200\nVary: Cookie
    
    MW-->>B: HTTP/1.1 200 OK + HTML
```

---

## 14. Django Admin Panel — архітектура

```mermaid
graph TD
    Dev[👨‍💻 Розробник] -->|register| AdminSite[django.contrib.admin\nAdminSite]
    
    subgraph Реєстрація моделей
        AdminSite --> BA[BookAdmin\nlist_display, search_fields]
        AdminSite --> UA[UserAdmin\nfilter_horizontal]
        AdminSite --> OtherAdmin[...]
    end
    
    User[👤 Адмін-користувач] -->|GET /admin/books/book/| AdminSite
    
    AdminSite -->|CRUD операції| ORM_A[Django ORM]
    ORM_A -->|SQL| DB_A[(Database)]
    
    AdminSite -->|auth check\nis_staff=True| Auth[Authentication System]
    
    style AdminSite fill:#0C4B33,color:#fff
    style DB_A fill:#336791,color:#fff
```

---

## 15. Масштабування Django у продакшні

```mermaid
graph TD
    Internet[🌐 Інтернет] --> LB[Load Balancer\nHAProxy / AWS ALB]
    
    LB --> Nginx1[Nginx 1]
    LB --> Nginx2[Nginx 2]
    
    Nginx1 --> App1[Django App\nContainer 1]
    Nginx1 --> App2[Django App\nContainer 2]
    Nginx2 --> App3[Django App\nContainer 3]
    Nginx2 --> App4[Django App\nContainer 4]
    
    App1 & App2 & App3 & App4 -->|Спільна БД| PG_Master[(PostgreSQL\nMaster)]
    App1 & App2 & App3 & App4 -->|Read replicas| PG_Read[(PostgreSQL\nRead Replica)]
    App1 & App2 & App3 & App4 -->|Shared cache\nSessions| Redis_Cluster[(Redis Cluster)]
    
    App1 & App2 & App3 & App4 -->|Tasks| CeleryQ[(Redis Queue)]
    CeleryQ --> CW1[Celery Worker 1]
    CeleryQ --> CW2[Celery Worker 2]
    
    style LB fill:#555,color:#fff
    style PG_Master fill:#336791,color:#fff
    style Redis_Cluster fill:#dc382c,color:#fff
```
