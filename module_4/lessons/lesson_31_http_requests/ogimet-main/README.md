# Meteo Telegram — навчальний demo stack

**Урок 31: HTTP Protocol, REST API, requests, FastAPI, Streamlit**

---

## Архітектура системи

```
┌─────────────────────────────────────────────────────────┐
│   CLIENT — Streamlit (порт 8501)                        │
│                                                          │
│   requests.post("http://app_fastapi:8000/...")          │
│       ↓  HTTP (JSON body)                               │
└──────────────────────┬──────────────────────────────────┘
                       │  TCP через Docker network
                       ↓
┌─────────────────────────────────────────────────────────┐
│   SERVER — FastAPI (порт 8000)                          │
│                                                          │
│   @app.post("/filter_telegrams/")                       │
│   def filter_telegrams(filter: TelegramFilter): ...     │
│       ↓  PyMongo                                        │
└──────────────────────┬──────────────────────────────────┘
                       │  MongoDB protocol
                       ↓
┌─────────────────────────────────────────────────────────┐
│   DATABASE — MongoDB (порт 27017)                       │
│   Collections: ua, bel                                  │
│   Documents: {"id_telegram": "...", "data": {...}}      │
└─────────────────────────────────────────────────────────┘
                       ↓  JSON → pandas → Plotly
              [ Grafік у браузері ]
```

---

## Швидкий старт

### 1. Запуск через Docker

```bash
# Перейти в директорію проєкту
cd ogimet-main

# Зібрати і запустити всі сервіси
docker compose up --build
```

| Сервіс | URL | Що це |
|--------|-----|-------|
| Streamlit dashboard | http://localhost:8501 | Навчальний frontend |
| FastAPI Swagger | http://localhost:8000/docs | Інтерактивна документація |
| FastAPI ReDoc | http://localhost:8000/redoc | Альтернативна документація |
| MongoDB | localhost:27017 | База даних (внутрішній) |

### 2. Завантажити початкові дані

Відкрий http://localhost:8501, перейди на вкладку **⬇️ Завантажити з Ogimet**
і натисни кнопку. Або через curl:

```bash
curl -X POST "http://localhost:8000/download_telegrams?country_code=ua"
```

> ⏳ Процес займає 1–5 хвилин — Python завантажує 35+ станцій по одній (blocking I/O).

### 3. Зупинити

```bash
docker compose down
```

### 4. Зупинити та очистити базу даних

```bash
docker compose down -v
```

---

## Що таке HTTP

**HTTP (HyperText Transfer Protocol)** — це протокол передачі даних рівня застосунку (L7).
Текстовий протокол поверх TCP.

### Анатомія HTTP-запиту

```
POST /filter_telegrams/ HTTP/1.1          ← метод + шлях + версія
Host: localhost:8000                       ← адреса сервера
Content-Type: application/json            ← тип тіла
Accept: application/json                  ← що хочемо отримати
Content-Length: 52                        ← розмір тіла в байтах
                                          ← порожній рядок = кінець заголовків
{"country_code": "ua", "station_id": "33345"}  ← тіло (JSON)
```

### Анатомія HTTP-відповіді

```
HTTP/1.1 200 OK                           ← версія + статус-код + фраза
Content-Type: application/json            ← тип тіла відповіді
Content-Length: 1024                      ← розмір відповіді
                                          ← порожній рядок
{"results": [...]}                        ← тіло відповіді (JSON)
```

---

## REST API — HTTP методи

| Метод | CRUD | Idempotent? | Цей проєкт |
|-------|------|-------------|-----------|
| **GET** | Read | ✅ Так | `GET /telegram/{col}/{id}` |
| **POST** | Create / пошук | ❌ Ні | `POST /filter_telegrams/`, `POST /download_telegrams` |
| **PUT** | Update | ✅ Так | `PUT /telegram/{col}/{id}` |
| **DELETE** | Delete | ✅ Так | `DELETE /telegram/{col}/{id}` |

**Idempotent** = однаковий результат при повторних запитах.

---

## HTTP Status Codes

| Код | Назва | Коли |
|-----|-------|------|
| 200 | OK | Запит успішний |
| 201 | Created | Ресурс створено |
| 400 | Bad Request | Некоректний запит |
| 404 | Not Found | Ресурс не існує |
| 422 | Unprocessable Entity | Pydantic відхилив body |
| 500 | Internal Server Error | Помилка на сервері |

---

## Як працює FastAPI

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class TelegramFilter(BaseModel):
    country_code: str | None = None
    station_id: str | None = None

# Цей декоратор реєструє функцію як обробник POST /filter_telegrams/
@app.post("/filter_telegrams/")
def filter_telegrams(filter: TelegramFilter):
    # filter — вже десеріалізований Python об'єкт (не рядок!)
    # FastAPI автоматично:
    #   1. Прочитав JSON body
    #   2. Валідував через Pydantic
    #   3. Передав у функцію
    results = db.find({"data.country": filter.country_code})
    return {"results": list(results)}   # ← FastAPI серіалізує у JSON
```

---

## Як працює requests (клієнт)

```python
import requests

# 1. Серіалізація: dict → JSON bytes
# 2. DNS: "localhost" → 127.0.0.1
# 3. TCP: з'єднання з 127.0.0.1:8000
# 4. HTTP: надсилаємо запит
# 5. BLOCKING: Python спить поки сервер не відповість
# 6. Deserialization: JSON bytes → dict
response = requests.post(
    "http://localhost:8000/filter_telegrams/",
    json={"country_code": "ua"},   # json= автоматично встановлює Content-Type: application/json
    timeout=(5.0, 60.0),           # ЗАВЖДИ! (connect, read)
)

# Перевірка статусу
print(response.status_code)   # 200
response.raise_for_status()   # кидає HTTPError якщо >= 400

# Отримання даних
data = response.json()         # JSON → dict
records = data["results"]      # list of dicts

# Інспекція запиту (що реально пішло по дроту)
print(response.request.headers)  # заголовки запиту
print(response.request.body)     # тіло запиту (bytes)
```

---

## API Endpoints — приклади

### GET — отримати одну телеграму

```bash
curl http://localhost:8000/telegram/ua/3450420249218
```

```python
response = requests.get("http://localhost:8000/telegram/ua/3450420249218")
print(response.json())
```

### POST — фільтрувати телеграми

```bash
curl -X POST http://localhost:8000/filter_telegrams/ \
     -H "Content-Type: application/json" \
     -d '{"country_code": "ua", "station_id": "33345", "fields_to_return": ["temperature", "year", "month", "day", "hour"]}'
```

```python
response = requests.post(
    "http://localhost:8000/filter_telegrams/",
    json={
        "country_code": "ua",
        "station_id": "33345",
        "fields_to_return": ["temperature", "year", "month", "day", "hour"],
    },
    timeout=(5.0, 30.0),
)
data = response.json()["results"]
```

### PUT — оновити поле

```bash
curl -X PUT http://localhost:8000/telegram/ua/3450420249218 \
     -H "Content-Type: application/json" \
     -d '{"temperature": 25.5}'
```

```python
response = requests.put(
    "http://localhost:8000/telegram/ua/3450420249218",
    json={"temperature": 25.5},
    timeout=(5.0, 10.0),
)
```

### DELETE — видалити запис

```bash
curl -X DELETE http://localhost:8000/telegram/ua/3450420249218
```

---

## ngrok — публічний доступ

ngrok створює публічний HTTPS тунель до твого локального сервера.
Студенти можуть тестувати API через інтернет без деплою.

### Запуск

```bash
# 1. Запусти Docker
docker compose up --build

# 2. В іншому терміналі — ngrok
ngrok http 8000

# Побачиш:
# Forwarding  https://d247-91-237-25-10.ngrok-free.app -> http://localhost:8000
```

### Swagger через ngrok

```
https://d247-91-237-25-10.ngrok-free.app/docs
```

### requests через ngrok URL

```python
import requests

BASE_URL = "https://d247-91-237-25-10.ngrok-free.app"

# Будь-який запит — через публічний інтернет!
response = requests.post(
    f"{BASE_URL}/filter_telegrams/",
    json={"country_code": "ua"},
    timeout=(5.0, 30.0),
)
print(response.json())
```

> **Примітка:** безкоштовний ngrok генерує новий URL при кожному запуску.

---

## Swagger UI — як тестувати

1. Відкрий http://localhost:8000/docs
2. Натисни на endpoint (наприклад `POST /filter_telegrams/`)
3. Натисни **"Try it out"**
4. Відредагуй JSON body
5. Натисни **"Execute"**
6. Бачиш: curl команду, request URL, response body, status code

---

## Структура проєкту

```
ogimet-main/
├── docker-compose.yaml          ← 3 сервіси: FastAPI, Streamlit, MongoDB
├── README.md                    ← цей файл
└── meteo_telegram/
    ├── Dockerfile               ← Python 3.11-slim, всі залежності
    ├── requirements.txt         ← FastAPI, Streamlit, Plotly, pymongo...
    ├── main.py                  ← FastAPI application (5 endpoints)
    ├── streamlit_app.py         ← Навчальний dashboard (новий!)
    ├── mongo_db/
    │   └── mongo_tools.py       ← MongoDB CRUD helper
    └── telegram_decode/
        ├── telegram_factory.py  ← фабрика процесорів
        ├── meteo_ogimet.py      ← HTTP запити до ogimet.com
        └── class_metedecode.py  ← декодер SYNOP телеграм
```

---

## Локальний запуск (без Docker)

```bash
cd meteo_telegram

pip install -r requirements.txt

# FastAPI (потрібен локальний MongoDB)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Streamlit (в іншому терміналі)
API_URL=http://localhost:8000 streamlit run streamlit_app.py
```

---

*Урок 31 — HTTP Protocol & REST API | Python Course Viktor Nikoriak*
