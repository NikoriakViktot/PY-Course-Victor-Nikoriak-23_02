# Echo Bot — Урок 46 (Beginner ⭐)

Навчальний Telegram-бот на aiogram 3.x. Демонструє чисту Router-архітектуру, async handlers та роботу з .env.

---

## Структура проєкту

```
echo_bot/
├── app/
│   ├── handlers/
│   │   ├── start.py      ← /start, /help, /about
│   │   └── echo.py       ← повторення тексту, фото, стікерів
│   ├── keyboards/
│   │   └── reply.py      ← ReplyKeyboard (головне меню)
│   ├── services/
│   │   └── user_service.py  ← облік користувачів (in-memory)
│   ├── bot.py            ← Bot, Dispatcher, startup/shutdown
│   └── config.py         ← .env через os.getenv
├── main.py               ← точка входу, asyncio.run()
├── .env.example
└── requirements.txt
```

---

## Налаштування через BotFather

### Крок 1 — Створити бота

1. Відкрити Telegram → знайти **@BotFather**
2. Надіслати: `/newbot`
3. Ввести назву бота: `My Echo Bot`
4. Ввести username (латиниця, закінчується на `bot`): `my_echo_42_bot`
5. BotFather відповість: `Done! Use this token to access the HTTP API:` і надасть токен

### Крок 2 — Зберегти токен

```
123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
         Це і є BOT_TOKEN — зберігати у .env, НЕ у код!
```

### Крок 3 — Налаштувати команди

У BotFather → `/setcommands` → обрати бота → надіслати:

```
start - Запустити бота
help - Допомога
about - Про бота
```

### Крок 4 — Privacy Mode (важливо для групових чатів)

За замовчуванням бот у групі бачить **лише** повідомлення з @mention і команди.

- `/setprivacy` → обрати бота → `Disable` (бачить усі повідомлення)  
- Або залишити `Enable` (безпечніше для продакшену)

---


# Запуск

# 1. Клонувати / перейти у директорію
```bash
cd module_5/lesson_46_Telegram_API/echo_bot
```

---

# 2. Створити новий venv

```powershell
py -3.12 -m venv .venv
```

---

# 3. Активувати

```powershell
.venv\Scripts\activate
```

---

# 4. Оновити pip

```powershell
python -m pip install --upgrade pip
```

# 5. Встановити залежності
```bash
pip install -r requirements.txt

```
___
# 6. Налаштувати .env
```bash
cp .env.example .env

```
# Відкрити .env та вставити BOT_TOKEN

# 7. Запустити
```bash
python main.py
```

**Очікуваний вивід:**
```
2024-01-15 10:00:00 | INFO     | app.bot | Команди бота зареєстровано в Telegram
2024-01-15 10:00:00 | INFO     | app.bot | Бот запущено: @my_echo_42_bot (id=123456789)
```

---

## Команди бота

| Команда | Опис |
|---------|------|
| `/start` | Привітання + клавіатура |
| `/help` | Список команд |
| `/about` | Інформація про бота |
| Текст | Ехо тексту |
| Фото | Повідомлення про отримання |
| Стікер | Emoji стікера |

---

## Архітектурні рішення

**Чому порядок роутерів важливий:**
```python
dp.include_router(start.router)  # специфічні команди — першими
dp.include_router(echo.router)   # F.text ловить все — останнім
```
Якщо поміняти місцями — `/help` ніколи не спрацює, бо `F.text` спіймає його першим.

**Чому `drop_pending_updates=True`:**  
Якщо бот був вимкнений і накопичилась черга повідомлень — вони будуть проігноровані при старті. Корисно для dev. У production може бути `False` (обробити всі накопичені).

**Чому `.env` а не `config.py` з токеном:**  
Токен у коді = потрапить у git history назавжди. `.env` додається у `.gitignore`.
