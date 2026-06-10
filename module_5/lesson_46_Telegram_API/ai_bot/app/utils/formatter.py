"""
app/utils/formatter.py — Конвертація Markdown → Telegram HTML.

РОЛЬ У АРХІТЕКТУРІ:
    Google Gemini повертає відповіді у форматі Markdown.
    Telegram підтримує HTML (не Markdown безпосередньо).
    Цей модуль виступає конвертером між двома форматами.

ЧОМУ НЕ parse_mode=MARKDOWNV2:
    Можна надіслати відповідь з parse_mode=MarkdownV2 і Telegram сам розбере.
    Але MarkdownV2 дуже суворий: потребує екранування _*[]()~`>#+-.!
    Відповіді Gemini часто містять ці символи у звичайному тексті →
    Telegram падає з помилкою "Bad Request: can't parse entities".

    HTML parse_mode надійніший: лише < > & потребують екранування,
    а решта символів передаються як є.

КОНВЕРТАЦІЯ ЯКА ВІДБУВАЄТЬСЯ:
    Markdown                        → Telegram HTML
    ─────────────────────────────────────────────────
    ```python\n код \n```           → <pre><code class="language-python">код</code></pre>
    ```\n код \n```                 → <pre>код</pre>
    `inline code`                   → <code>inline code</code>
    **жирний**                      → <b>жирний</b>
    *курсив*                        → <i>курсив</i>
    - пункт                         → • пункт
    1. пункт                        → 1. пункт (без змін)

ПОРЯДОК ЗАСТОСУВАННЯ ФУНКЦІЙ:
    format_ai_response() викликає функції у правильному порядку:
        1. format_code_blocks()    — спочатку блоки коду (щоб не зіпсувати `inline`)
        2. format_markdown_lists() — списки
        3. format_inline_markdown() — inline: `код`, **жирний**, *курсив*

    Порядок важливий: якщо format_inline_markdown() йде раніше format_code_blocks(),
    він може змінити код всередині ``` блоків.

MAX_MESSAGE_LEN:
    Telegram обмежує одне повідомлення до 4096 символів.
    Ми використовуємо 4000 (з запасом для HTML тегів, що Telegram рахує).
    split_long_message() розбиває довгі відповіді на частини.
"""
import html
import re

# Ліміт для одного Telegram-повідомлення
# Telegram: 4096 символів. Ми беремо 4000 — з запасом для HTML тегів.
MAX_MESSAGE_LEN = 4000


def format_code_blocks(text: str) -> str:
    """
    Конвертує Markdown блоки коду у Telegram HTML.

    Markdown:
        ```python
        print("hello")
        ```

        ```
        some code
        ```

    → Telegram HTML:
        <pre><code class="language-python">print(&quot;hello&quot;)</code></pre>
        <pre>some code</pre>

    re.DOTALL:
        Без цього прапора "." у regex не матчить символи нового рядка \n.
        З DOTALL "." матчить ВСЕ включно з \n.
        Це потрібно для багаторядкових блоків коду.

    html.escape(code):
        Екранує < > & всередині коду → щоб Telegram не намагався
        парсити код як HTML теги.
        Наприклад: x < 10 → x &lt; 10

    Regex: r"```(\w+)?\n(.*?)```"
        ```      — початок блоку коду
        (\w+)?   — опціональна назва мови (python, js, sql тощо)
        \n       — перенос рядка після мови
        (.*?)    — вміст блоку (non-greedy, з DOTALL)
        ```      — кінець блоку коду
    """
    # Regex pattern: знаходить ``` блоки з опціональною назвою мови
    pattern = r"```(\w+)?\n(.*?)```"

    def replacer(match: re.Match) -> str:
        """
        Функція-замінник для re.sub.
        Викликається для кожного знайденого ``` блоку.
        """
        # match.group(1) — назва мови ("python", "sql" тощо) або None
        language = match.group(1) or ""

        # match.group(2) — вміст блоку коду
        # strip() прибирає зайві пробіли/переноси на початку і кінці
        # html.escape() екранує спецсимволи HTML всередині коду
        code = html.escape(match.group(2).strip())

        if language:
            # З назвою мови: <pre><code class="language-python">...</code></pre>
            # class="language-X" — стандарт для syntax highlighting бібліотек
            return f'<pre><code class="language-{language}">{code}</code></pre>'

        # Без назви мови: просто <pre>блок коду</pre>
        return f"<pre>{code}</pre>"

    # re.sub: замінює всі знайдені ``` блоки результатом replacer()
    # re.DOTALL: крапка матчить і \n (для багаторядкових блоків)
    return re.sub(pattern, replacer, text, flags=re.DOTALL)


def format_markdown_lists(text: str) -> str:
    """
    Конвертує Markdown списки у Telegram-friendly формат.

    Telegram HTML НЕ підтримує <ul>, <li>, <ol> теги.
    Натомість використовуємо символ • (bullet point) для маркованих списків.

    Markdown:
        - Перший пункт
        * Другий пункт
        - Третій пункт

    → Результат:
        • Перший пункт
        • Другий пункт
        • Третій пункт

    Нумеровані списки:
        1. Крок перший
        2. Крок другий

    → Залишаємо без змін (вже читабельно):
        1. Крок перший
        2. Крок другий

    Regex пояснення для маркованих списків:
        (?m)     — multiline режим: ^ матчить початок КОЖНОГО рядка
        ^\s*     — початок рядка + опціональні пробіли (відступ)
        [-*]     — дефіс або зірочка (обидва є маркерами Markdown списку)
        \s+      — пробіл(и) після маркера

    Regex пояснення для нумерованих:
        ^\s*     — початок рядка + відступ
        \d+\.    — одна або більше цифр + крапка (1. 2. 10. тощо)
        \s+      — пробіл після номера
        lambda: m.group(0).strip() + " " — прибирає відступ, залишає "1. "
    """
    # Маркований список: "  - текст" → "• текст"
    # або "  * текст" → "• текст"
    text = re.sub(r"(?m)^\s*[-*]\s+", "• ", text)

    # Нумерований список: "  1. текст" → "1. текст"
    # Прибираємо відступ, але зберігаємо "1. "
    text = re.sub(
        r"(?m)^\s*\d+\.\s+",
        lambda m: m.group(0).strip() + " ",
        text,
    )

    return text


def format_inline_markdown(text: str) -> str:
    """
    Конвертує inline Markdown синтаксис у Telegram HTML теги.

    Що конвертується:
        `код`         → <code>код</code>     (inline code)
        **жирний**    → <b>жирний</b>        (bold)
        *курсив*      → <i>курсив</i>        (italic)

    ВАЖЛИВО: ця функція застосовується ПІСЛЯ format_code_blocks().
    Якщо б вона йшла першою — могла б змінити вміст ``` блоків.

    Regex для `inline code`:
        `([^`]+)` — текст між зворотними лапками, не жадібний, без вкладення.

    Regex для **bold**:
        \*\*(.+?)\*\* — текст між подвійними зірочками.
        Обережно: .+? (non-greedy) — щоб не захопити зайвого.

    Regex для *italic*:
        (?<!\*)  — lookbehind: зірочка НЕ передує ще одній зірочці
        \*       — відкриваюча одна зірочка
        (?!\*)   — lookahead: після зірочки немає ще однієї
        (.+?)    — вміст (non-greedy)
        (?<!\*)  — lookbehind: перед закриваючою зірочкою немає ще однієї
        \*       — закриваюча зірочка
        (?!\*)   — lookahead: після закриваючої немає ще однієї

    Навіщо lookahead/lookbehind для *italic*?
        Без них: **жирний** спочатку замінив би *(жирни)* на <i>(жирни)</i>.
        Комплексний regex гарантує, що * і ** не плутаються.
    """
    # `inline code` → <code>inline code</code>
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)

    # **жирний** → <b>жирний</b>
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

    # *курсив* → <i>курсив</i>
    # Lookbehind/lookahead запобігають плутанині з **
    text = re.sub(
        r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)",
        r"<i>\1</i>",
        text,
    )

    return text


def format_ai_response(text: str) -> str:
    """
    Повна конвертація AI відповіді: Markdown → Telegram HTML + шапка.

    Застосовує перетворення у правильному порядку:
        1. Блоки коду — спочатку (захищаємо вміст від наступних regex)
        2. Списки
        3. Inline Markdown

    Додає шапку "🧠 AI Assistant" для візуального виділення відповіді.

    Результат:
        🧠 <b>AI Assistant</b>
        ━━━━━━━━━━━━━━

        (текст відповіді з Telegram HTML форматуванням)
    """
    # Застосовуємо конвертери у правильному порядку
    text = format_code_blocks(text)     # ``` → <pre><code>
    text = format_markdown_lists(text)  # - → •
    text = format_inline_markdown(text) # ** → <b>, * → <i>, ` → <code>

    # Додаємо шапку з декоративним роздільником
    return (
        "🧠 <b>AI Assistant</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        f"{text}"
    )


def split_long_message(text: str) -> list[str]:
    """
    Розбиває довгий текст на список чанків до MAX_MESSAGE_LEN символів.

    Telegram обмежує одне повідомлення до 4096 символів.
    Якщо відповідь AI довша — надсилаємо кількома повідомленнями.

    Алгоритм: простий slice по довжині.
        text[0:4000]    — перший чанк
        text[4000:8000] — другий чанк
        text[8000:...]  — третій чанк

    Проблема (відома):
        Простий slice може розрізати текст посередині HTML-тегу.
        Наприклад: "<b>жирн" і "ий текст</b>" у різних повідомленнях.
        Telegram може відхилити таке повідомлення.
        Для production краще шукати "безпечне місце" для розрізу (\n, пробіл).
        Поточна реалізація достатня для навчального проєкту.

    Повертає:
        [text]           — якщо текст вміщується у одне повідомлення
        [chunk1, chunk2] — якщо потрібно кілька повідомлень
    """
    # Якщо текст коротший за ліміт — повертаємо як єдиний елемент списку
    if len(text) <= MAX_MESSAGE_LEN:
        return [text]

    # range(0, len(text), MAX_MESSAGE_LEN) генерує: 0, 4000, 8000, 12000...
    # text[i:i + MAX_MESSAGE_LEN] — зрізи по MAX_MESSAGE_LEN символів
    return [
        text[i: i + MAX_MESSAGE_LEN]
        for i in range(0, len(text), MAX_MESSAGE_LEN)
    ]
