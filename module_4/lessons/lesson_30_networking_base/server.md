# Python Web Servers, Kernel та Production Networking

---

# Головна ідея

Більшість початківців думають:

```python
from fastapi import FastAPI
```

або:

```python
from flask import Flask
```

це вже:

```text
web server
```

Але це НЕ так.

---

# Framework ≠ Server

FastAPI, Flask, Django —
це:

```text
application frameworks
```

Вони:
- описують routes,
- business logic,
- request handlers,
- middleware.

Але вони НЕ:
- відкривають TCP sockets напряму,
- НЕ роблять accept(),
- НЕ керують epoll/select,
- НЕ працюють із kernel networking stack напряму.

---

# Хто реально працює з мережею?

Реальний networking робить:

- Gunicorn
- Uvicorn
- Hypercorn
- uWSGI
- Daphne

Саме вони:
- відкривають sockets,
- bind() на port,
- listen(),
- accept(),
- recv(),
- send().

---

# Архітектурно

```text
Python App
    ↓
WSGI / ASGI
    ↓
Python Server
    ↓
OS Kernel
    ↓
TCP/IP Stack
    ↓
Network
```

---

# Що таке WSGI?

WSGI =
```text
Web Server Gateway Interface
```

Старий synchronous стандарт Python web.

---

# WSGI модель

```text
HTTP Request
↓
1 worker/thread/process
↓
Framework handles request
↓
HTTP Response
```

---

# Frameworks які працюють через WSGI

| Framework | Тип |
|---|---|
| Flask | minimal WSGI |
| Django (classic) | full-stack WSGI |

---

# Що таке ASGI?

ASGI =
```text
Asynchronous Server Gateway Interface
```

Новий async стандарт Python.

---

# ASGI підтримує

- asyncio
- WebSocket
- long connections
- streaming
- async I/O
- event loops

---

# Frameworks які працюють через ASGI

| Framework | Тип |
|---|---|
| FastAPI | modern ASGI |
| Starlette | lightweight ASGI |
| Quart | async Flask |
| aiohttp | async HTTP |
| modern Django async | hybrid |

---

# Найважливіший systems-thinking момент

Framework:
```text
визначає application logic
```

Server:
```text
визначає networking model
```

---

# Що реально робить Gunicorn?

Gunicorn:
- socket()
- bind()
- listen()
- fork workers
- accept()
- recv()
- передає request у Flask/Django app

---

# Gunicorn lifecycle

```text
socket()
↓
bind()
↓
listen()
↓
fork workers
↓
accept()
↓
recv()
↓
WSGI app
↓
response
```

---

# Що реально робить Uvicorn?

Uvicorn —
це async ASGI server.

Він:
- використовує event loop,
- epoll/select,
- non-blocking sockets,
- asyncio tasks.

---

# Uvicorn lifecycle

```text
socket()
↓
epoll/select
↓
event loop
↓
async tasks
↓
ASGI app
↓
await recv/send
```

---

# Production Architecture

Типова production схема для FastAPI:

```text
                 INTERNET
                      │
══════════════════════╪══════════════════════
                      ▼
               ┌────────────┐
               │   Nginx    │
               │ :80 / :443 │
               └─────┬──────┘
                     │ reverse proxy
                     ▼
          ┌─────────────────────┐
          │     Uvicorn         │
          │   ASGI Server       │
          └─────┬──────┬────────┘
                │      │
         Worker 1   Worker 2
                │      │
                ▼      ▼
             FastAPI App
```

---

# Для Django

```text
Browser
↓
Nginx
↓
Gunicorn
↓
Django
```

---

# Що робить Nginx?

Nginx:
- слухає 80/443,
- TLS/HTTPS,
- reverse proxy,
- buffering,
- static files,
- load balancing,
- keep-alive connections.

---

# Чому НЕ запускати FastAPI/Flask напряму?

Бо:

```python
app.run()

```

це:

```text
development server
```

---

# Development server НЕ вміє нормально

- multiprocessing
- worker management
- graceful shutdown
- production buffering
- efficient concurrency
- load balancing
- advanced socket handling

---

# Повна Mental Model

```text
        USER SPACE
═══════════════════════════════════

 FastAPI / Django / Flask
            │
            ▼
    Uvicorn / Gunicorn
            │
            ▼
════════ syscall boundary ════════

         OS KERNEL
═══════════════════════════════════

 TCP Stack
 Socket Buffers
 Scheduler
 epoll/select
 File Descriptors

═══════════════════════════════════

        NETWORK LAYER
═══════════════════════════════════

 TCP/IP
 Ethernet
 Wi-Fi
 Routers
 Internet
```

---

# Що означає recv() у production server?

Коли Uvicorn або Gunicorn робить:

```python
sock.recv(1024)
```

це означає:

```text
перехід через syscall boundary у kernel
```

---

# Далі kernel:

- перевіряє receive buffer,
- якщо bytes є → повертає data,
- якщо bytes немає → блокує thread/process.

---

# Blocking Model

```text
Python Process
↓
recv()
↓
Kernel checks socket buffer
↓
buffer empty
↓
process asleep
↓
packet arrives
↓
kernel wakeup
↓
recv() returns bytes
```

---

# Найважливіший висновок

Python framework —
це лише application layer.

Реальний networking:
- sockets,
- TCP,
- buffers,
- event loops,
- epoll/select,
- scheduler,
- kernel wakeups

робить:
- Gunicorn,
- Uvicorn,
- kernel networking stack.

# 🔥 1. Flask / Django (WSGI) Architecture

```mermaid
flowchart TB

    classDef client fill:#263238,stroke:#90a4ae,color:#fff
    classDef proxy fill:#4a3b00,stroke:#ff9800,color:#fff
    classDef server fill:#1b5e20,stroke:#4CAF50,color:#fff
    classDef framework fill:#4e1f1f,stroke:#f44336,color:#fff

    Browser["🌍 Browser"]:::client

    Nginx["Nginx\nReverse Proxy"]:::proxy

    Gunicorn["Gunicorn\nWSGI Server"]:::server

    Django["Django / Flask\nWSGI App"]:::framework

    Browser -->|"HTTP Request"| Nginx

    Nginx -->|"proxy_pass"| Gunicorn

    Gunicorn -->|"WSGI call"| Django

    Django --> Gunicorn

    Gunicorn --> Nginx

    Nginx --> Browser
```

---

# 🔥 2. FastAPI + Uvicorn (ASGI)

```mermaid
flowchart TB

    classDef client fill:#263238,stroke:#90a4ae,color:#fff
    classDef proxy fill:#4a3b00,stroke:#ff9800,color:#fff
    classDef server fill:#1b5e20,stroke:#4CAF50,color:#fff
    classDef framework fill:#4e1f1f,stroke:#f44336,color:#fff
    classDef async fill:#1565C0,stroke:#42A5F5,color:#fff

    Browser["🌍 Browser"]:::client

    Nginx["Nginx\n:80 / :443"]:::proxy

    Uvicorn["Uvicorn\nASGI Server"]:::server

    Loop["asyncio Event Loop"]:::async

    FastAPI["FastAPI\nASGI App"]:::framework

    Browser --> Nginx

    Nginx -->|"reverse proxy"| Uvicorn

    Uvicorn --> Loop

    Loop --> FastAPI
```

---

# 🔥 3. Full Production Networking Stack

```mermaid
flowchart TB

    classDef user fill:#263238,stroke:#90a4ae,color:#fff
    classDef app fill:#1b5e20,stroke:#4CAF50,color:#fff
    classDef kernel fill:#4a3b00,stroke:#ff9800,color:#fff
    classDef hardware fill:#4e1f1f,stroke:#f44336,color:#fff

    subgraph USER["USER SPACE"]
        App["FastAPI / Django / Flask"]:::app
        Server["Uvicorn / Gunicorn"]:::app
    end

    subgraph KERNEL["KERNEL SPACE"]
        TCP["TCP/IP Stack"]:::kernel
        Buffers["Socket Buffers"]:::kernel
        Scheduler["Scheduler"]:::kernel
        Epoll["epoll/select"]:::kernel
    end

    NIC["🌐 NIC Driver"]:::hardware

    Internet["🌍 Internet"]:::hardware

    App --> Server

    Server -->|"syscalls"| TCP

    TCP --> Buffers
    TCP --> Scheduler
    TCP --> Epoll

    Buffers --> NIC

    NIC --> Internet
```

---

# 🔥 4. Gunicorn Worker Model

```mermaid
flowchart TB

    classDef master fill:#4a3b00,stroke:#ff9800,color:#fff
    classDef worker fill:#1b5e20,stroke:#4CAF50,color:#fff
    classDef app fill:#263238,stroke:#90a4ae,color:#fff

    Master["Gunicorn Master Process"]:::master

    W1["Worker 1"]:::worker
    W2["Worker 2"]:::worker
    W3["Worker 3"]:::worker

    Flask["Flask/Django App"]:::app

    Master --> W1
    Master --> W2
    Master --> W3

    W1 --> Flask
    W2 --> Flask
    W3 --> Flask
```

---

# 🔥 5. Uvicorn Event Loop Model

```mermaid

flowchart LR

    classDef loop fill:#1565C0,stroke:#42A5F5,color:#fff
    classDef socket fill:#263238,stroke:#90a4ae,color:#fff
    classDef app fill:#1b5e20,stroke:#4CAF50,color:#fff

    EventLoop["🔄 asyncio Event Loop"]:::loop

    Socket1["Socket A"]:::socket
    Socket2["Socket B"]:::socket
    Socket3["Socket C"]:::socket

    FastAPI["FastAPI ASGI App"]:::app

    EventLoop --> Socket1
    EventLoop --> Socket2
    EventLoop --> Socket3

    Socket1 --> FastAPI
    Socket2 --> FastAPI
    Socket3 --> FastAPI
```

---

# 🔥 6. recv() Through Kernel Boundary

```mermaid
sequenceDiagram

    participant Python as Uvicorn/Gunicorn
    participant Kernel as OS Kernel
    participant NIC as Network Card

    Python->>Kernel: recv()

    Kernel->>Kernel: check socket buffer

    alt buffer empty
        Kernel->>Python: BLOCK process/thread
    end

    NIC->>Kernel: packet arrived

    Kernel->>Kernel: copy bytes into receive buffer

    Kernel-->>Python: return bytes
```

---

# 🔥 7. Development Server vs Production Server

```mermaid
flowchart LR

    subgraph DEV["❌ Development"]
        FlaskRun["app.run()"]
        Single["single process"]
        NoWorkers["no worker management"]
    end

    subgraph PROD["✅ Production"]
        Nginx["Nginx"]
        Gunicorn["Gunicorn/Uvicorn"]
        Workers["multiple workers"]
        Buffers["socket buffering"]
    end

    FlaskRun --> Single
    Single --> NoWorkers

    Nginx --> Gunicorn
    Gunicorn --> Workers
    Workers --> Buffers
```

---

# 🔥 8. Reverse Proxy Architecture

```mermaid
flowchart LR

    classDef client fill:#263238,stroke:#90a4ae,color:#fff
    classDef proxy fill:#4a3b00,stroke:#ff9800,color:#fff
    classDef backend fill:#1b5e20,stroke:#4CAF50,color:#fff

    Browser["🌍 Browser"]:::client

    Nginx["Nginx Reverse Proxy"]:::proxy

    API1["FastAPI Worker 1"]:::backend
    API2["FastAPI Worker 2"]:::backend
    API3["FastAPI Worker 3"]:::backend

    Browser --> Nginx

    Nginx --> API1
    Nginx --> API2
    Nginx --> API3
```

---

# 🔥 9. Socket Lifecycle in Production Server

```mermaid
stateDiagram-v2

    [*] --> socket

    socket --> bind

    bind --> listen

    listen --> accept

    accept --> recv

    recv --> process_request

    process_request --> send_response

    send_response --> close

    close --> [*]
```

