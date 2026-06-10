# Мережевий фундамент — Mermaid-схеми

> Усі схеми цього файлу — візуалізація концепцій із `network_foundation.md`.
> Рендеруються в будь-якому Markdown-переглядачі з підтримкою Mermaid (GitHub, Obsidian, VSCode).

---

## 1. Огляд Інтернету — від браузера до сервера

```mermaid
graph LR
    A[🖥️ Браузер] -->|DNS-запит| B[DNS Resolver]
    B -->|IP-адреса| A
    A -->|TCP + HTTP| C[🌐 Інтернет]
    C -->|пакети| D[Router ISP]
    D -->|маршрутизація| E[Router Datacenter]
    E -->|пакети| F[🖧 Веб-сервер]
    F -->|HTTP відповідь| C
    C -->|відповідь| A
```

---

## 2. Повний маршрут запиту: Клієнт → Router → ISP → Сервер

```mermaid
graph TD
    Browser[Браузер\n192.168.1.10] -->|HTTP GET /| HomeRouter[Домашній роутер\nNAT: замінює IP]
    HomeRouter -->|Публічний IP клієнта| ISP[ISP\nInternet Provider]
    ISP -->|BGP маршрутизація| InternetCore[Магістральні вузли\nInternet backbone]
    InternetCore -->|До цільової AS| DatacenterRouter[Маршрутизатор датацентру]
    DatacenterRouter -->|До сервера| LB[Load Balancer\nнеобов'язково]
    LB -->|Round-robin| Server[🖧 Цільовий сервер\n203.0.113.10:443]
    Server -->|HTTP Response| DatacenterRouter
    DatacenterRouter -->|Зворотній маршрут| Browser
```

---

## 3. DNS-резолюція — покроково

```mermaid
sequenceDiagram
    participant Browser as Браузер
    participant Cache as Локальний кеш ОС
    participant Resolver as DNS Resolver\n(провайдер / 8.8.8.8)
    participant Root as Root DNS Server
    participant TLD as TLD Server (.com)
    participant Auth as Authoritative DNS\n(github.com)

    Browser->>Cache: github.com → IP?
    Cache-->>Browser: Немає (кеш порожній)
    Browser->>Resolver: github.com → IP?
    Resolver->>Root: github.com → IP?
    Root-->>Resolver: Запитай TLD для .com
    Resolver->>TLD: github.com → IP?
    TLD-->>Resolver: Запитай ns1.p16.dynect.net
    Resolver->>Auth: github.com → IP?
    Auth-->>Resolver: 140.82.121.4 (TTL=60s)
    Resolver-->>Browser: 140.82.121.4
    Note over Browser,Cache: Браузер кешує результат на TTL секунд
    Browser->>Browser: З'єднання до 140.82.121.4:443
```

---

## 4. TCP — Three-Way Handshake + HTTP + Teardown

```mermaid
sequenceDiagram
    participant C as Клієнт (Браузер)
    participant S as Сервер (Nginx)

    Note over C,S: Фаза 1 — TCP Three-Way Handshake
    C->>S: SYN (seq=100)
    S-->>C: SYN-ACK (seq=200, ack=101)
    C->>S: ACK (ack=201)
    Note over C,S: З'єднання встановлено ✓

    Note over C,S: Фаза 2 — HTTP обмін
    C->>S: HTTP GET /products/ (заголовки + тіло)
    Note over S: Nginx обробляє, Django генерує відповідь
    S-->>C: HTTP 200 OK + HTML (Content-Length: 4200)

    Note over C,S: Фаза 3 — Завершення з'єднання
    C->>S: FIN
    S-->>C: ACK
    S->>C: FIN
    C-->>S: ACK
    Note over C,S: З'єднання закрито
```

---

## 5. HTTP Request/Response Lifecycle

```mermaid
sequenceDiagram
    participant U as 👤 Користувач
    participant B as Браузер
    participant DNS as DNS
    participant S as Сервер

    U->>B: Вводить https://shop.com/cart/
    B->>DNS: shop.com → IP?
    DNS-->>B: 93.184.216.34
    B->>S: TCP + TLS Handshake
    Note over B,S: Шифрований канал встановлено
    B->>S: GET /cart/ HTTP/1.1\nHost: shop.com\nCookie: sessionid=abc
    Note over S: Серверна логіка:\n1. Читає sessionid\n2. Знаходить юзера\n3. Запитує БД\n4. Рендерить HTML
    S-->>B: HTTP/1.1 200 OK\nContent-Type: text/html\n\n<html>...</html>
    B->>U: Відображає сторінку кошика
```

---

## 6. HTTPS / TLS Handshake

```mermaid
sequenceDiagram
    participant C as Клієнт (Браузер)
    participant S as Сервер (Nginx + SSL cert)
    participant CA as Certificate Authority\n(Let's Encrypt)

    Note over C,S: TCP з'єднання вже встановлено
    C->>S: ClientHello (TLS версія, cipher suites, random_C)
    S-->>C: ServerHello + SSL Certificate (підписаний CA)
    C->>CA: Перевірка підпису сертифікату
    CA-->>C: Сертифікат валідний ✓
    C->>S: Pre-master secret (зашифрований публічним ключем сервера)
    Note over C,S: Обидві сторони генерують session key
    C->>S: Finished (перший зашифрований пакет)
    S-->>C: Finished (підтвердження)
    Note over C,S: Всі наступні дані шифруються session key
    C->>S: HTTP GET / (тепер зашифровано)
    S-->>C: HTTP 200 OK + HTML (зашифровано)
```

---

## 7. Браузер → Бекенд → База даних (повний стек)

```mermaid
graph TD
    Browser[🖥️ Браузер] -->|HTTPS запит| Nginx[Nginx\nReverse Proxy :443]
    Nginx -->|Статичний файл?| Static[(📁 Файлова система\n/static/ /media/)]
    Static -->|PNG CSS JS| Nginx
    Nginx -->|Динамічний запит\nUnix Socket| WSGI[uWSGI / Gunicorn\nПроцес-менеджер]
    WSGI -->|WSGI environ dict| Django[🐍 Django Application]
    Django -->|SQL запит\nORM| PG[(PostgreSQL)]
    PG -->|Рядки даних| Django
    Django -->|HttpResponse HTML/JSON| WSGI
    WSGI -->|HTTP байти| Nginx
    Nginx -->|HTTPS відповідь| Browser

    style Browser fill:#4A90D9,color:#fff
    style Nginx fill:#2C7A2C,color:#fff
    style WSGI fill:#8B5E3C,color:#fff
    style Django fill:#0C4B33,color:#fff
    style PG fill:#336791,color:#fff
```

---

## 8. Socket-комунікація

```mermaid
graph LR
    subgraph Сервер
        S_App[Програма\nDjango/FastAPI] -->|socket.bind\nport 8000| S_Socket[Server Socket\n0.0.0.0:8000]
        S_Socket -->|socket.listen| Queue[Черга з'єднань]
        Queue -->|socket.accept| Conn[Активне з'єднання\nConn Socket]
        Conn -->|recv / send| S_App
    end

    subgraph Клієнт
        C_App[Браузер /\nHTTP клієнт] -->|socket.connect\n93.184.1.1:8000| C_Socket[Client Socket\nephemeral port]
        C_Socket -->|send / recv| C_App
    end

    Conn <-->|TCP байти| C_Socket
```

---

## 9. REST API Flow — повний цикл

```mermaid
sequenceDiagram
    participant App as 📱 Мобільний додаток
    participant Auth as Auth Middleware
    participant Router as URL Router
    participant View as API View
    participant DB as База даних

    App->>Auth: POST /api/login/ {"username": "...", "password": "..."}
    Auth-->>App: 200 OK {"token": "eyJhbGc..."}

    App->>Auth: GET /api/products/ + Header: Authorization: Bearer eyJhbGc...
    Note over Auth: Перевірка JWT токену
    Auth->>Router: Request + request.user (автентифікований)
    Router->>View: ProductListView.get(request)
    View->>DB: SELECT * FROM products WHERE active=true
    DB-->>View: 150 рядків продуктів
    View-->>Auth: JsonResponse([...], status=200)
    Auth-->>App: 200 OK [{"id":1, "name":"..."}, ...]

    App->>Auth: POST /api/cart/items/ {"product_id": 5, "qty": 2}
    Auth->>Router: CartItemCreateView.post(request)
    Router->>View: Валідація + збереження
    View->>DB: INSERT INTO cart_items ...
    DB-->>View: OK, id=42
    View-->>Auth: JsonResponse({"id": 42}, status=201)
    Auth-->>App: 201 Created {"id": 42}
```

---

## 10. Клієнт-серверна архітектура — концептуальний огляд

```mermaid
graph TB
    subgraph Клієнти
        Browser[🖥️ Веб-браузер]
        Mobile[📱 Мобільний додаток]
        CLI[⌨️ CLI / curl]
    end

    subgraph Internet[Інтернет]
        DNS_S[DNS Server]
        Router_I[Маршрутизатори]
    end

    subgraph Server[Серверна інфраструктура]
        Nginx_S[Nginx :80/:443]
        App[Python Backend\nDjango / FastAPI]
        DB_S[(PostgreSQL)]
        Cache_S[(Redis Cache)]
        Worker[Celery Workers]
    end

    Browser -->|HTTPS| Nginx_S
    Mobile -->|HTTPS| Nginx_S
    CLI -->|HTTP| Nginx_S
    
    Browser <-->|DNS lookup| DNS_S
    
    Nginx_S --> App
    App <--> DB_S
    App <--> Cache_S
    App -->|Task queue| Worker
    Worker <--> DB_S
```

---

## 11. Packets та маршрутизація IP

```mermaid
flowchart LR

    classDef layer fill:#E3F2FD,stroke:#1E88E5,color:#000
    classDef router fill:#FFF3E0,stroke:#FB8C00,color:#000
    classDef endpoint fill:#E8F5E9,stroke:#43A047,color:#000

    subgraph PACKET["TCP/IP Packet"]
        direction TB

        ETH["Ethernet Header\nMAC addresses"]:::layer

        IP["IP Header\nsrc/dst IP"]:::layer

        TCP["TCP Header\nports + sequence"]:::layer

        DATA["Payload\nHTTP data"]:::layer
    end

    Browser["🌍 Browser"]:::endpoint

    R1["Home Router"]:::router

    ISP["ISP Router"]:::router

    Core["Core Router"]:::router

    Alt["Alternative Route"]:::router

    Server["🖥️ Server"]:::endpoint

    Browser --> R1

    R1 --> ISP

    ISP --> Core

    ISP --> Alt

    Core --> Server

    Alt --> Server
```

---

## Довідкова таблиця протоколів

```mermaid
graph TD
    subgraph OSI [Рівні мережі спрощено]
        L7[L7 Прикладний\nHTTP HTTPS DNS FTP SMTP]
        L4[L4 Транспортний\nTCP UDP]
        L3[L3 Мережевий\nIP ICMP]
        L2[L2 Канальний\nEthernet WiFi MAC]
        L1[L1 Фізичний\nДроти Оптика Радіо]
    end
    L7 --> L4 --> L3 --> L2 --> L1
    
    style L7 fill:#4A90D9,color:#fff
    style L4 fill:#2C7A2C,color:#fff
    style L3 fill:#8B5E3C,color:#fff
    style L2 fill:#6B4C9A,color:#fff
    style L1 fill:#555,color:#fff
```
