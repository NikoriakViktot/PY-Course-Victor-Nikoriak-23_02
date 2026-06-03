# Docker: Повний практичний посібник

> **Модуль 3 — Python Advanced · Віктор Нікоряк**  
> Посібник досвідченого інженера з Docker: ментальні моделі, архітектура, реальні робочі процеси та продакшн-патерни.

---

## Зміст

0. [Встановлення Docker](#0-встановлення-docker)
1. [Що таке Docker (ментальна модель)](#1-що-таке-docker-ментальна-модель)
2. [Основні концепції](#2-основні-концепції)
3. [Огляд архітектури](#3-огляд-архітектури)
4. [Робочий процес Docker (реальний lifecycle)](#4-робочий-процес-docker-реальний-lifecycle)
5. [Основні команди Docker](#5-основні-команди-docker)
6. [Docker Compose (багатоконтейнерні системи)](#6-docker-compose-багатоконтейнерні-системи)
7. [Volumes та збереження даних](#7-volumes-та-збереження-даних)
8. [Мережі (Networking)](#8-мережі-networking)
9. [Типові помилки](#9-типові-помилки)
10. [Найкращі практики](#10-найкращі-практики)
11. [Офіційні образи для курсу Python Advanced](#11-офіційні-образи-для-курсу-python-advanced)

---

## 0. Встановлення Docker

Офіційна сторінка для завантаження та встановлення Docker Desktop (Windows, macOS, Linux):

> **[https://www.docker.com/](https://www.docker.com/)**

### Кроки встановлення (Windows / macOS)

1. Перейдіть на [https://www.docker.com/](https://www.docker.com/)
2. Натисніть **"Download Docker Desktop"**
3. Запустіть інсталятор та дотримуйтесь інструкцій
4. Після встановлення перевірте:

```bash
docker --version
# Docker version 26.x.x, build ...

docker compose version
# Docker Compose version v2.x.x
```

### Перша перевірка

```bash
docker run hello-world
# Якщо побачили "Hello from Docker!" — встановлення успішне
```

### Docker Hub — реєстр образів

Після встановлення Docker зареєструйтеся на **[Docker Hub](https://hub.docker.com/)** — головному публічному реєстрі Docker-образів.

```bash
docker login               # увійти в Docker Hub з термінала
docker logout              # вийти
```

Docker Hub містить офіційні образи для:
- **Мов**: `python`, `node`, `golang`, `java`
- **БД**: `postgres`, `mysql`, `redis`, `mongodb`
- **Веб-серверів**: `nginx`, `traefik`, `caddy`
- **Ваших власних додатків**: завантаженних командою `docker push`

---

## 1. Що таке Docker (ментальна модель)

### Проблема, яку вирішує Docker

До Docker розгортання ПЗ означало постійну відповідь на питання:

> *"У мене на машині працює — чому на сервері падає?"*

Відповідь завжди була однаковою: **середовище різне**. Різна ОС, різні версії бібліотек, різні системні залежності, різні шляхи Python.

Docker вирішує це, пакуючи не тільки ваш код — але й **усе виконавче середовище**, від якого залежить ваш код.

### Правильна ментальна модель: Вантажний контейнер

До контейнерних перевезень вантаж завантажували на кораблі як окремі предмети. Завантаження та розвантаження було повільним, ненадійним і різним у кожному порту.

Винахід **стандартизованого вантажного контейнера** змінив все:
- **Один і той самий контейнер** підходить для будь-якого корабля, вантажівки або крана
- Вміст не залежить від транспортного засобу
- Транспортний засіб не залежить від вмісту

Docker — це саме так, але для програмного забезпечення:

| Фізичні перевезення | Docker |
|---------------------|--------|
| Вантажний контейнер | Docker-контейнер |
| Товари всередині | Ваш додаток + залежності |
| Корабель / вантажівка | Будь-який сервер з Docker |
| Портова інфраструктура | Docker daemon |
| Стандарт специфікації контейнера | OCI (Open Container Initiative) |

### Чим Docker НЕ є

Docker — це **не** віртуальна машина. Це найпоширеніша помилкова думка.

```
Віртуальна машина:                Docker-контейнер:

┌─────────────────────┐           ┌─────────────────────┐
│    Ваш додаток      │           │    Ваш додаток      │
├─────────────────────┤           ├─────────────────────┤
│    Guest OS         │           │    Libs/Deps        │
│    (повна Linux/Win)│           │    (без ядра ОС!)   │
├─────────────────────┤           ├─────────────────────┤
│    Гіпервізор       │           │    Docker Engine    │
├─────────────────────┤           ├─────────────────────┤
│    Host OS          │           │  Host OS (спільне)  │
├─────────────────────┤           ├─────────────────────┤
│    Фізичне залізо   │           │    Фізичне залізо   │
└─────────────────────┘           └─────────────────────┘

Розмір: ~1–10 ГБ                  Розмір: ~10–500 МБ
Завантаження: ~30–60 сек          Завантаження: ~0.1–2 сек
```

**Ключова різниця:** Контейнери спільно використовують **ядро ОС хоста**. Вони не емулюють апаратне забезпечення. Це робить їх значно швидшими та легшими за VM.

### Навіщо Docker: три осі болю

| Біль | Без Docker | З Docker |
|------|-----------|----------|
| **Drift середовища** | "Працює на моїй машині" | Ідентичне середовище скрізь |
| **Пекло залежностей** | Конфлікти Python 3.8 vs 3.11 | Кожен додаток — власні ізольовані бібліотеки |
| **Складність розгортання** | Ansible-скрипти, SSH, ручні кроки | `docker run` на будь-якій машині |

---

## 2. Основні концепції

### 2.1 Image (Образ)

**Визначення:** Docker-образ — це **незмінний, шарований знімок файлової системи**, що містить усе необхідне для запуску додатку: бібліотеки ОС, runtime, залежності, код додатку та команду запуску.

**Ментальна модель:** Образ — це **рецепт** (або клас в ООП). Він визначає, як виглядатиме контейнер, але сам нічого не запускає.

**Роль у системі:**
- Будується один раз, запускається багато разів
- Зберігається у реєстрах (Docker Hub, AWS ECR, GitHub Container Registry)
- Ідентифікується назвою + тегом: `python:3.11-slim`, `nginx:1.25`, `myapp:v2.3`

**Зв'язок з іншими:**
- `Dockerfile` → збирає → `Image`
- `Image` → інстанціюється у → `Container`
- Образи складаються з **шарів** — кожна інструкція `RUN`, `COPY`, `ADD` у Dockerfile створює новий шар

```
Архітектура шарів образу:

Шар 4: COPY app/ /app          ← ваш код (змінюється часто)
Шар 3: RUN pip install -r ...  ← залежності (змінюються іноді)
Шар 2: RUN apt-get install ... ← системні бібліотеки (рідко змінюються)
Шар 1: FROM python:3.11-slim   ← базовий образ (спільний між образами)
```

Шари **кешуються та спільно використовуються**. Якщо шари 1–3 не змінилися, Docker їх перевикористовує — перебудовується лише шар 4. Ось чому **порядок шарів важливий**.

---

### 2.2 Container (Контейнер)

**Визначення:** Контейнер — це **запущений екземпляр образу**. Це ізольований процес на ОС хоста з власною файловою системою, мережевим інтерфейсом і простором процесів.

**Ментальна модель:** Якщо образ — це клас, то контейнер — це **об'єкт** — екземпляр, створений з цього класу. З одного образу можна створити багато контейнерів.

**Роль у системі:**
- Виконує реальне навантаження
- Має **шар запису** поверх незмінних шарів образу
- За замовчуванням **ефемерний** — після зупинки та видалення всі записані дані втрачаються
- Має lifecycle: `created → running → paused → stopped → removed`

```
Контейнер = Шари образу (незмінні) + Шар запису (ефемерний)

┌──────────────────────────────────┐
│  Шар запису (дані контейнера)    │ ← втрачається при rm
├──────────────────────────────────┤
│  Шар образу 4: код додатку       │ ← тільки читання
│  Шар образу 3: pip пакети        │ ← тільки читання
│  Шар образу 2: системні бібл.    │ ← тільки читання
│  Шар образу 1: базова ОС         │ ← тільки читання (спільний)
└──────────────────────────────────┘
```

---

### 2.3 Volume (Том)

**Визначення:** Docker volume — це **керований механізм зберігання**, що існує поза шаром запису контейнера. Дані у volume зберігаються навіть після видалення контейнера.

**Ментальна модель:** Volume — це **USB-флешка**, яку ви підключаєте до контейнера. Контейнер можна видалити, але USB-флешка — і її дані — залишаються.

**Роль у системі:**
- Зберігає постійні дані: бази даних, завантажені файли, логи
- Може бути спільним для кількох контейнерів
- Управляється Docker (зберігається у `/var/lib/docker/volumes/` на Linux)

**Типи:**

| Тип | Синтаксис | Випадок використання |
|-----|-----------|----------------------|
| **Named volume** | `mydata:/app/data` | Продакшн БД, постійні дані додатку |
| **Bind mount** | `/host/path:/container/path` | Розробка — live перезавантаження коду |
| **tmpfs mount** | `tmpfs:/app/cache` | Чутливі дані, які не повинні потрапити на диск |

---

### 2.4 Network (Мережа)

**Визначення:** Docker network — це **шар віртуальної мережі**, що дозволяє контейнерам спілкуватися між собою та із зовнішнім світом.

**Ментальна модель:** Мережа — це **приватна офісна LAN**. Контейнери в одній мережі можуть звертатися один до одного за іменем сервісу (як за hostname). Контейнери в різних мережах ізольовані.

**Роль у системі:**
- Забезпечує комунікацію між сервісами (API → База даних)
- Ізолює середовища (продакшн і стейджинг-контейнери не бачать один одного)
- Контролює, що доступно з хост-машини (опубліковані порти)

**Вбудовані драйвери мереж:**

| Драйвер | Опис |
|---------|------|
| `bridge` | Стандартний. Ізольована віртуальна мережа на хості. Контейнери спілкуються за іменем сервісу |
| `host` | Контейнер використовує мережевий стек хоста. Немає ізоляції — використовується рідко |
| `none` | Без мережі. Повна ізоляція |
| `overlay` | Багатохостова мережа. Використовується у Docker Swarm / Kubernetes |

---

## 3. Огляд архітектури

```mermaid
flowchart TD
    classDef user fill:#263238,stroke:#90a4ae,color:#fff
    classDef cli fill:#1b5e20,stroke:#4caf50,color:#fff
    classDef daemon fill:#37474f,stroke:#64b5f6,color:#fff
    classDef resource fill:#4a3b00,stroke:#ff9800,color:#fff
    classDef registry fill:#4e1f1f,stroke:#f44336,color:#fff

    User([Розробник / CI Pipeline]):::user
    CLI[Docker CLI\ndocker build / run / push]:::cli
    Daemon[Docker Daemon\ndockerd]:::daemon
    Registry[(Docker Registry\nHub / ECR / GHCR)]:::registry
    Images[(Images\nнезмінні шари)]:::resource
    Containers[(Containers\nзапущені процеси)]:::resource
    Volumes[(Volumes\nпостійне сховище)]:::resource
    Networks[(Networks\nвіртуальні LAN)]:::resource

    User --> CLI
    CLI -->|REST API / Unix socket| Daemon
    Daemon -->|push / pull| Registry
    Daemon --> Images
    Daemon -->|інстанціює| Containers
    Containers -->|монтує| Volumes
    Containers -->|підключається до| Networks
    Images -->|незмінна основа для| Containers
```

### Пояснення діаграми

**1. Розробник → Docker CLI**  
Кожна команда Docker (`docker build`, `docker run`, `docker ps`) обробляється **Docker CLI** — клієнтським інструментом. CLI сам по собі не виконує важку роботу.

**2. Docker CLI → Docker Daemon**  
CLI спілкується з **Docker Daemon** (`dockerd`) через REST API по Unix-сокету (`/var/run/docker.sock`). Daemon — це фонова служба, яка фактично всім керує. Саме тому іноді виникають помилки "permission denied" — потрібен доступ до цього сокету.

**3. Daemon → Registry**  
Коли ви виконуєте `docker pull python:3.11` або `docker push myapp:v2`, daemon підключається до **реєстру** — віддаленого сховища образів. Docker Hub — стандартний публічний реєстр. Компанії використовують приватні реєстри (AWS ECR, GitHub Container Registry).

**4. Images → Containers**  
Daemon використовує образи як незмінні базові шари. Під час запуску контейнера Docker додає тонкий шар запису поверх шарів образу.

**5. Containers → Volumes & Networks**  
Запущені контейнери взаємодіють із зовнішнім світом через:
- **Volumes** — для читання/запису постійних даних
- **Networks** — для спілкування з іншими контейнерами або публікації портів на хості

---

## 4. Робочий процес Docker (реальний lifecycle)

```mermaid
flowchart LR
    classDef step fill:#263238,stroke:#90a4ae,color:#fff
    classDef action fill:#1b5e20,stroke:#4caf50,color:#fff
    classDef artifact fill:#4a3b00,stroke:#ff9800,color:#fff

    Code([1. Пишемо код\n+ Dockerfile]):::step
    Build([2. docker build\nСтворюємо Image]):::action
    Image[(Image\nv1.0)]:::artifact
    Run([3. docker run\nЗапускаємо контейнер]):::action
    Container([4. Запущений\nконтейнер]):::step
    Debug([5. Дебаг\ndocker logs / exec]):::step
    Fix([6. Виправляємо код]):::step
    Push([7. docker push\nДо реєстру]):::action
    Registry[(Registry\nHub / ECR)]:::artifact

    Code --> Build --> Image --> Run --> Container
    Container --> Debug --> Fix --> Build
    Image --> Push --> Registry
```

### Покроково: реальний процес розробника

**Крок 1 — Пишемо код + Dockerfile**

Ви пишете свій додаток І `Dockerfile`, що описує, як його запакувати. Dockerfile живе у вашому репозиторії поруч із кодом.

```dockerfile
# Приклад: Python FastAPI сервіс
FROM python:3.11-slim                   # базовий образ

WORKDIR /app                            # робоча директорія всередині контейнера

COPY requirements.txt .                 # спочатку копіюємо тільки requirements (кеш шару)
RUN pip install --no-cache-dir -r requirements.txt  # встановлюємо залежності

COPY . .                               # копіюємо код додатку

EXPOSE 8000                            # документуємо, який порт використовує додаток
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Крок 2 — `docker build`: Створюємо образ**

```bash
docker build -t myapi:v1.0 .
```

Docker читає `Dockerfile` зверху вниз, виконує кожну інструкцію і створює новий шар для кожної. Результат — образ з тегом `myapi:v1.0`.

**Крок 3 — `docker run`: Запускаємо контейнер**

```bash
docker run -d -p 8000:8000 --name api-server myapi:v1.0
```

Docker створює контейнер з образу і запускає його. `-d` запускає у фоні. `-p 8000:8000` прокидає порт 8000 хоста на порт 8000 всередині контейнера.

**Крок 4 — Запущений контейнер**

Ваш додаток зараз працює в ізольованому середовищі. Він має власну файлову систему, мережу та простір процесів, але спільно використовує ядро хоста.

**Крок 5 — Дебаг**

```bash
docker logs api-server          # переглянути stdout/stderr
docker logs -f api-server       # слідкувати за логами в реальному часі
docker exec -it api-server sh   # відкрити shell всередині запущеного контейнера
```

**Крок 6 — Виправляємо код → Перебудовуємо**

Знайшли баг. Виправте код, потім перебудуйте образ. Кеш шарів Docker означає, що перебудовуються лише змінені шари — зазвичай швидко.

```bash
# Тільки шар COPY . . перебудовується, якщо код змінився
docker build -t myapi:v1.1 .
```

**Крок 7 — Push до реєстру**

```bash
docker tag myapi:v1.1 ghcr.io/myorg/myapi:v1.1
docker push ghcr.io/myorg/myapi:v1.1
```

Образ тепер доступний для будь-якого сервера, CI/CD пайплайну або колеги.

---

## 5. Основні команди Docker

### Lifecycle контейнера

#### `docker run`

```bash
docker run [OPTIONS] IMAGE [COMMAND]
```

Створює і запускає новий контейнер з образу.

| Прапор | Значення |
|--------|----------|
| `-d` | Фоновий режим (detached) |
| `-p HOST:CONTAINER` | Публікуємо порт |
| `--name NAME` | Даємо контейнеру ім'я |
| `-e KEY=VALUE` | Встановлюємо змінну середовища |
| `-v VOLUME:PATH` | Монтуємо volume |
| `--rm` | Автоматично видалити контейнер після зупинки |
| `-it` | Інтерактивний + псевдо-TTY (для shell) |

```bash
# Реальні приклади:
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=secret --name pg postgres:15
docker run --rm -it python:3.11-slim bash
docker run -d -p 8000:8000 -v mydata:/app/data --name api myapi:v1.0
```

**Типова помилка:** Забути `-d` і заблокувати термінал, або забути `--rm` і накопичувати зупинені контейнери.

---

#### `docker start` / `docker stop` / `docker restart`

```bash
docker stop api-server          # коректна зупинка (SIGTERM → SIGKILL через 10с)
docker start api-server         # запустити зупинений контейнер
docker restart api-server       # зупинити + запустити
docker kill api-server          # негайна зупинка (SIGKILL, без grace period)
```

**Типова помилка:** Використання `docker kill` в продакшні — завжди надавайте перевагу `docker stop` для коректного завершення.

---

#### `docker ps`

```bash
docker ps               # запущені контейнери
docker ps -a            # всі контейнери (включно із зупиненими)
docker ps -q            # тільки ID контейнерів (корисно для скриптів)
```

```bash
# Зупинити всі запущені контейнери:
docker stop $(docker ps -q)

# Видалити всі зупинені контейнери:
docker rm $(docker ps -aq -f status=exited)
```

---

#### `docker rm`

```bash
docker rm api-server            # видалити зупинений контейнер
docker rm -f api-server         # примусово видалити (навіть запущений)
```

**Типова помилка:** Плутати `docker stop` (коректно зупиняє) з `docker rm` (видаляє). Потрібно спочатку зупинити, а потім видалити, або використати `-f`.

---

### Керування образами

#### `docker build`

```bash
docker build -t NAME:TAG CONTEXT_PATH
```

```bash
docker build -t myapp:1.0 .                       # з поточної директорії
docker build -t myapp:1.0 -f Dockerfile.prod .    # кастомна назва Dockerfile
docker build --no-cache -t myapp:1.0 .            # ігнорувати кеш шарів (чиста збірка)
docker build --target builder -t myapp:dev .      # збірка до конкретного стейджу (multi-stage)
```

**Типова помилка:** Збірка з неправильного контексту (`.` означає "відправити поточну директорію до daemon"). Великі директорії уповільнюють збірку. Використовуйте `.dockerignore`.

---

#### `docker pull` / `docker push`

```bash
docker pull python:3.11-slim                      # завантажити з реєстру
docker push ghcr.io/myorg/myapp:v1.0              # завантажити до реєстру
```

---

#### `docker images`

```bash
docker images                   # список всіх локальних образів
docker images -q                # тільки ID образів
docker images myapp             # фільтр за назвою
```

---

#### `docker tag`

```bash
docker tag SOURCE_IMAGE TARGET_IMAGE
docker tag myapp:1.0 ghcr.io/myorg/myapp:1.0
docker tag myapp:1.0 myapp:latest
```

**Типова помилка:** Думати, що `tag` створює копію. Він створює **псевдонім** — обидві назви вказують на ті самі шари образу.

---

### Дебаг та інспекція

#### `docker logs`

```bash
docker logs api-server          # вивести всі логи
docker logs -f api-server       # слідкувати (аналог tail -f)
docker logs --tail 50 api-server        # останні 50 рядків
docker logs --since 10m api-server      # логи за останні 10 хвилин
```

**Типова помилка:** Не використовувати `-f` при дебазі запущеного сервісу — потрібен потік.

---

#### `docker exec`

```bash
docker exec -it CONTAINER COMMAND
```

Виконує команду **всередині вже запущеного** контейнера без його зупинки.

```bash
docker exec -it api-server bash         # відкрити bash shell
docker exec -it api-server sh           # відкрити sh (для alpine образів)
docker exec api-server env              # вивести змінні середовища
docker exec -it pg psql -U postgres     # підключитися до PostgreSQL всередині контейнера
```

**Типова помилка:** Використовувати `docker exec` для "виправлення" шляхом ручного редагування файлів всередині запущеного контейнера. Ця зміна **втрачається при перезапуску**. Завжди виправляйте у Dockerfile або коді додатку.

---

#### `docker inspect`

```bash
docker inspect CONTAINER|IMAGE
docker inspect api-server | python3 -m json.tool   # форматований вивід
docker inspect -f '{{.NetworkSettings.IPAddress}}' api-server  # витягнути конкретне поле
```

Повертає повні JSON-метадані: мережа, монтування, змінні середовища, стан тощо.

---

#### `docker stats`

```bash
docker stats                    # використання ресурсів для всіх контейнерів
docker stats api-server         # конкретний контейнер
```

Показує CPU%, використання пам'яті, мережевий та дисковий I/O в реальному часі. Аналог `htop` для контейнерів.

---

### Очищення системи

```bash
# Видалити зупинені контейнери
docker container prune

# Видалити невикористані образи (не посилаються жодним контейнером)
docker image prune

# Видалити dangling образи (без тегів, від старих збірок)
docker image prune -a

# Видалити невикористані volumes
docker volume prune

# Видалити невикористані мережі
docker network prune

# Ядерна опція: видалити ВСЕ невикористане (контейнери, образи, мережі, кеш збірки)
docker system prune -a --volumes
```

**Типова помилка:** Запускати `docker system prune` на продакшн-сервері без перевірки "невикористаного" — може видалити образи, на які посилаються зупинені контейнери, які ви збираєтесь перезапустити.

**Спочатку перевірте використання диска:**

```bash
docker system df        # показує використання диска образами, контейнерами, volumes
```

---

## 6. Docker Compose (багатоконтейнерні системи)

### Навіщо потрібен Compose

Реальні додатки ніколи не є одним контейнером. Типовий веб-сервіс має:

```
Ваш API (Python/FastAPI)
    + PostgreSQL база даних
    + Redis кеш
    + Celery worker
    + Nginx reverse proxy
```

Управління цим за допомогою окремих команд `docker run` — болісне:
- Потрібно пам'ятати точні прапори для кожного сервісу
- Потрібно вручну створювати мережі та volumes
- Запуск/зупинка вимагають виконання 5+ команд у правильному порядку
- Змінні середовища та секрети потрібно передавати вручну кожного разу

Docker Compose вирішує це за допомогою **єдиного `docker-compose.yml`**, що декларативно визначає всі сервіси, їх конфігурацію та спосіб з'єднання.

```mermaid
flowchart TD
    classDef service fill:#263238,stroke:#90a4ae,color:#fff
    classDef data fill:#1b5e20,stroke:#4caf50,color:#fff
    classDef proxy fill:#4a3b00,stroke:#ff9800,color:#fff

    Nginx[Nginx\nПорт 80/443]:::proxy
    WebApp[FastAPI\nПорт 8000]:::service
    Worker[Celery Worker\nбез порту]:::service
    Database[(PostgreSQL\nПорт 5432)]:::data
    Redis[(Redis\nПорт 6379)]:::data

    Nginx -->|proxy_pass| WebApp
    WebApp -->|SQL запити| Database
    WebApp -->|черга задач| Redis
    Worker -->|обробка задач| Redis
    Worker -->|SQL запис| Database
```

### Реальний `docker-compose.yml`

```yaml
version: "3.9"

services:
  api:
    build: ./services/api          # збірка з локального Dockerfile
    ports:
      - "8000:8000"                # публікуємо для хоста
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
      - REDIS_URL=redis://redis:6379
    depends_on:
      db:
        condition: service_healthy  # чекаємо готовності БД
      redis:
        condition: service_started
    volumes:
      - ./services/api:/app        # bind mount для розробки (live reload)
    networks:
      - backend

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: mydb
    volumes:
      - pgdata:/var/lib/postgresql/data   # named volume для збереження
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d mydb"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - backend

  redis:
    image: redis:7-alpine
    networks:
      - backend

  worker:
    build: ./services/worker
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    networks:
      - backend

volumes:
  pgdata:                          # Docker-керований постійний volume

networks:
  backend:                         # ізольована віртуальна мережа для всіх сервісів
    driver: bridge
```

### Як сервіси спілкуються між собою

Всередині Compose-мережі **кожен сервіс доступний за своєю назвою як hostname**.

```
З контейнера 'api':
  Підключитися до PostgreSQL: postgresql://user:pass@db:5432/mydb
                                                      ^^
                                                      ім'я сервісу = hostname

  Підключитися до Redis: redis://redis:6379
                                ^^^^^
                                ім'я сервісу = hostname
```

Вбудований DNS-резолвер Docker автоматично обробляє відповідність імен до IP-адрес. IP-адреси не потрібно прописувати вручну.

### Основні команди Compose

```bash
docker compose up                   # запустити всі сервіси (передній план)
docker compose up -d                # запустити всі сервіси (фон)
docker compose up --build           # перебудувати образи перед запуском
docker compose down                 # зупинити та видалити контейнери + мережі
docker compose down -v              # також видалити volumes (ОБЕРЕЖНО: втрата даних)
docker compose logs -f api          # слідкувати за логами конкретного сервісу
docker compose exec api bash        # shell у запущеному сервісі
docker compose ps                   # список запущених сервісів
docker compose restart api          # перезапустити один сервіс
docker compose build api            # перебудувати образ тільки одного сервісу
```

---

## 7. Volumes та збереження даних

### Чому контейнери ефемерні

Кожен контейнер має **шар запису** поверх шарів образу. Коли контейнер видаляється, цей шар видаляється. Це навмисно — робить контейнери одноразовими та відтворюваними.

```
Lifecycle контейнера та дані:

docker run postgres → [Контейнер A] записує дані в шар запису
docker rm [Контейнер A] → УСІ ДАНІ ВИДАЛЕНО

docker run postgres → [Контейнер B] стартує ПОРОЖНІМ
```

Це особливість, а не баг. Але це означає, що ви повинні явно обирати збереження.

```mermaid
flowchart LR
    classDef container fill:#263238,stroke:#90a4ae,color:#fff
    classDef volume fill:#1b5e20,stroke:#4caf50,color:#fff
    classDef host fill:#4a3b00,stroke:#ff9800,color:#fff
    classDef lost fill:#4e1f1f,stroke:#f44336,color:#fff

    subgraph "Контейнер (ефемерний)"
        App[Додаток]:::container
        WritableLayer[Шар запису\nвтрачається при rm]:::lost
    end

    subgraph "Постійне сховище"
        NamedVolume[(Named Volume\npgdata)]:::volume
        BindMount[Bind Mount\n./code → /app]:::host
    end

    App -->|читає/пише| WritableLayer
    App -->|зберігає дані БД| NamedVolume
    App -->|живий код| BindMount
```

### Named Volumes vs Bind Mounts

**Named Volumes** — Docker управляє розташуванням сховища:

```bash
# Створити та використати named volume
docker volume create pgdata
docker run -v pgdata:/var/lib/postgresql/data postgres:15

# Інспектувати volume
docker volume inspect pgdata

# Volume переживає видалення контейнера:
docker rm -f my-postgres    # контейнер видалено
# volume pgdata досі існує з усіма даними
docker run -v pgdata:/var/lib/postgresql/data postgres:15   # дані повернулися!
```

**Bind Mounts** — ви вказуєте точний шлях на хості:

```bash
# Змонтувати поточну директорію в контейнер (розробка)
docker run -v $(pwd):/app -p 8000:8000 myapi:dev

# Змонтувати конкретний файл конфігурації
docker run -v $(pwd)/nginx.conf:/etc/nginx/nginx.conf nginx
```

**Коли що використовувати:**

| Сценарій | Використовуйте |
|----------|----------------|
| Файли БД (PostgreSQL, MySQL) | Named volume |
| Розробка — live перезавантаження коду | Bind mount |
| Лог-файли, до яких потрібен доступ з хоста | Bind mount |
| Продакшн дані, що повинні пережити перезапуск | Named volume |
| Секрети / облікові дані | Named volume або Docker secrets |
| CI/CD збірки (одноразові) | Нічого — ефемерний шар запису |

### Команди для volumes

```bash
docker volume create mydata
docker volume ls
docker volume inspect mydata
docker volume rm mydata
docker volume prune              # видалити всі невикористані volumes
```

---

## 8. Мережі (Networking)

### Як працюють мережі Docker

Коли Docker запускається, він створює віртуальний мережевий інтерфейс на хості (`docker0` на Linux). Контейнери підключаються до віртуальних мереж, що бриджуються через цей інтерфейс.

```mermaid
flowchart TD
    classDef host fill:#4a3b00,stroke:#ff9800,color:#fff
    classDef network fill:#263238,stroke:#90a4ae,color:#fff
    classDef container fill:#1b5e20,stroke:#4caf50,color:#fff
    classDef external fill:#4e1f1f,stroke:#f44336,color:#fff

    Internet([Інтернет]):::external
    HostPort["Порт хоста :80\n(опублікований)"]:::host
    HostPort2["Порт хоста :8000\n(опублікований)"]:::host
    Bridge["bridge мережа\n172.17.0.0/16"]:::network
    Nginx["nginx\n172.17.0.2"]:::container
    API["api\n172.17.0.3"]:::container
    DB["postgres\n172.17.0.4\n(без опублікованого порту)"]:::container
    Redis["redis\n172.17.0.5\n(без опублікованого порту)"]:::container

    Internet --> HostPort --> Nginx
    Internet --> HostPort2 --> API
    Nginx -->|внутрішньо: api:8000| API
    API -->|внутрішньо: postgres:5432| DB
    API -->|внутрішньо: redis:6379| Redis
```

### Публікація портів vs внутрішня мережа

**Опубліковані порти** (`-p HOST:CONTAINER`): Робить порт контейнера доступним з хост-машини (і тому з мережі). Публікуйте тільки те, що потрібно зовні.

**Внутрішня мережа**: Контейнери в одній Docker-мережі можуть спілкуватися на будь-якому порту за іменем сервісу — **без публікації цього порту на хості**.

```bash
# НЕПРАВИЛЬНО: Публікація порту БД назовні (ризик безпеки)
docker run -p 5432:5432 postgres     # будь-хто може підключитися до вашої БД!

# ПРАВИЛЬНО: БД залишається внутрішньою, API публікується
docker run -p 8000:8000 api          # API публічний
docker run postgres                  # БД доступна тільки всередині мережі Docker
```

### Команди для мереж

```bash
docker network create mynet                     # створити кастомну bridge мережу
docker network ls                               # список мереж
docker network inspect mynet                    # повні деталі (IP-діапазони, підключені контейнери)
docker network connect mynet api-container      # підключити запущений контейнер до мережі
docker network disconnect mynet api-container   # відключити контейнер від мережі
docker network rm mynet                         # видалити мережу
```

### DNS-резолюція всередині Docker

Docker запускає **вбудований DNS-сервер** за адресою `127.0.0.11` всередині кожного контейнера. Він автоматично перетворює імена сервісів в IP-адреси контейнерів.

```bash
# З контейнера 'api':
ping db          # перетворюється в IP контейнера postgres
ping redis       # перетворюється в IP контейнера redis
curl http://nginx/health   # перетворюється в контейнер nginx
```

Це означає, що конфігурація вашого додатку повинна використовувати **імена сервісів, ніколи IP-адреси**.

---

## 9. Типові помилки

### Помилка 1: Використання тегу `latest`

```dockerfile
# ПОГАНО
FROM python:latest
FROM node:latest
```

Тег `latest` означає "що завгодно, що є поточним latest під час збірки". Сьогодні це Python 3.12. Наступного тижня може бути Python 3.13 з незворотними змінами. Ваші збірки стають нереспектованими.

```dockerfile
# ДОБРЕ: фіксуємо точну версію
FROM python:3.11.9-slim
FROM node:20.15.1-alpine
```

**Правило:** Завжди фіксуйте точні версії в інструкціях `FROM`. Ставтесь до них як до версій у `requirements.txt`.

---

### Помилка 2: Зберігання даних всередині контейнерів

```bash
# ПОГАНО: запис у файлову систему контейнера
docker exec api-server sh -c "echo 'config' > /app/config.json"
# Ця конфігурація втрачається при перезапуску контейнера
```

```yaml
# ДОБРЕ: використовуйте volumes для будь-яких даних, що повинні зберігатися
services:
  api:
    volumes:
      - ./config:/app/config     # bind mount конфігурації з хоста
      - appdata:/app/data        # named volume для згенерованих даних
```

Будь-який файл, записаний безпосередньо всередині шару запису контейнера, є **ефемерним**. Якщо контейнер падає, замінюється новою версією або перезапускається оркестратором — ці дані зникають. Використовуйте volumes.

---

### Помилка 3: Неприбирання ресурсів

```bash
# Після тижнів розробки перевірте використання диска:
docker system df
```

Поширені причини роздування диска:
- **Зупинені контейнери**, що накопичуються з кожного `docker run` без `--rm`
- **Dangling образи** — проміжні шари від повторних збірок (з іменем `<none>:<none>`)
- **Старі named volumes** від видалених проектів
- **Кеш збірки** від `docker build`

```bash
# Команди регулярного технічного обслуговування:
docker container prune          # видалити зупинені контейнери
docker image prune              # видалити dangling образи
docker system prune             # видалити контейнери, мережі, dangling образи
docker system prune -a          # також видалити невикористані образи (не тільки dangling)
```

**Завжди використовуйте `--rm`** для одноразових контейнерів:

```bash
docker run --rm python:3.11 python -c "print('hello')"
# Контейнер автоматично видаляється після завершення
```

---

### Помилка 4: Неправильне використання `docker exec`

```bash
# ПОГАНО: "виправлення" запущеного контейнера через exec
docker exec api-server pip install missing-package
# Пакет встановлюється ТІЛЬКИ в запущений контейнер
# Наступний перезапуск контейнера: пакет зник
# Наступне розгортання: пакет відсутній
# Інші члени команди: пакет відсутній

# ПОГАНО: редагування коду безпосередньо всередині контейнера
docker exec -it api-server vim /app/main.py
```

`docker exec` — це **інструмент діагностики лише для читання**. Він для інспекції того, що відбувається — перевірки логів, запуску `psql` для запиту БД, налагодження мережевої проблеми.

```bash
# ДОБРЕ використання docker exec:
docker exec -it postgres psql -U user -d mydb    # підключитися до БД для дослідження
docker exec api-server env                        # перевірити змінні середовища
docker exec api-server python -c "import sys; print(sys.path)"  # дебаг імпортів
docker exec -it api-server curl localhost:8000/health  # перевірити внутрішній endpoint
```

Будь-яка реальна зміна повинна йти у ваш `Dockerfile` або код додатку, потім `docker build` і перерозгортання.

---

### Помилка 5: Неправильний порядок інструкцій Dockerfile

```dockerfile
# ПОГАНО: зміни коду інвалідують шар залежностей
COPY . .                           # змінюється кожного разу при зміні коду
RUN pip install -r requirements.txt  # перевстановлює ВСІ залежності навіть якщо не змінилися!
```

```dockerfile
# ДОБРЕ: залежності в кеші, якщо requirements.txt не змінився
COPY requirements.txt .            # спочатку копіюємо тільки requirements
RUN pip install -r requirements.txt  # в кеші, якщо requirements.txt не змінився
COPY . .                           # копіюємо код останнім (змінюється часто)
```

Docker перебудовує з першого зміненого шару вниз. Розміщуйте **рідко змінювані інструкції першими**, **часто змінювані — останніми**.

---

## 10. Найкращі практики

### 1. Шарування образу: порядок для ефективності кешу

```dockerfile
FROM python:3.11-slim

# Шар 1: Системні залежності (рідко змінюються)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Шар 2: Python залежності (змінюються іноді)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Шар 3: Код додатку (змінюється часто)
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Правило:** Стабільне → Напівстабільне → Мінливе. Залежності перед кодом.

---

### 2. Маленькі образи: використовуйте Alpine або Slim варіанти

| Базовий образ | Розмір | Використання |
|--------------|--------|--------------|
| `python:3.11` | ~1 ГБ | Ніколи в продакшні |
| `python:3.11-slim` | ~130 МБ | Стандартний вибір для продакшну |
| `python:3.11-alpine` | ~50 МБ | Найменший, але може не мати бібліотек |
| `gcr.io/distroless/python3` | ~30 МБ | Максимальна безпека (без shell) |

```dockerfile
# Використовуйте slim або alpine де можливо:
FROM python:3.11-slim
FROM node:20-alpine
FROM nginx:1.25-alpine
```

Також: завжди очищайте кеші менеджера пакетів в тому ж шарі:

```dockerfile
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*   # ОБОВ'ЯЗКОВО в тому ж RUN для зменшення розміру шару
```

---

### 3. Багатоетапні збірки (Multi-Stage) для продакшну

Інструменти збірки, компілятори та тестові залежності не повинні бути у вашому продакшн-образі.

```dockerfile
# Стейдж 1: Builder (має компілятори, dev-інструменти)
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# Стейдж 2: Продакшн (мінімальний, без інструментів збірки)
FROM python:3.11-slim AS production
WORKDIR /app
COPY --from=builder /install /usr/local    # копіюємо тільки встановлені пакети
COPY src/ .
CMD ["python", "main.py"]
```

Продакшн-образ містить тільки те, що потрібно для запуску — не для збірки. Менша поверхня атаки, менший розмір.

---

### 4. Відтворюваність: `.dockerignore`

```dockerignore
# .dockerignore — запобігає відправці зайвих файлів до Docker daemon
.git
.gitignore
__pycache__
*.pyc
*.pyo
.env
.env.*
.venv
venv/
node_modules/
*.log
dist/
build/
.pytest_cache/
.mypy_cache/
```

Без `.dockerignore`, `COPY . .` відправляє всю вашу директорію (включаючи `.git`, `venv`, `node_modules`) до Docker daemon. Це значно уповільнює збірки та збільшує розмір образу.

---

### 5. Dev vs Prod: Окремі Compose-файли

```
docker-compose.yml          ← базова конфігурація (спільні сервіси)
docker-compose.dev.yml      ← dev-перевизначення (bind mounts, debug порти)
docker-compose.prod.yml     ← prod-перевизначення (ліміти ресурсів, restart policies)
```

```yaml
# docker-compose.yml (база)
services:
  api:
    image: myapi:${TAG:-latest}
    environment:
      - DATABASE_URL=${DATABASE_URL}

# docker-compose.dev.yml (dev перевизначення)
services:
  api:
    build: .                           # локальна збірка для dev
    volumes:
      - .:/app                         # live reload
    environment:
      - DEBUG=true
    command: uvicorn main:app --reload

# docker-compose.prod.yml (prod перевизначення)
services:
  api:
    restart: always                    # автоперезапуск при збої
    deploy:
      resources:
        limits:
          memory: 512M
```

```bash
# Розробка:
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Продакшн:
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

### 6. Основи безпеки

**Ніколи не запускайте від імені root:**

```dockerfile
# Створюємо непривілейованого користувача
RUN addgroup --system app && adduser --system --group app
USER app                    # всі наступні інструкції виконуються як 'app'
```

**Ніколи не зберігайте секрети в Dockerfile або образі:**

```dockerfile
# ПОГАНО: секрет запечений у шар образу (видно в history)
ENV DATABASE_PASSWORD=supersecret

# ДОБРЕ: передаємо під час запуску
# docker run -e DATABASE_PASSWORD=$SECRET_FROM_VAULT myapi
```

**Використовуйте файлову систему тільки для читання де можливо:**

```bash
docker run --read-only -v /tmp:/tmp myapi    # файлова система лише для читання крім /tmp
```

**Скануйте образи на вразливості:**

```bash
docker scout cves myapi:v1.0    # вбудований сканер Docker
trivy image myapi:v1.0          # Trivy (популярний сканер з відкритим кодом)
```

---

### Швидкий довідник

```
Збірка:    docker build -t name:tag .
Запуск:    docker run -d -p 8000:8000 --name app name:tag
Логи:      docker logs -f app
Shell:     docker exec -it app bash
Зупинка:   docker stop app
Видалення: docker rm app
Образи:    docker images
Очищення:  docker system prune -a

Compose:
  Запуск:  docker compose up -d --build
  Зупинка: docker compose down
  Логи:    docker compose logs -f service
  Shell:   docker compose exec service bash
```

---

## 11. Офіційні образи для курсу Python Advanced

Усі перелічені образи — офіційні, доступні на **[Docker Hub](https://hub.docker.com/)**.

### 11.1 Python

**Образ:** [`python`](https://hub.docker.com/_/python) — офіційний образ інтерпретатора Python.

```bash
docker pull python:3.11-slim
```

| Тег | Розмір | Коли використовувати |
|-----|--------|----------------------|
| `python:3.11` | ~1 ГБ | Ніколи в продакшні |
| `python:3.11-slim` | ~130 МБ | Стандарт: продакшн сервіси |
| `python:3.11-alpine` | ~50 МБ | Мінімальний розмір (менше сумісності) |

```bash
# Запустити Python REPL у контейнері
docker run --rm -it python:3.11-slim python

# Виконати скрипт із поточної директорії
docker run --rm -v $(pwd):/app -w /app python:3.11-slim python my_script.py
```

---

### 11.2 PostgreSQL

**Образ:** [`postgres`](https://hub.docker.com/_/postgres) — офіційний образ реляційної СУБД PostgreSQL.

```bash
docker pull postgres:16-alpine
```

| Змінна середовища | Обов'язкова | Значення за замовчуванням |
|-------------------|-------------|---------------------------|
| `POSTGRES_PASSWORD` | Так | — |
| `POSTGRES_USER` | Ні | `postgres` |
| `POSTGRES_DB` | Ні | `= POSTGRES_USER` |

```bash
# Запустити PostgreSQL
docker run -d \
  --name my-postgres \
  -e POSTGRES_PASSWORD=secret \
  -e POSTGRES_USER=user \
  -e POSTGRES_DB=mydb \
  -p 5432:5432 \
  -v pgdata:/var/lib/postgresql/data \
  postgres:16-alpine

# Підключитися через psql
docker exec -it my-postgres psql -U user -d mydb
```

---

### 11.3 MongoDB

**Образ:** [`mongo`](https://hub.docker.com/_/mongo) — офіційний образ документно-орієнтованої NoSQL бази даних MongoDB.

```bash
docker pull mongo:7
```

| Змінна середовища | Опис |
|-------------------|------|
| `MONGO_INITDB_ROOT_USERNAME` | Ім'я адмін-користувача |
| `MONGO_INITDB_ROOT_PASSWORD` | Пароль адміна |
| `MONGO_INITDB_DATABASE` | Початкова БД |

```bash
# Запустити MongoDB
docker run -d \
  --name my-mongo \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=secret \
  -p 27017:27017 \
  -v mongodata:/data/db \
  mongo:7

# Підключитися через mongosh
docker exec -it my-mongo mongosh -u admin -p secret
```

```python
# Python підключення (pymongo)
from pymongo import MongoClient
client = MongoClient("mongodb://admin:secret@localhost:27017/")
db = client["mydb"]
```

---

### 11.4 Redis

**Образ:** [`redis`](https://hub.docker.com/_/redis) — офіційний образ in-memory сховища даних. Використовується як кеш, брокер повідомлень (Celery), pub/sub.

```bash
docker pull redis:7-alpine
```

```bash
# Запустити Redis
docker run -d \
  --name my-redis \
  -p 6379:6379 \
  redis:7-alpine

# Підключитися через redis-cli
docker exec -it my-redis redis-cli

# Основні команди redis-cli:
# SET key value
# GET key
# DEL key
# KEYS *
```

```python
# Python підключення (redis-py)
import redis
r = redis.Redis(host="localhost", port=6379, decode_responses=True)
r.set("name", "Docker")
print(r.get("name"))  # Docker
```

---

### 11.5 Neo4j

**Образ:** [`neo4j`](https://hub.docker.com/_/neo4j) — офіційний образ графової СУБД Neo4j. Зберігає дані у вигляді вузлів (nodes) та зв'язків (relationships).

```bash
docker pull neo4j:5
```

| Порт | Призначення |
|------|-------------|
| `7474` | Neo4j Browser (веб-інтерфейс) |
| `7687` | Bolt protocol (для підключення програм) |

```bash
# Запустити Neo4j
docker run -d \
  --name my-neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -v neo4jdata:/data \
  neo4j:5

# Відкрити у браузері:
# http://localhost:7474
# Логін: neo4j / Пароль: password
```

```python
# Python підключення (neo4j driver)
from neo4j import GraphDatabase
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

with driver.session() as session:
    session.run("CREATE (n:Person {name: 'Alice'})")
    result = session.run("MATCH (n:Person) RETURN n.name")
    for record in result:
        print(record["n.name"])
```

---

### 11.6 Ubuntu

**Образ:** [`ubuntu`](https://hub.docker.com/_/ubuntu) — офіційний образ ОС Ubuntu. Використовується як базовий образ або для інтерактивних сесій.

```bash
docker pull ubuntu:24.04
```

```bash
# Запустити інтерактивну Ubuntu-сесію
docker run --rm -it ubuntu:24.04 bash

# Встановити пакети та протестувати
docker run --rm -it ubuntu:24.04 bash -c "
  apt-get update -qq && \
  apt-get install -y python3 python3-pip && \
  python3 --version
"
```

---

### Зведена таблиця образів курсу

| Образ | Версія | Порт | Призначення |
|-------|--------|------|-------------|
| `python` | `3.11-slim` | — | Виконання Python додатків |
| `postgres` | `16-alpine` | 5432 | Реляційна БД |
| `mongo` | `7` | 27017 | Документна NoSQL БД |
| `redis` | `7-alpine` | 6379 | Кеш / брокер повідомлень |
| `neo4j` | `5` | 7474, 7687 | Графова БД |
| `ubuntu` | `24.04` | — | Базова ОС / навчальне середовище |

---

*Посібник Docker · Модуль 3 · Python Advanced · Віктор Нікоряк*
