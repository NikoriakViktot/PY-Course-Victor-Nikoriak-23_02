# Урок 35 — Claude Code: від встановлення до продвинутих тем

> **Claude Code** — це AI-агент від Anthropic, вбудований у термінал, IDE та браузер.
> Він читає ваш код, редагує файли, запускає команди та автоматизує весь цикл розробки.

---

## Зміст

1. [Що таке Claude Code](#1-що-таке-claude-code)
2. [Встановлення](#2-встановлення)
3. [Перший запуск](#3-перший-запуск)
4. [CLI — команди та флаги](#4-cli--команди-та-флаги)
5. [Як писати ефективні промпти](#5-як-писати-ефективні-промпти)
6. [CLAUDE.md — постійна пам'ять](#6-claudemd--постійна-память)
7. [Auto Memory — автоматичне збереження](#7-auto-memory--автоматичне-збереження)
8. [Slash Commands та Skills](#8-slash-commands-та-skills)
9. [MCP — підключення зовнішніх інструментів](#9-mcp--підключення-зовнішніх-інструментів)
10. [Hooks — автоматизація подій](#10-hooks--автоматизація-подій)
11. [Налаштування та конфігурація](#11-налаштування-та-конфігурація)
12. [Продвинуті теми](#12-продвинуті-теми)
13. [Корисні посилання](#13-корисні-посилання)

---

## 1. Що таке Claude Code

Claude Code — це **агентичний інструмент для розробки**, доступний через:

| Платформа | Як отримати |
|-----------|-------------|
| Terminal CLI | `claude` у будь-якому терміналі |
| VS Code | Розширення з маркетплейсу |
| JetBrains | PyCharm, IntelliJ, WebStorm |
| Desktop App | macOS / Windows застосунок |
| Web | [claude.ai/code](https://claude.ai/code) |
| iOS | Мобільний застосунок |

### Що Claude Code вміє

```
Ваш запит
    ↓
Claude читає весь ваш репозиторій
    ↓
Редагує файли, запускає команди, тестує
    ↓
Створює коміт і PR
    ↓
Готовий результат
```

**Конкретні можливості:**
- Виправляє баги та впроваджує функції в кількох файлах одночасно
- Пише тести, фіксить lint-помилки, вирішує merge-конфлікти
- Створює git-коміти та pull requests
- Підключається до баз даних, JIRA, Figma, GitHub через MCP
- Запускає команди bash та інтерпретує їх результати
- Планує архітектуру та пояснює чужий код
- Автоматично запам'ятовує ваші уподобання між сесіями

---

## 2. Встановлення

### Системні вимоги

| Компонент | Вимога |
|-----------|--------|
| ОС | macOS 13.0+, Windows 10 1809+, Ubuntu 20.04+, Debian 10+, Alpine 3.19+ |
| RAM | 4 GB або більше |
| Процесор | x64 або ARM64 |
| Мережа | Необхідне з'єднання з інтернетом |
| Підписка | Claude Pro / Max / Team / Enterprise або Anthropic Console |

### Встановлення — рекомендований спосіб

**macOS / Linux / WSL:**
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows PowerShell:**
```powershell
irm https://claude.ai/install.ps1 | iex
```

**Windows CMD:**
```cmd
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

### Альтернативні способи

```bash
# Homebrew (macOS)
brew install --cask claude-code

# WinGet (Windows)
winget install Anthropic.ClaudeCode

# npm (cross-platform)
npm install -g @anthropic-ai/claude-code

# Linux — Debian/Ubuntu
sudo apt install claude-code

# Linux — Fedora/RHEL
sudo dnf install claude-code

# Linux — Alpine
sudo apk add claude-code
```

### Перевірка встановлення

```bash
claude --version      # Версія
claude doctor         # Детальна діагностика конфігурації
```

### Автооновлення

- **Нативне встановлення**: оновлення у фоні (за замовчуванням `stable`)
- **Homebrew / WinGet / пакетні менеджери**: вручну (`claude update`)
- Налаштувати канал: `"autoUpdatesChannel": "latest"` у settings.json

---

## 3. Перший запуск

```bash
cd your-project    # Перейдіть у папку проекту
claude             # Запустіть Claude Code
```

При першому запуску вас попросять залогінитись на [claude.ai](https://claude.ai).

### Базові операції

```bash
claude                          # Інтерактивна сесія
claude "поясни цей проект"      # Сесія з початковим запитом
claude -p "знайди баги"         # Один запит, вихід після відповіді
claude -c                       # Продовжити останню сесію
claude -r "auth-refactor"       # Відновити сесію за назвою
```

### Перші кроки після входу

```
/init       → Ініціалізація CLAUDE.md для проекту
/help       → Всі доступні команди
/config     → Відкрити налаштування
/memory     → Переглянути пам'ять та CLAUDE.md
```

---

## 4. CLI — команди та флаги

### Основні команди

| Команда | Опис |
|---------|------|
| `claude` | Відкрити інтерактивну сесію |
| `claude "запит"` | Сесія з початковим запитом |
| `claude -p "запит"` | Один запит без інтерактивного режиму |
| `claude -c` | Продовжити останню розмову |
| `claude -r "назва"` | Відновити сесію за ID або назвою |
| `claude update` | Оновити до останньої версії |
| `cat file.py \| claude -p "поясни"` | Передати файл через pipe |

### Автентифікація

```bash
claude auth login     # Увійти в акаунт Anthropic
claude auth logout    # Вийти
claude auth status    # Перевірити статус авторизації
claude setup-token    # Згенерувати довготривалий OAuth токен
```

### Управління сесіями

```bash
claude agents         # Відкрити панель агентів (паралельні сесії)
claude attach <id>    # Підключитись до фонової сесії
claude logs <id>      # Переглянути вивід фонової сесії
claude stop <id>      # Зупинити фонову сесію
claude respawn <id>   # Перезапустити зупинену сесію
claude rm <id>        # Видалити сесію
```

### Важливі флаги

| Флаг | Призначення | Приклад |
|------|-------------|---------|
| `--model` | Вибір моделі | `claude --model claude-opus-4-7` |
| `--effort` | Рівень зусиль | `claude --effort high` |
| `--permission-mode` | Режим дозволів | `claude --permission-mode plan` |
| `--add-dir` | Додати директорії | `claude --add-dir ../api ../lib` |
| `--tools` | Обмежити інструменти | `claude --tools "Bash,Edit,Read"` |
| `--bg` | Фоновий агент | `claude --bg "досліди баг"` |
| `-w` | Git worktree | `claude -w feature-auth` |
| `--debug` | Логи для налагодження | `claude --debug "api,hooks"` |
| `--json-schema` | Структурована відповідь | `claude -p --json-schema '{...}' "запит"` |
| `--system-prompt` | Замінити системний промпт | `claude --system-prompt "Ти Python-експерт"` |
| `-n` | Назва сесії | `claude -n "auth-redesign"` |

### Моделі Claude (2025)

| Модель | ID | Призначення |
|--------|-----|-------------|
| Claude Opus 4.7 | `claude-opus-4-7` | Найпотужніша, складні задачі |
| Claude Sonnet 4.6 | `claude-sonnet-4-6` | Баланс швидкості та якості |
| Claude Haiku 4.5 | `claude-haiku-4-5-20251001` | Швидка, прості задачі |

---

## 5. Як писати ефективні промпти

### Принципи ефективного промптингу

```
❌ Погано:  "виправ код"
✅ Добре:   "в функції calculate_total() є баг — при порожньому списку
             кидає KeyError. Виправ і додай тест"

❌ Погано:  "зроби гарно"
✅ Добре:   "відформатуй файл: відступи 4 пробіли, рядки до 88 символів,
             одинарні лапки, PEP 8"
```

### Структура ефективного запиту

```
1. КОНТЕКСТ:  Що ти робиш і навіщо
2. ПРОБЛЕМА:  Конкретно що не так або що потрібно
3. ОБМЕЖЕННЯ: Що не можна змінювати / технологія
4. ОЧІКУВАННЯ: Який результат хочеш отримати
```

**Приклад:**
```
Я будую FastAPI застосунок (Python 3.12).
У ендпоінті POST /api/users є перевірка email,
але вона не відхиляє адреси без домену (напр. "user@").
Виправ валідацію, використовуй pydantic v2 EmailStr,
і додай 3 pytest-тести для крайніх випадків.
```

### Режими роботи

| Команда | Що робить |
|---------|-----------|
| `--permission-mode plan` | Тільки планує, не виконує |
| `--permission-mode acceptEdits` | Авто-приймає редагування |
| `--permission-mode bypassPermissions` | Повний автопілот |

### Корисні техніки

**Попросити спочатку план:**
```
Створи план для рефакторингу модуля auth.
Не починай реалізацію — тільки план.
```

**Вставити код/помилку напряму:**
```
Отримую цю помилку:
---
ImportError: cannot import name 'AsyncSession' from 'sqlalchemy.orm'
---
Як виправити при використанні SQLAlchemy 2.0?
```

**Обмежити scope:**
```
Виправ тільки функцію validate_token() у файлі auth/utils.py.
Не чіпай інші файли.
```

**Ітеративне покращення:**
```
Добре, тепер зроби цю функцію асинхронною.
```

---

## 6. CLAUDE.md — постійна пам'ять

`CLAUDE.md` — це Markdown-файл, який Claude читає на початку **кожної** сесії.
Це ваш спосіб передати йому постійні інструкції про проект.

### Ієрархія завантаження (порядок пріоритету)

```
1. /.claude/CLAUDE.md          ← організаційний рівень (не можна ігнорувати)
2. ~/.claude/CLAUDE.md         ← всі ваші проекти (особисті правила)
3. ./CLAUDE.md                 ← проект (команда, через git)
4. ./.claude/CLAUDE.md         ← проект (альтернативне розташування)
5. ./CLAUDE.local.md           ← локально (add to .gitignore)
```

### Створення CLAUDE.md

```bash
# Автоматична ініціалізація (рекомендовано)
/init

# Або вручну
touch CLAUDE.md
```

### Приклад CLAUDE.md для Python-проекту

```markdown
# Проект: News Dashboard API

## Технологічний стек
- Python 3.12, FastAPI 0.115, MongoDB (motor 3.7)
- Docker Compose для запуску (docker compose up --build)
- Тести: pytest + httpx

## Команди розробки
- `docker compose up --build` — запустити всі сервіси
- `docker compose build fastapi-news` — перебудувати тільки API
- `pytest tests/ -v` — запустити тести

## Структура проекту
- `app/main.py` — FastAPI ендпоінти
- `app/nlp.py` — NLP pipeline (pymorphy3 + spaCy)
- `app/scraper.py` — aiohttp скрейпер
- `streamlit/app.py` — Streamlit дашборд

## Стиль коду
- Відступи: 4 пробіли
- Рядки: до 100 символів
- Лапки: подвійні в Python
- Типи: обов'язкові анотації для всіх функцій

## Важливі правила
- Завжди використовуй async/await для MongoDB (motor)
- Не коміть .env файли
- Додавай логування через logging, не print()
- Документуй публічні функції однорядковим docstring
```

### Підключення зовнішніх файлів

```markdown
# Огляд проекту
@README.md

# Інструкції з розгортання
Дивись @docs/deployment.md
```

### Path-specific правила (`.claude/rules/`)

Правила для конкретних файлів:

```markdown
---
paths:
  - "src/api/**/*.ts"
  - "src/api/**/*.tsx"
---

# Правила для API

- Всі ендпоінти повинні мати input validation
- Використовуй стандартний формат помилок
- Включай OpenAPI документацію (docstrings)
```

### Найкращі практики

| Правило | Чому |
|---------|------|
| До 200 рядків на файл | Менше витрат контексту |
| Конкретні правила, не загальні | "2 пробіли" краще за "форматуй гарно" |
| Регулярно оновлюй | Застарілі правила плутають |
| Видаляй суперечливі інструкції | Claude буде розгублений |

---

## 7. Auto Memory — автоматичне збереження

Claude автоматично зберігає знання між сесіями у файлах пам'яті.

### Де зберігається

```
~/.claude/projects/<project-hash>/memory/
├── MEMORY.md          ← індекс (до 200 рядків)
├── user_role.md       ← хто ви, яка у вас роль
├── feedback.md        ← ваші уподобання та виправлення
├── project_*.md       ← деталі поточного проекту
└── reference.md       ← посилання на зовнішні ресурси
```

### Типи пам'яті

| Тип | Що зберігає | Коли |
|-----|-------------|------|
| `user` | Ваша роль, рівень досвіду | Коли Claude дізнається про вас |
| `feedback` | Ваші виправлення, уподобання | Коли ви виправляєте Claude |
| `project` | Рішення, обмеження, дедлайни | Коли дізнається про проект |
| `reference` | Посилання на зовнішні системи | Коли ви даєте посилання |

### CLAUDE.md vs Auto Memory

| | CLAUDE.md | Auto Memory |
|--|-----------|-------------|
| Хто пише | Ви | Claude |
| Що містить | Правила та інструкції | Навчання та патерни |
| Коли корисно | Стандарти, архітектура | Build-команди, баги, уподобання |
| Завантаження | Щоразу (повністю) | Щоразу (перші 200 рядків) |

### Управління пам'яттю

```bash
/memory    # Переглянути всі CLAUDE.md і пам'ять у поточній сесії
```

**Явне збереження:**
```
Запам'ятай: у нас freeze на мерджі після четверга через реліз
```

**Видалення:**
```
Забудь про правило щодо відступів — ми перейшли на tabs
```

**Вимкнути Auto Memory:**
```json
{ "autoMemoryEnabled": false }
```

---

## 8. Slash Commands та Skills

### Вбудовані команди

```bash
/help              # Всі команди
/init              # Ініціалізувати CLAUDE.md для проекту
/memory            # Переглянути пам'ять та інструкції
/config            # Відкрити налаштування
/model             # Змінити модель
/effort            # Встановити рівень зусиль
/review            # Рев'ю коду або PR
/security-review   # Аудит безпеки
/compact           # Стиснути контекст (коли він заповнюється)
/rename            # Перейменувати сесію
/stop              # Зупинити поточну відповідь
/mcp               # Управління MCP серверами
/skills            # Переглянути/управляти скілами
```

### Що таке Skills

**Skill** — це власна команда у вигляді `SKILL.md` файлу, яку ви додаєте до Claude.

```
/deploy            → запускає ваш deployment-скрипт
/pr-summary        → генерує опис PR з diff
/check-security    → сканує код на вразливості
/update-changelog  → оновлює CHANGELOG.md
```

### Створення свого Skill

**Крок 1: Структура директорії**
```bash
mkdir -p ~/.claude/skills/pr-summary
touch ~/.claude/skills/pr-summary/SKILL.md
```

**Крок 2: SKILL.md**
```markdown
---
description: Генерує опис PR з git diff і коментарів
argument-hint: "[номер PR]"
---

## Контекст PR

- Diff: !`git diff main`
- Коміти: !`git log main..HEAD --oneline`

## Інструкції

1. Стисло опиши зміни (2-3 речення)
2. Перелічи всі змінені файли з причиною
3. Вкажи можливі ризики або breaking changes
4. Запропонуй шаблон для опису PR
```

**Крок 3: Використання**
```bash
/pr-summary
# або природньою мовою:
"Що я змінив?"
```

### Розташування Skills

| Місце | Scope | Через git |
|-------|-------|-----------|
| Enterprise | Організація | Так (IT) |
| `~/.claude/skills/` | Всі проекти | Ні (особисті) |
| `.claude/skills/` | Поточний проект | Так |
| Plugin | Там, де плагін | Так |

### Frontmatter Skills

```yaml
---
name: my-skill
description: Що робить skill і коли використовувати
argument-hint: "[аргумент]"
arguments: [issue, branch]
disable-model-invocation: true  # тільки ви можете викликати
allowed-tools: Bash(npm test) Read Edit
model: claude-opus-4-7
effort: high
context: fork          # запустити в підагенті
agent: Explore         # використати спеціалізований агент
---
```

### Динамічний контекст у Skills

```markdown
---
description: Аналіз поточних змін
---

## Git статус

!`git status`
!`git diff HEAD`

## Зміни по файлах

!`git log --oneline -10`

Проаналізуй ці зміни і запропонуй покращення.
```

### Приклади корисних Skills

**Skill: автоматичний коміт**
```markdown
---
name: smart-commit
description: Аналізує зміни і створює описовий коміт
allowed-tools: Bash(git add *) Bash(git commit *) Bash(git status *)
---

!`git diff --staged`
!`git status`

Проаналізуй зміни і зроби git коміт з описовим повідомленням.
Формат: "<type>: <short description>" де type = feat/fix/docs/refactor/test
```

**Skill: аналіз безпеки**
```markdown
---
name: security-check
description: Перевіряє код на типові вразливості
agent: Explore
---

Перевір наступні файли на OWASP Top 10 вразливості:
!`git diff HEAD --name-only`

Для кожного знайденого файлу: прочитай і перевір на
SQL injection, XSS, незахищені endpoints, hardcoded secrets.
```

---

## 9. MCP — підключення зовнішніх інструментів

**Model Context Protocol (MCP)** — відкритий стандарт для підключення AI до зовнішніх джерел даних та сервісів.

### Що можна підключити

```
GitHub     → читати issues, PR, код
Figma      → отримувати дизайн-специфікації
PostgreSQL → запитувати бази даних напряму
JIRA       → читати і оновлювати задачі
Sentry     → аналізувати помилки
Slack      → читати канали
Gmail      → обробляти пошту
MongoDB    → запитувати колекції
```

**Каталог MCP серверів:** [claude.ai/directory](https://claude.ai/directory)

### Встановлення MCP серверу

**HTTP сервер (рекомендовано):**
```bash
claude mcp add --transport http notion https://mcp.notion.com/mcp
```

**З API ключем:**
```bash
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp \
  --header "Authorization: Bearer YOUR_TOKEN"
```

**Локальний stdio сервер:**
```bash
claude mcp add --transport stdio postgres \
  -- npx -y @bytebase/dbhub \
  --dsn "postgresql://user:pass@localhost:5432/mydb"
```

> **Важливо:** опції (`--transport`, `--header`, `--scope`) МАЮТЬ йти ДО назви сервера!

### Управління серверами

```bash
claude mcp list              # Список всіх серверів
claude mcp get github        # Деталі сервера
claude mcp remove github     # Видалити сервер
/mcp                         # Статус у Claude Code (+ OAuth)
```

### Scope (область видимості)

| Scope | Де діє | Спільний | Файл |
|-------|--------|----------|------|
| `local` (за замовч.) | Поточний проект | Ні | `~/.claude.json` |
| `project` | Поточний проект | Так (git) | `.mcp.json` |
| `user` | Всі проекти | Ні | `~/.claude.json` |

```bash
claude mcp add --scope project --transport http \
  github https://api.githubcopilot.com/mcp/ \
  --header "Authorization: Bearer YOUR_PAT"
```

### `.mcp.json` — конфіг для команди

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    },
    "postgres": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@bytebase/dbhub", "--dsn", "${DATABASE_URL}"]
    },
    "sentry": {
      "type": "http",
      "url": "https://mcp.sentry.dev/mcp"
    }
  }
}
```

### Використання MCP у розмові

```
Які найпоширеніші помилки за останні 24 години?    ← Sentry
Покажи схему таблиці orders                         ← PostgreSQL
Зроби issue #123 і запропонуй рішення               ← GitHub
Що змінилося в макеті LoginScreen?                  ← Figma
```

**MCP Resources через @mentions:**
```
Проаналізуй @github:issue://123 і запропонуй фікс
Порівняй @postgres:schema://users з @docs:file://api/auth
```

### Практичні приклади

**GitHub + Claude:**
```bash
# Підключити
claude mcp add --scope user --transport http github \
  https://api.githubcopilot.com/mcp/ \
  --header "Authorization: Bearer ghp_xxxx"

# Використати
claude "Переглянь відкриті issues і знайди найпростіший баг для початківця"
```

**PostgreSQL аналітика:**
```bash
claude mcp add --transport stdio analytics \
  -- npx -y @bytebase/dbhub \
  --dsn "postgresql://readonly:pass@prod.db:5432/analytics"

# Запитати
claude "Яка середня конверсія по джерелах трафіку цього місяця?"
```

---

## 10. Hooks — автоматизація подій

**Hooks** — це shell-команди або HTTP-ендпоінти, що виконуються в конкретні моменти роботи Claude.

### Приклади використання

```
Після кожного редагування файлу → запустити lint
Перед виконанням bash-команди   → перевірити безпечність
Після коміту                    → запустити тести
При старті сесії                → завантажити конфіг
```

### Типи подій (Hook Events)

**На сесію:**
- `SessionStart` — початок або продовження сесії
- `SessionEnd` — завершення сесії

**На хід:**
- `UserPromptSubmit` — користувач надіслав запит
- `Stop` — Claude завершив відповідь

**На кожен виклик інструменту:**
- `PreToolUse` — перед виконанням інструменту
- `PostToolUse` — після успішного виконання
- `PostToolUseFailure` — після невдачі

**Асинхронні:**
- `FileChanged` — файл змінився (watch mode)
- `ConfigChange` — змінився файл конфігурації

### Конфігурація Hooks у settings.json

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/lint.sh",
            "timeout": 30,
            "statusMessage": "Перевіряю стиль коду..."
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/safety-check.sh"
          }
        ]
      }
    ]
  }
}
```

### Блокування небезпечних команд

```bash
#!/bin/bash
# .claude/hooks/block-dangerous.sh
INPUT=$(cat)
CMD=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))")

if echo "$CMD" | grep -qE "^rm -rf|DROP TABLE|> /dev/"; then
  echo '{"continue": false, "stopReason": "Небезпечна команда заблокована"}'
  exit 2
fi
```

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/block-dangerous.sh"
      }]
    }]
  }
}
```

### Lint після редагування

```bash
#!/bin/bash
# .claude/hooks/lint-python.sh
INPUT=$(cat)
FILE=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))")

if [[ "$FILE" == *.py ]]; then
  ruff check "$FILE" 2>&1
  BLACK_RESULT=$(black --check "$FILE" 2>&1)
  if [ $? -ne 0 ]; then
    echo "Lint помилки: $BLACK_RESULT"
    exit 2
  fi
fi
```

### Exit-коди Hooks

| Код | Значення | Дія |
|-----|----------|-----|
| `0` | Успіх | Продовжуємо |
| `2` | Блокуюча помилка | stderr показується Claude, дія **заблокована** |
| Інший | Некритична помилка | stderr показується, продовжуємо |

---

## 11. Налаштування та конфігурація

### Файли конфігурації (пріоритет від вищого до нижчого)

```
1. Managed     → сервер/адмін (неможливо перевизначити)
2. CLI flags   → --permission-mode, --model, тощо
3. Local       → .claude/settings.local.json   (особисті, не в git)
4. Project     → .claude/settings.json          (команда, через git)
5. User        → ~/.claude/settings.json        (всі проекти, особисті)
```

### Основні налаштування

**`~/.claude/settings.json` (особисті):**
```json
{
  "model": "claude-sonnet-4-6",
  "effortLevel": "high",
  "autoMemoryEnabled": true,
  "editorMode": "vim",
  "autoScrollEnabled": true,
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      "Bash(npm run *)",
      "Bash(git add *)",
      "Bash(git commit *)",
      "Bash(docker compose *)"
    ],
    "ask": [
      "Bash(git push *)",
      "Bash(rm *)"
    ],
    "deny": [
      "Read(./.env)",
      "Bash(curl * | bash)"
    ]
  }
}
```

**`.claude/settings.json` (проект, у git):**
```json
{
  "model": "claude-sonnet-4-6",
  "permissions": {
    "allow": [
      "Bash(npm run test)",
      "Bash(npm run lint)",
      "Bash(npm run build)"
    ]
  }
}
```

### Режими дозволів

| Режим | Опис |
|-------|------|
| `default` | Запитує дозвіл на небезпечні дії |
| `acceptEdits` | Авто-приймає редагування файлів |
| `bypassPermissions` | Повний автопілот (обережно!) |
| `plan` | Тільки планує, не виконує |

```bash
# Запустити у режимі планування
claude --permission-mode plan "розроби архітектуру нового API"

# Повний автопілот для CI/CD
claude --permission-mode bypassPermissions -p "запусти тести і виправ всі проблеми"
```

### Sandbox (ізольоване середовище)

```json
{
  "sandbox": {
    "enabled": true,
    "filesystem": {
      "allowWrite": ["/tmp/build", "./dist"],
      "denyRead": ["~/.aws/credentials", "./.env"]
    },
    "network": {
      "allowedDomains": ["github.com", "*.npmjs.org", "pypi.org"]
    }
  }
}
```

### Змінні оточення

```json
{
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "0",
    "NODE_ENV": "development"
  }
}
```

### Важливі env-змінні

| Змінна | Значення |
|--------|----------|
| `ANTHROPIC_API_KEY` | API ключ (для headless/API режиму) |
| `CLAUDE_CODE_DISABLE_AUTO_MEMORY` | `1` → вимкнути auto memory |
| `ENABLE_TOOL_SEARCH` | `true/false/auto` → відкладене завантаження MCP |
| `MAX_MCP_OUTPUT_TOKENS` | Ліміт токенів для MCP відповідей |
| `ANTHROPIC_MODEL` | Перевизначити модель |

---

## 12. Продвинуті теми

### Паралельна робота (Multi-Agent)

```bash
# Запустити агента у фоні
claude --bg "перепиши всі тести для auth модуля"

# Переглянути всі агенти
claude agents

# Підключитись до результату
claude attach <session-id>
```

**Worktrees — ізольована розробка:**
```bash
# Кожна гілка в окремій папці
claude -w feature-payment "реалізуй оплату через Stripe"
claude -w bugfix-login "виправ баг автентифікації"
# Обидва агенти працюють паралельно, не заважаючи одне одному
```

### Pipe та скриптування

```bash
# Аналіз логів
cat error.log | claude -p "знайди патерн помилок і запропонуй рішення"

# Аналіз даних
cat sales.csv | claude -p "знайди топ-5 продуктів і аномалії"

# Code review через stdin
git diff main | claude -p "зроби code review, фокус на безпеку"

# Генерація коду
claude -p "напиши pydantic модель для User з email, name, created_at" \
  > models/user.py
```

### Структуровані відповіді (JSON Schema)

```bash
# Отримати структурований JSON
claude -p --json-schema '{
  "type": "object",
  "properties": {
    "bugs": {"type": "array", "items": {"type": "string"}},
    "severity": {"type": "string", "enum": ["low", "medium", "high"]},
    "suggestions": {"type": "array"}
  }
}' "проаналізуй auth/utils.py на баги"
```

### Claude як CI/CD крок

```yaml
# .github/workflows/claude-review.yml
- name: Claude Code Review
  run: |
    claude --permission-mode bypassPermissions -p \
      "перевір PR на: 1) баги 2) безпеку 3) дотримання стандартів. 
       Якщо є критичні проблеми — вийди з кодом 1."
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Remote Control

```bash
claude remote-control    # Запустити сервер для віддаленого управління
```

Дозволяє контролювати Claude Code з будь-якого місця через API.

### Збірка власного агента (Agent SDK)

```python
import anthropic

client = anthropic.Anthropic()

# Запустити агента з інструментами
response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=4096,
    tools=[
        {
            "name": "read_file",
            "description": "Читає файл з диску",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        }
    ],
    messages=[{
        "role": "user",
        "content": "Прочитай README.md і поясни проект"
    }]
)
```

### Context Management

```bash
/compact    # Стиснути контекст (видаляє старі повідомлення зі summary)
```

**Коли стискати:**
- Claude починає забувати початок розмови
- Відповіді стають менш точними
- Вказується "context limit approaching"

---

## 13. Корисні посилання

### Офіційна документація Claude Code

| Розділ | Посилання |
|--------|-----------|
| Огляд | https://docs.anthropic.com/en/docs/claude-code/overview |
| Встановлення | https://docs.anthropic.com/en/docs/claude-code/getting-started |
| CLI Reference | https://docs.anthropic.com/en/docs/claude-code/cli-reference |
| Налаштування | https://docs.anthropic.com/en/docs/claude-code/settings |
| Пам'ять (CLAUDE.md) | https://docs.anthropic.com/en/docs/claude-code/memory |
| Hooks | https://docs.anthropic.com/en/docs/claude-code/hooks |
| MCP | https://docs.anthropic.com/en/docs/claude-code/mcp |
| Skills / Slash Commands | https://docs.anthropic.com/en/docs/claude-code/slash-commands |

### Anthropic API та моделі

| Ресурс | Посилання |
|--------|-----------|
| API документація | https://docs.anthropic.com/en/api |
| Моделі Claude | https://docs.anthropic.com/en/docs/about-claude/models |
| Claude Console | https://console.anthropic.com |
| Pricing | https://www.anthropic.com/pricing |

### MCP та інтеграції

| Ресурс | Посилання |
|--------|-----------|
| MCP специфікація | https://modelcontextprotocol.io |
| Каталог MCP серверів | https://claude.ai/directory |
| Побудова MCP сервера | https://modelcontextprotocol.io/docs/develop/build-server |

### Навчання та туторіали

| Ресурс | Посилання |
|--------|-----------|
| Туторіали | https://claude.com/resources/tutorials |
| Claude Code Web | https://claude.ai/code |
| GitHub (Issues, зворотній зв'язок) | https://github.com/anthropics/claude-code/issues |

---

## Швидка шпаргалка

```bash
# === ВСТАНОВЛЕННЯ ===
curl -fsSL https://claude.ai/install.sh | bash   # macOS/Linux
claude --version                                  # Перевірити

# === БАЗОВЕ ВИКОРИСТАННЯ ===
cd my-project && claude                           # Запустити
claude "поясни цей проект"                        # Швидкий запит
claude -p "знайди баги" && exit                   # Один запит
claude -c                                         # Продовжити сесію

# === ПАМ'ЯТЬ ===
/init                                             # Створити CLAUDE.md
/memory                                           # Переглянути пам'ять
claude "Запам'ятай: ми використовуємо tabs"       # Зберегти

# === МОДЕЛІ ===
claude --model claude-opus-4-7                    # Найпотужніша
claude --model claude-haiku-4-5-20251001          # Найшвидша

# === АВТОМАТИЗАЦІЯ ===
claude --permission-mode bypassPermissions -p \
  "запусти тести і виправ всі помилки"            # Повний автопілот
cat log.txt | claude -p "проаналізуй помилки"     # Через pipe

# === MCP ===
claude mcp add --transport http github \
  https://api.githubcopilot.com/mcp/              # Підключити GitHub
claude mcp list                                    # Список серверів
/mcp                                              # Статус + авторизація

# === SKILLS ===
mkdir -p ~/.claude/skills/my-skill                # Створити skill
/my-skill                                         # Використати
/skills                                           # Переглянути всі
```

---

> **Версія документації:** 2025-05  
> **Актуально для:** Claude Code 2025, моделі Claude Sonnet 4.6 / Opus 4.7 / Haiku 4.5  
> **Офіційна документація:** https://docs.anthropic.com/en/docs/claude-code/overview
