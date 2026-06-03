# Redis Socket Lesson

Цей mini-project показує Redis не як "магічну базу", а як реальний TCP server.

Redis у Docker слухає порт:

```yaml
ports:
  - "6379:6379"
```

Тобто Python може підключитися до Redis напряму через socket:

```text
Python Process
↓
TCP socket
↓
OS Send Buffer
↓
Docker port forwarding
↓
Redis container
↓
Redis RESP parser
```

## Перед запуском

Переконайся, що Redis container запущений:

```bash
docker compose up -d redis
```

або:

```bash
docker ps
```

Має бути щось типу:

```text
0.0.0.0:6379->6379/tcp
```

## Файли

### 01_check_redis_socket.py

Перевіряє, що Redis реально слухає TCP port 6379.

### 02_raw_ping.py

Надсилає Redis команду `PING` вручну через RESP protocol.

### 03_raw_set_get.py

Надсилає `SET` і `GET` через raw TCP socket.

### 04_resp_client.py

Маленький навчальний RESP client:
- сам збирає RESP command;
- сам відправляє bytes;
- сам читає Redis response.

### 05_partial_send_demo.py

Показує, що Redis може отримувати команду частинами, бо TCP — byte stream.

## Головна ідея уроку

Коли ми пишемо:

```python
sock.sendall(...)
```

ми не "викликаємо Redis функцію".

Ми відправляємо bytes у TCP stream.

Redis сам:
- читає bytes;
- буферизує їх;
- парсить RESP protocol;
- відновлює команду;
- виконує її у своїй пам'яті.

# 🔥 1. Redis як TCP Socket Server

```mermaid
flowchart LR
    classDef client fill:#1b5e20,stroke:#4CAF50,color:#fff
    classDef server fill:#4a3b00,stroke:#ff9800,color:#fff
    classDef network fill:#263238,stroke:#90a4ae,color:#fff

    Client["Python Client\nsocket()"]:::client
    TCP["TCP Socket\nlocalhost:6379"]:::network
    Redis["Redis Server\nRESP Protocol"]:::server

    Client -->|"connect()"| TCP
    TCP --> Redis
    Redis -->|"PONG"| Client
```

---

# 🔥 2. RESP Protocol Architecture

```mermaid
flowchart TB
    classDef raw fill:#4e1f1f,stroke:#f44336,color:#fff
    classDef parsed fill:#1b5e20,stroke:#4CAF50,color:#fff
    classDef redis fill:#4a3b00,stroke:#ff9800,color:#fff

    Raw["Raw TCP Bytes\n*1\r\n$4\r\nPING\r\n"]:::raw
    Parser["RESP Parser"]:::parsed
    Redis["Redis Command Engine"]:::redis
    Response["Simple String\n+PONG\r\n"]:::raw

    Raw --> Parser
    Parser --> Redis
    Redis --> Response
```

---

# 🔥 3. Socket Communication Flow

```mermaid
sequenceDiagram
    participant C as Python Client
    participant R as Redis

    C->>R: TCP connect()
    C->>R: PING
    R-->>C: PONG

    C->>R: SET name Viktor
    R-->>C: OK

    C->>R: GET name
    R-->>C: Viktor
```

---

# 🔥 4. Raw RESP Message Structure

```mermaid
flowchart TD
    classDef cmd fill:#1b5e20,stroke:#4CAF50,color:#fff
    classDef len fill:#4a3b00,stroke:#ff9800,color:#fff
    classDef data fill:#263238,stroke:#90a4ae,color:#fff

    A["*3\nArray of 3 elements"]:::len
    B["$3\nLength = 3"]:::len
    C["SET"]:::cmd
    D["$4\nLength = 4"]:::len
    E["name"]:::data
    F["$6\nLength = 6"]:::len
    G["Viktor"]:::data

    A --> B --> C --> D --> E --> F --> G
```

---

# 🔥 5. Partial Send Problem (`05_partial_send_demo.py`)

```mermaid
flowchart LR
    classDef sender fill:#1b5e20,stroke:#4CAF50,color:#fff
    classDef network fill:#4a3b00,stroke:#ff9800,color:#fff
    classDef receiver fill:#4e1f1f,stroke:#f44336,color:#fff

    Client["Client\nsend(1000 bytes)"]:::sender

    Chunk1["400 bytes"]:::network
    Chunk2["350 bytes"]:::network
    Chunk3["250 bytes"]:::network

    Server["Server recv()\nотримує частинами"]:::receiver

    Client --> Chunk1
    Client --> Chunk2
    Client --> Chunk3

    Chunk1 --> Server
    Chunk2 --> Server
    Chunk3 --> Server
```

---

# 🔥 6. Naive Task Queue Architecture

```mermaid
flowchart LR
    classDef api fill:#1b5e20,stroke:#4CAF50,color:#fff
    classDef redis fill:#4a3b00,stroke:#ff9800,color:#fff
    classDef worker fill:#263238,stroke:#90a4ae,color:#fff

    Producer["Producer\n06_naive_task_queue.py"]:::api
    Redis["Redis List Queue"]:::redis
    Worker["Worker\n07_naive_worker.py"]:::worker

    Producer -->|"LPUSH tasks"| Redis
    Worker -->|"BRPOP tasks"| Redis
```

---

# 🔥 7. Celery-style Mental Model

```mermaid
flowchart TB
    classDef api fill:#1b5e20,stroke:#4CAF50,color:#fff
    classDef broker fill:#4a3b00,stroke:#ff9800,color:#fff
    classDef worker fill:#263238,stroke:#90a4ae,color:#fff
    classDef result fill:#4e1f1f,stroke:#f44336,color:#fff

    API["FastAPI / App"]:::api
    Redis["Redis Broker"]:::broker
    Worker["Celery Worker"]:::worker
    Result["Result Backend"]:::result

    API -->|"enqueue task"| Redis
    Worker -->|"consume task"| Redis
    Worker -->|"store result"| Result
```

---

# 🔥 8. Stack vs Queue (для BFS/Task Queue пояснення)

```mermaid
flowchart LR

    subgraph STACK["STACK (LIFO)"]
        S1["A"] --> S2["B"] --> S3["C"]
    end

    subgraph QUEUE["QUEUE (FIFO)"]
        Q1["A"] --> Q2["B"] --> Q3["C"]
    end
```

---

| File                       | Mermaid Diagram      |
| -------------------------- | -------------------- |
| `01_check_redis_socket.py` | Redis TCP Socket     |
| `02_raw_ping.py`           | Socket Communication |
| `03_raw_set_get.py`        | RESP Structure       |
| `04_resp_client.py`        | RESP Parser          |
| `05_partial_send_demo.py`  | Partial Send         |
| `06_naive_task_queue.py`   | Task Queue           |
| `07_naive_worker.py`       | Worker Architecture  |

---