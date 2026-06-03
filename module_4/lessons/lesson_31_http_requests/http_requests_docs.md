# Урок 31 — HTTP Requests: Документація та Архітектурні Схеми

**Модуль 4 · Network & Concurrent Systems**

> Цей файл — довідник та архітектурний компаньйон до `note_lesson_31_http_requests.ipynb`.
> Містить Mermaid-схеми, глибокі пояснення та production patterns.

---

## Зміст

1. [Що таке HTTP](#1-що-таке-http)
2. [Шари мережевого стеку](#2-шари-мережевого-стеку)
3. [7 Фаз HTTP-запиту](#3-7-фаз-http-запиту)
4. [requests: Внутрішня архітектура](#4-requests-внутрішня-архітектура)
5. [Типи помилок та їх джерела](#5-типи-помилок-та-їх-джерела)
6. [HTTP Methods та семантика](#6-http-methods-та-семантика)
7. [Session vs Standalone Requests](#7-session-vs-standalone-requests)
8. [Production Patterns](#8-production-patterns)
9. [Debugging Flowchart](#9-debugging-flowchart)

---

## 1. Що таке HTTP

### Визначення

HTTP (HyperText Transfer Protocol) — текстовий протокол прикладного рівня (L7),
що визначає формат запитів і відповідей між клієнтом і сервером.

### Ключові властивості

| Властивість | Пояснення |
| ----------- | --------- |
| **Stateless** | Сервер не пам'ятає попередніх запитів |
| **Text-based** | Повідомлення — це відформатований ASCII текст |
| **Request-Response** | Клієнт завжди ініціює, сервер відповідає |
| **TCP-based** | Працює поверх TCP (надійна доставка) |
| **Layered** | HTTP не знає про TCP деталі; TCP не знає про HTTP |

### Анатомія HTTP Request

```
GET /users/octocat HTTP/1.1\r\n         ← Request Line
Host: api.github.com\r\n                 ← Headers (конверт)
User-Agent: python-requests/2.28.1\r\n
Authorization: Bearer token123\r\n
Accept: application/json\r\n
\r\n                                     ← Порожній рядок = кінець headers
                                         ← Body (для GET — порожнє)
```

### Анатомія HTTP Response

```
HTTP/1.1 200 OK\r\n                      ← Status Line
Content-Type: application/json\r\n       ← Headers
Content-Length: 135\r\n
X-RateLimit-Remaining: 59\r\n
\r\n                                     ← Порожній рядок
{"login": "octocat", "id": 1, ...}       ← Body (JSON)
```

---

## 2. Шари Мережевого Стеку

```mermaid
flowchart TD
    A["🐍 Твій Python код\nrequests.get(url)"]
    B["📦 requests library\nSession · PreparedRequest · HTTPAdapter"]
    C["🔗 urllib3\nConnectionPool · HTTPConnection · Retry"]
    D["⚙️ OS Kernel\nTCP/IP Stack · DNS · TLS · Socket Buffers"]
    E["🔌 NIC Hardware\nДрайвер мережевої карти"]
    F["🌐 Internet\nRouters · Switches · Optical Fiber"]
    G["🖥️ Remote Server\nNginx · FastAPI · Django · Database"]

    A -->|"high-level wrapper"| B
    B -->|"connection pooling"| C
    C -->|"system calls (syscalls)"| D
    D -->|"NIC driver interrupt"| E
    E -->|"електричні / оптичні сигнали"| F
    F -->|"TCP segments"| G

    style A fill:#e3f2fd,stroke:#1565c0,color:#000
    style B fill:#e8f5e9,stroke:#2e7d32,color:#000
    style C fill:#fff8e1,stroke:#f57f17,color:#000
    style D fill:#fce4ec,stroke:#880e4f,color:#000
    style E fill:#f3e5f5,stroke:#4a148c,color:#000
    style F fill:#e0f7fa,stroke:#006064,color:#000
    style G fill:#efebe9,stroke:#3e2723,color:#000
```

**Ключовий принцип:** Python працює лише на рівні A і частково B.
Все нижче — OS Kernel і hardware. `requests` ховає цю складність,
але при помилках вона "протікає" назад до тебе як exception.

---

## 3. 7 Фаз HTTP-запиту

### Sequence Diagram: Повний Lifecycle

```mermaid
sequenceDiagram
    participant PY as 🐍 Python Process
    participant OS as ⚙️ OS Kernel
    participant DNS as 🔍 DNS Server
    participant NET as 🌐 Internet
    participant SRV as 🖥️ Remote Server
    participant DB as 🗄️ Database

    Note over PY: [T=0] requests.get() викликано
    Note over PY: Python ЗУПИНЯЄТЬСЯ

    PY->>OS: getaddrinfo("api.github.com")
    OS->>DNS: UDP Query: "api.github.com?"
    DNS-->>OS: IP: 140.82.112.4
    OS-->>PY: IP отримано

    Note over PY,OS: Фаза 1: DNS Resolution ✓

    PY->>OS: connect(140.82.112.4:443)
    OS->>SRV: SYN →
    SRV-->>OS: ← SYN-ACK
    OS->>SRV: ACK →
    Note over OS,SRV: TCP ESTABLISHED
    OS->>SRV: TLS ClientHello →
    SRV-->>OS: ← TLS ServerHello + Certificate
    OS->>SRV: TLS Finished →
    Note over OS,SRV: TLS ESTABLISHED

    Note over PY,OS: Фаза 2: TCP + TLS Handshake ✓

    PY->>OS: sendall(HTTP bytes)
    Note over PY: PreparedRequest побудовано
    OS->>NET: TCP Segments
    NET->>SRV: Пакети прибули

    Note over PY,OS: Фаза 3+4: Serialization + Send ✓
    Note over PY: Python СПИТЬ (blocking recv)

    SRV->>DB: SQL Query
    DB-->>SRV: Result rows
    SRV->>SRV: Формує JSON відповідь
    SRV->>NET: HTTP Response bytes
    NET->>OS: Пакети прибули

    Note over PY,OS: Фаза 5: Server Processing ✓

    OS->>OS: Receive Buffer заповнено
    Note over PY: Hardware interrupt!
    OS-->>PY: recv() повертає bytes
    Note over PY: Python ПРОКИДАЄТЬСЯ

    Note over PY,OS: Фаза 6: Receiving + Wakeup ✓

    PY->>PY: HTTP parsing → Response object
    PY->>PY: response.json() → json.loads()
    Note over PY: [T=6] requests.get() повертає Response

    Note over PY: Фаза 7: Deserialization ✓
```

### Фази у деталях

| Фаза | Час | Де Python | Хто виконує роботу |
| ---- | --- | --------- | ------------------- |
| DNS Resolution | T=0 | Зупинений | OS Kernel → DNS Server |
| TCP + TLS Handshake | T=1 | Зупинений | OS Kernel ↔ Remote OS |
| HTTP Serialization | T=2 | Активний | `requests` library |
| Send + Long Sleep | T=3 | **Спить** | OS Kernel → NIC → Internet |
| Server Processing | T=4 | **Спить** | Remote Server + DB |
| Receive + Wakeup | T=5 | Прокидається | OS Kernel (interrupt) |
| Deserialization | T=6 | Активний | `json.loads()` у RAM |

---

## 4. requests: Внутрішня Архітектура

```mermaid
classDiagram
    class Session {
        +headers: dict
        +cookies: CookieJar
        +auth: tuple
        +adapters: dict
        +get(url, **kwargs)
        +post(url, **kwargs)
        +request(method, url, **kwargs)
        +prepare_request(request)
    }

    class Request {
        +method: str
        +url: str
        +headers: dict
        +params: dict
        +data: dict
        +json: dict
        +auth: tuple
    }

    class PreparedRequest {
        +method: str
        +url: str
        +headers: CaseInsensitiveDict
        +body: bytes
        +prepare()
    }

    class HTTPAdapter {
        +max_retries: Retry
        +send(request, timeout)
        +build_response(request, resp)
    }

    class Response {
        +status_code: int
        +headers: dict
        +text: str
        +content: bytes
        +request: PreparedRequest
        +history: list
        +json()
        +raise_for_status()
    }

    Session --> Request : prepare_request()
    Request --> PreparedRequest : prepare()
    Session --> HTTPAdapter : send()
    HTTPAdapter --> Response : build_response()
    Response --> PreparedRequest : .request (зворотне посилання)
```

### Потік даних всередині requests

```mermaid
flowchart LR
    A["requests.get(url,\nparams=...,\nheaders=...,\njson=...,\ntimeout=...)"]

    B["Request об'єкт\n(непідготовлений)"]

    C["PreparedRequest\nmethod='GET'\nurl='https://...?q=python'\nheaders={...}\nbody=b'{...}'"]

    D["HTTPAdapter.send()\nurllib3\nConnectionPool"]

    E["OS Socket\nsendall() + recv()"]

    F["HTTP Response bytes\nHTTP/1.1 200 OK\n..."]

    G["Response об'єкт\n.status_code=200\n.headers={...}\n.text='...'"]

    A -->|"Session.request()"| B
    B -->|"prepare_request()"| C
    C -->|"adapter.send()"| D
    D -->|"socket syscall"| E
    E -->|"raw bytes"| F
    F -->|"build_response()"| G

    style C fill:#fff3e0,stroke:#e65100
    style E fill:#fce4ec,stroke:#880e4f
```

---

## 5. Типи Помилок та їх Джерела

```mermaid
flowchart TD
    START["requests.get(url, timeout=5)"]

    DNS{"DNS\nResolution\nуспішно?"}
    TCP{"TCP\nHandshake\nуспішно?"}
    SEND{"sendall()\nуспішно?"}
    WAIT{"recv()\nотримав\nбайти?"}
    STATUS{"HTTP Status\nCode?"}
    JSON{"response.json()\nуспішно?"}

    ERR1["❌ ConnectionError\n(DNSError)\nDNS не відповідає\nабо домен не існує"]
    ERR2["❌ ConnectionError\n(Connection Refused)\nSервер закрив TCP\nабо порт не слухається"]
    ERR3["❌ ConnectTimeout\nTCP handshake\nзайняв занадто довго"]
    ERR4["❌ ReadTimeout\nСервер не відповів\nза read_timeout секунд"]
    ERR5["⚠️ HTTPError 4xx\nТвій запит неправильний\n401 · 403 · 404 · 429"]
    ERR6["⚠️ HTTPError 5xx\nСервер зламано\n500 · 502 · 503 · 504"]
    ERR7["❌ JSONDecodeError\nСервер повернув HTML\nзамість JSON"]
    SUCCESS["✅ Python dict\nДані отримано"]

    START --> DNS
    DNS -->|"Ні"| ERR1
    DNS -->|"Так"| TCP
    TCP -->|"RST packet"| ERR2
    TCP -->|"Timeout"| ERR3
    TCP -->|"OK"| SEND
    SEND --> WAIT
    WAIT -->|"Timeout"| ERR4
    WAIT -->|"bytes"| STATUS
    STATUS -->|"2xx"| JSON
    STATUS -->|"4xx"| ERR5
    STATUS -->|"5xx"| ERR6
    JSON -->|"HTML/XML"| ERR7
    JSON -->|"valid JSON"| SUCCESS

    style ERR1 fill:#ffebee,stroke:#c62828
    style ERR2 fill:#ffebee,stroke:#c62828
    style ERR3 fill:#fff3e0,stroke:#e65100
    style ERR4 fill:#fff3e0,stroke:#e65100
    style ERR5 fill:#fffde7,stroke:#f9a825
    style ERR6 fill:#fff3e0,stroke:#e65100
    style ERR7 fill:#ffebee,stroke:#c62828
    style SUCCESS fill:#e8f5e9,stroke:#2e7d32
```

### Таблиця Exception → Причина → Дія

| Exception | Рівень | Причина | Дія |
| --------- | ------ | ------- | --- |
| `ConnectionError` (DNS) | L3-L4 | Домен не знайдено | Перевір DNS: `ping domain.com` |
| `ConnectionError` (Refused) | L4 | Порт закрито, RST | Перевір чи сервер запущено |
| `ConnectTimeout` | L4 | Handshake завис | Збільш connect_timeout або перевір firewall |
| `ReadTimeout` | L7 | Сервер повільний | Збільш read_timeout або retry |
| `SSLError` | L4-L7 | Невалідний сертифікат | Оновити CA bundle або `verify=False` (небезпечно!) |
| `HTTPError 401` | L7 | Немає авторизації | Додай `Authorization` header |
| `HTTPError 403` | L7 | Заблоковано (WAF/bot) | Перевір `User-Agent`, IP ban |
| `HTTPError 404` | L7 | Ресурс не існує | Перевір URL, не retry |
| `HTTPError 429` | L7 | Rate limit | Чекай `Retry-After` секунд |
| `HTTPError 5xx` | L7 | Сервер зламаний | Retry з backoff |
| `JSONDecodeError` | Python | HTML замість JSON | Перевір `Content-Type` header |
| `TooManyRedirects` | L7 | Redirect loop | `allow_redirects=False`, перевір URL |

---

## 6. HTTP Methods та Семантика

```mermaid
flowchart LR
    subgraph GET["GET — Отримати ресурс"]
        direction TB
        G1["params= → URL query string\n?search=python&page=1"]
        G2["Body: порожнє"]
        G3["Idempotent: Так\nSafe: Так (не змінює стан)"]
    end

    subgraph POST["POST — Створити ресурс"]
        direction TB
        P1["json= → JSON body\ndata= → form-encoded body"]
        P2["Body: payload"]
        P3["Idempotent: Ні\nSafe: Ні"]
    end

    subgraph PUT["PUT — Замінити ресурс"]
        direction TB
        U1["json= → повна заміна об'єкта"]
        U2["Body: повний об'єкт"]
        U3["Idempotent: Так\nSafe: Ні"]
    end

    subgraph PATCH["PATCH — Частково оновити"]
        direction TB
        PA1["json= → лише змінені поля"]
        PA2["Body: часткові зміни"]
        PA3["Idempotent: Залежить\nSafe: Ні"]
    end

    subgraph DELETE["DELETE — Видалити ресурс"]
        direction TB
        D1["params= → ID у URL"]
        D2["Body: зазвичай порожнє"]
        D3["Idempotent: Так\nSafe: Ні"]
    end
```

### Де йдуть дані — чіткий порівняльник

| Kwargs | HTTP частина | Метод | Приклад |
| ------ | ------------ | ----- | ------- |
| `params={'q': 'py'}` | URL: `?q=py` | GET | пошук, фільтрація |
| `headers={'Auth': '...'}` | HTTP Headers | будь-який | токени, content-type |
| `data={'key': 'val'}` | Body (form-encoded) | POST | HTML форми |
| `json={'key': 'val'}` | Body (JSON) | POST/PUT/PATCH | REST API |
| `files={'file': ...}` | Body (multipart) | POST | завантаження файлів |
| `auth=('user','pass')` | Authorization header | будь-який | Basic Auth |

---

## 7. Session vs Standalone Requests

```mermaid
sequenceDiagram
    participant CODE as Твій код
    participant SA as Standalone requests
    participant SESS as requests.Session()
    participant SRV as Сервер

    Note over CODE,SRV: STANDALONE — кожен запит ізольований

    CODE->>SA: requests.get(url, auth=creds)
    SA->>SRV: GET + Authorization header
    SRV-->>SA: 200 OK + Set-Cookie: session=abc
    SA-->>CODE: Response (cookie відкинуто!)

    CODE->>SA: requests.get(url)
    SA->>SRV: GET (без cookie, без auth!)
    SRV-->>SA: 401 Unauthorized
    SA-->>CODE: Response(401)

    Note over CODE,SRV: SESSION — стан зберігається

    CODE->>SESS: session.auth = ('user', 'pass')
    CODE->>SESS: session.get(url)
    SESS->>SRV: GET + Authorization header
    SRV-->>SESS: 200 OK + Set-Cookie: session=abc
    SESS->>SESS: Cookie збережено автоматично!
    SESS-->>CODE: Response(200)

    CODE->>SESS: session.get(other_url)
    SESS->>SRV: GET + Authorization + Cookie: session=abc
    SRV-->>SESS: 200 OK
    SESS-->>CODE: Response(200)
```

### Що Session зберігає між запитами

```python
session = requests.Session()
session.headers['User-Agent'] = 'MyApp/1.0'     # всі запити матимуть цей User-Agent
session.auth = ('user', 'pass')                  # Basic Auth у кожному запиті
session.cookies.set('tracking', 'value')         # cookie у кожному запиті
session.verify = False                           # вимкнути SSL verify (небезпечно!)
```

---

## 8. Production Patterns

### 8.1. Базовий Production Pattern

```python
import requests
from typing import Any

def safe_api_call(
    url: str,
    method: str = 'GET',
    **kwargs: Any
) -> dict:
    """
    Production-grade HTTP запит із повною обробкою помилок.
    """
    kwargs.setdefault('timeout', (3.05, 10))

    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.ConnectTimeout:
        raise RuntimeError(f"TCP handshake timeout: {url}")

    except requests.exceptions.ReadTimeout:
        raise RuntimeError(f"Server response timeout: {url}")

    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(f"Network unreachable (DNS/TCP): {e}")

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        body = e.response.text[:500]
        raise RuntimeError(f"HTTP {status} from {url}: {body}")

    except ValueError:
        raise RuntimeError(f"Invalid JSON from {url}: {response.text[:200]}")
```

### 8.2. Session з Retry та Backoff

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def build_session(
    retries: int = 3,
    backoff_factor: float = 1.0,
    base_url: str = '',
    token: str = '',
) -> requests.Session:
    """
    Production session із retry, backoff та авторизацією.
    """
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,   # 1с → 2с → 4с між спробами
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=['GET', 'POST', 'PUT'],
        respect_retry_after_header=True,
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    session = requests.Session()
    session.mount('https://', adapter)
    session.mount('http://', adapter)

    if base_url:
        session.headers['X-Base-URL'] = base_url

    if token:
        session.headers['Authorization'] = f'Bearer {token}'

    return session


# Використання
session = build_session(
    retries=3,
    backoff_factor=1.0,
    token='my_api_token_here'
)

response = session.get(
    'https://httpbin.org/get',
    params={'q': 'python'},
    timeout=(3.05, 10)
)
response.raise_for_status()
data = response.json()
```

### 8.3. Debugging Helper

```python
import requests

def inspect_request(response: requests.Response) -> None:
    """Повна діагностика відправленого запиту та отриманої відповіді."""

    req = response.request

    print("── ВІДПРАВЛЕНО ──────────────────────")
    print(f"  {req.method} {req.url}")
    for k, v in req.headers.items():
        print(f"  {k}: {v}")
    if req.body:
        print(f"\n  Body: {req.body[:200]}")

    print("\n── ОТРИМАНО ─────────────────────────")
    print(f"  HTTP {response.status_code} {response.reason}")
    for k, v in response.headers.items():
        print(f"  {k}: {v}")
    print(f"\n  Body (перші 300 символів):")
    print(f"  {response.text[:300]}")

    if response.history:
        print(f"\n── РЕДИРЕКТИ ({len(response.history)}) ────────────")
        for r in response.history:
            print(f"  {r.status_code} → {r.headers.get('Location')}")
```

---

## 9. Debugging Flowchart

```mermaid
flowchart TD
    START["API відповідає неправильно або падає exception"]

    Q1{"Який тип\nexception?"}

    Q2{"ConnectionError:\nDNS чи Refused?"}
    Q3{"Timeout:\nconnect чи read?"}
    Q4{"HTTPError:\nякий статус?"}
    Q5{"JSONDecodeError?"}

    A1["ping домен у терміналі\ncurl -v URL\nперевір Wi-Fi/VPN"]
    A2["nc -zv host port\nперевір чи сервер запущений\nперевір firewall правила"]
    A3["збільш connect_timeout\nперевір firewall/NAT\ncurl --connect-timeout 10"]
    A4["збільш read_timeout\nперевір навантаження сервера"]

    A5["401: перевір Authorization header\n403: перевір User-Agent, IP ban\n404: перевір URL, не retry\n429: чекай Retry-After\n5xx: retry з backoff"]

    A6["перевір Content-Type header\nprint(response.text[:300])\nperevir raise_for_status() спершу"]

    START --> Q1
    Q1 -->|"ConnectionError"| Q2
    Q1 -->|"Timeout"| Q3
    Q1 -->|"HTTPError"| Q4
    Q1 -->|"JSONDecodeError"| Q5
    Q1 -->|"Немає exception\nале результат неправильний"| INSPECT

    Q2 -->|"DNS fail"| A1
    Q2 -->|"Connection Refused"| A2
    Q3 -->|"connect timeout"| A3
    Q3 -->|"read timeout"| A4
    Q4 --> A5
    Q5 --> A6

    INSPECT["Інспектуй PreparedRequest:\nprint(response.request.url)\nprint(response.request.headers)\nprint(response.request.body)"]

    style START fill:#ffebee,stroke:#c62828
    style INSPECT fill:#e8eaf6,stroke:#3949ab
    style A5 fill:#fff9c4,stroke:#f9a825
```

### Загальний Debug Checklist

```
Крок 1: Перевір status_code
    → 2xx? Продовжуй
    → 4xx? Твій запит неправильний
    → 5xx? Сервер зламаний, retry

Крок 2: Перевір Content-Type
    → application/json? Можна response.json()
    → text/html? Сервер повернув HTML сторінку помилки

Крок 3: Перегляни перші 300 символів тіла
    → response.text[:300]

Крок 4: Перевір що Python відправив
    → response.request.url
    → response.request.headers
    → response.request.body

Крок 5: Обійди Python
    → curl -v "https://..." у терміналі
    → ping domain.com
    → telnet host port
```

---

## Глосарій

| Термін | Визначення |
| ------ | ---------- |
| **HTTP** | HyperText Transfer Protocol — текстовий протокол L7 |
| **Stateless** | Кожен запит ізольований; сервер не пам'ятає попередніх |
| **TCP Handshake** | 3-way (SYN-SYN/ACK-ACK) встановлення з'єднання |
| **TLS** | Transport Layer Security — шифрування HTTPS |
| **DNS** | Domain Name System — конвертація домену в IP |
| **PreparedRequest** | Внутрішній об'єкт requests: готовий HTTP рядок байтів |
| **Blocking I/O** | `recv()` зупиняє Python process до отримання відповіді |
| **Serialization** | Python dict → JSON рядок → bytes |
| **Deserialization** | bytes → JSON рядок → Python dict |
| **Timeout tuple** | `(connect_timeout, read_timeout)` у секундах |
| **raise_for_status()** | Кидає `HTTPError` якщо status_code >= 400 |
| **Session** | Об'єкт що зберігає headers/cookies/auth між запитами |
| **Retry / Backoff** | Повторні спроби із зростаючою паузою між ними |
| **Rate Limiting** | Сервер обмежує кількість запитів (429 Too Many Requests) |
| **Thundering Herd** | Всі retry запуститись одночасно → перевантаження сервера |
| **Circuit Breaker** | Патерн: після N помилок — одразу fail, не retry |

---

*Документація до Уроку 31 · Модуль 4 · Python Networking Course*
