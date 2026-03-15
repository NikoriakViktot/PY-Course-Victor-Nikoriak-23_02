"""
cli_calculator.py — Повноцінний консольний калькулятор (CLI).

───────────────────────────────────────────────────────────────────────────────
🎯 ЦІЛЬ
Цей файл показує, як зробити калькулятор БЕЗ eval() — тобто без небезпечного
виконання коду. Замість eval() ми:

1) РОЗБИВАЄМО вираз на токени (tokenize)
2) ПЕРЕТВОРЮЄМО інфіксний вираз у постфіксний (RPN) через shunting-yard (to_rpn)
3) ОБЧИСЛЮЄМО RPN через стек (eval_rpn)

───────────────────────────────────────────────────────────────────────────────
✅ ЩО ТАКЕ RPN (Reverse Polish Notation)?
Звичайний (інфіксний) запис:
    2 + 3 * 4

RPN (постфіксний) запис:
    2 3 4 * +

Чому це зручно?
Бо RPN легко обчислювати СТЕКОМ.

───────────────────────────────────────────────────────────────────────────────
📌 СХЕМА АЛГОРИТМУ (ДУЖЕ ВАЖЛИВО ДЛЯ РОЗУМІННЯ)

[1] expr (рядок)
    |
    v
[2] tokenize(expr) -> ["2", "+", "3", "*", "4"]
    |
    v
[3] to_rpn(tokens) -> ["2", "3", "4", "*", "+"]
    |
    v
[4] eval_rpn(rpn) -> 14

───────────────────────────────────────────────────────────────────────────────
▶ Запуск:
    python cli_calculator.py
    python cli_calculator.py --help

▶ Параметри:
    --help
    --once "2+2"
    --history N

▶ Команди в інтерактивному режимі:
    help, history, clear, exit
"""

import sys
# sys — модуль Python для роботи з параметрами командного рядка.
# Наприклад, якщо запускаємо:
#   python cli_calculator.py --once "2+2"
# тоді sys.argv буде:
#   ["cli_calculator.py", "--once", "2+2"]


# ────────────────────────────────────────────────────────────
# 1) ОПИС ОПЕРАТОРІВ
# ────────────────────────────────────────────────────────────
# Ми описуємо кожен оператор трьома характеристиками:
#   prec  — пріоритет (чим більше, тим раніше виконується)
#   assoc — асоціативність: L (left) або R (right)
#   arity — скільки операндів бере оператор:
#           2 — бінарний: a + b
#           1 — унарний: -a  або  +a

OPS = {
    "+": {"prec": 1, "assoc": "L", "arity": 2},
    "-": {"prec": 1, "assoc": "L", "arity": 2},
    "*": {"prec": 2, "assoc": "L", "arity": 2},
    "/": {"prec": 2, "assoc": "L", "arity": 2},
    "//": {"prec": 2, "assoc": "L", "arity": 2},
    "%": {"prec": 2, "assoc": "L", "arity": 2},
    "**": {"prec": 3, "assoc": "R", "arity": 2},
    # u- та u+ — це спеціальні "унарні" оператори.
    # Наприклад: -5  це НЕ "0 - 5", а саме "унарний мінус" застосований до 5.
    "u-": {"prec": 4, "assoc": "R", "arity": 1},
    "u+": {"prec": 4, "assoc": "R", "arity": 1},
}


# ────────────────────────────────────────────────────────────
# 2) ВАЛІДАЦІЯ ЧИСЕЛ БЕЗ try/except
# ────────────────────────────────────────────────────────────

def is_unsigned_int(s: str) -> bool:
    """
    Перевіряє, чи рядок є НЕВІД’ЄМНИМ цілим числом.

    Приклади:
        "10"   -> True
        "0"    -> True
        "-10"  -> False   (бо мінус не дозволяється тут)
        "3.14" -> False
        "abc"  -> False

    Важливо: ми працюємо з токенами без знака.
    Мінус/плюс обробляємо окремо як u- / u+.
    """
    s = s.strip()
    # bool(s) гарантує, що рядок не пустий
    # s.isdigit() перевіряє, що всі символи — цифри
    return bool(s) and s.isdigit()


def is_unsigned_float(s: str) -> bool:
    """
    Перевіряє, чи рядок є НЕВІД’ЄМНИМ числом з крапкою (або без).

    Дозволяє:
        "12"    -> True
        "12."   -> True
        ".5"    -> True
        "12.5"  -> True

    Не дозволяє:
        ""      -> False
        "."     -> False
        "1.2.3" -> False
        "a.5"   -> False

    Без try/except: тільки логічні перевірки.
    """
    s = s.strip()

    # 1) Порожній рядок — одразу не число
    if not s:
        return False

    # 2) Якщо тільки цифри — це валідне число
    if s.isdigit():
        return True

    # 3) Дрібне число має мати рівно одну крапку
    if s.count(".") != 1:
        return False

    # 4) Розділяємо на ліву та праву частину
    left, right = s.split(".", 1)

    # Випадок "." -> left="" і right=""
    if left == "" and right == "":
        return False

    # 5) Якщо ліва частина не пуста — має бути цифрами
    if left != "" and not left.isdigit():
        return False

    # 6) Якщо права частина не пуста — має бути цифрами
    if right != "" and not right.isdigit():
        return False

    return True


def is_number_token(s: str) -> bool:
    """
    У нас в токенах числа вже БЕЗ знака +/-.
    Бо знак обробляється в to_rpn як u- або u+.
    """
    return is_unsigned_float(s)


def to_number(s: str) -> float:
    """
    Безпечно перетворює рядок у float, бо ми вже перевірили токен валідатором.
    """
    return float(s)


# ────────────────────────────────────────────────────────────
# 3) ТОКЕНІЗАЦІЯ: рядок -> список токенів
# ────────────────────────────────────────────────────────────
# Токен — це "атом" виразу:
#   число, оператор, дужка
#
# Приклад:
#   " (2 + 3) * 4 "
# стане:
#   ["(", "2", "+", "3", ")", "*", "4"]

def tokenize(expr: str) -> tuple[bool, list[str] | str]:
    """
    Перетворює рядок expr у список токенів.
    Повертає:
        (True, tokens)  якщо все ок
        (False, error)  якщо знайшли помилку
    """
    s = expr.strip()

    # Якщо після strip() рядок пустий — це помилка
    if not s:
        return False, "Порожній вираз."

    tokens: list[str] = []
    i = 0
    n = len(s)

    # Поки не дійшли до кінця рядка — читаємо символи
    while i < n:
        ch = s[i]

        # 1) Пробіли пропускаємо
        if ch.isspace():
            i += 1
            continue

        # 2) Дужки — це окремі токени
        if ch in "()":
            tokens.append(ch)
            i += 1
            continue

        # 3) Оператори з 2 символів: // і **
        #    треба перевірити їх раніше за односимвольні
        if i + 1 < n:
            two = s[i:i + 2]
            if two in ("//", "**"):
                tokens.append(two)
                i += 2
                continue

        # 4) Оператори з 1 символу
        if ch in "+-*/%":
            tokens.append(ch)
            i += 1
            continue

        # 5) Число: може починатися з цифри або крапки
        if ch.isdigit() or ch == ".":
            j = i
            dot_count = 0

            # Читаємо "підряд" усе, що схоже на число (цифри + крапка)
            while j < n and (s[j].isdigit() or s[j] == "."):
                if s[j] == ".":
                    dot_count += 1
                    # Якщо дві крапки — виходимо, щоб зібрати raw_num
                    # і видати нормальну помилку валідатора
                    if dot_count > 1:
                        break
                j += 1

            raw_num = s[i:j]

            # Перевіряємо наш валідатор
            if not is_number_token(raw_num):
                return False, f"Некоректне число: '{raw_num}'"

            tokens.append(raw_num)
            i = j
            continue

        # Якщо символ не вписався у жодне правило — він невідомий
        return False, f"Невідомий символ: '{ch}'"

    return True, tokens


# ────────────────────────────────────────────────────────────
# 4) SHUNTING-YARD: інфіксний -> RPN
# ────────────────────────────────────────────────────────────
# Ідея:
#   - Вихід (out) збирає RPN
#   - Стек (stack) тимчасово тримає оператори і дужки
#
# Приклад:
#   tokens: ["2", "+", "3", "*", "4"]
#   rpn:    ["2", "3", "4", "*", "+"]

def to_rpn(tokens: list[str]) -> tuple[bool, list[str] | str]:
    """
    Перетворює список токенів (інфікс) у RPN (постфікс).
    """
    out: list[str] = []     # сюди будемо додавати готові токени RPN
    stack: list[str] = []   # стек для операторів і дужок

    # prev_type потрібен, щоб зрозуміти, коли + або - є УНАРНИМИ.
    # Наприклад:
    #   "-5"     -> u- 5
    #   "2*-3"   -> 2 * (u- 3)
    prev_type = "START"  # START | NUM | OP | LPAREN | RPAREN

    for tok in tokens:
        # ── 1) Ліва дужка: просто кладемо в стек
        if tok == "(":
            stack.append(tok)
            prev_type = "LPAREN"
            continue

        # ── 2) Права дужка: викидаємо зі стеку все до "("
        if tok == ")":
            found = False
            while stack:
                top = stack.pop()
                if top == "(":
                    found = True
                    break
                out.append(top)

            # Якщо "(" так і не знайшли — значить дужки неправильні
            if not found:
                return False, "Помилка дужок: зайва ')'."

            prev_type = "RPAREN"
            continue

        # ── 3) Число: відразу у вихід
        if is_number_token(tok):
            out.append(tok)
            prev_type = "NUM"
            continue

        # ── 4) Оператор:
        # Якщо tok == "+" або "-" і він стоїть:
        #   - на початку
        #   - після іншого оператора
        #   - після "("
        # тоді це унарний оператор
        if tok in ("+", "-"):
            if prev_type in ("START", "OP", "LPAREN"):
                tok = "u+" if tok == "+" else "u-"

        # Якщо оператора нема в OPS — це помилка
        if tok not in OPS:
            return False, f"Невідомий оператор: '{tok}'"

        # o1 — поточний оператор
        o1 = tok
        p1 = OPS[o1]["prec"]
        a1 = OPS[o1]["assoc"]

        # Поки в стеку є оператори, які треба "вивантажити" у out
        while stack:
            o2 = stack[-1]

            # Якщо на вершині стеку не оператор (наприклад "("), зупиняємось
            if o2 not in OPS:
                break

            p2 = OPS[o2]["prec"]

            # Умова з shunting-yard:
            # - для лівоасоціативних: вивантажуємо поки p1 <= p2
            # - для правоасоціативних: вивантажуємо поки p1 <  p2
            if (a1 == "L" and p1 <= p2) or (a1 == "R" and p1 < p2):
                out.append(stack.pop())
            else:
                break

        # Кладемо поточний оператор у стек
        stack.append(o1)
        prev_type = "OP"

    # Після проходу всіх токенів — зливаємо залишок стеку
    while stack:
        top = stack.pop()
        # Якщо в стеку лишилась "(" або ")" — дужки не закриті
        if top in ("(", ")"):
            return False, "Помилка дужок: не закрито '('."
        out.append(top)

    return True, out


# ────────────────────────────────────────────────────────────
# 5) ОБЧИСЛЕННЯ RPN ЧЕРЕЗ СТЕК
# ────────────────────────────────────────────────────────────
# Правило:
#   - якщо токен число -> push у стек
#   - якщо токен оператор:
#         * якщо arity=2 -> pop b, pop a, push (a op b)
#         * якщо arity=1 -> pop a, push (op a)

def apply_op(op: str, stack: list[float]) -> tuple[bool, str | None]:
    """
    Виконує один оператор над стеком.

    Повертає:
        (True, None)  якщо виконали успішно
        (False, err)  якщо помилка (недостатньо операндів, ділення на нуль тощо)
    """
    arity = OPS[op]["arity"]

    # ── Унарний оператор (u- або u+)
    if arity == 1:
        if len(stack) < 1:
            return False, "Помилка: недостатньо операндів (унарний оператор)."

        a = stack.pop()

        if op == "u-":
            stack.append(-a)
        elif op == "u+":
            stack.append(+a)
        else:
            return False, f"Невідомий унарний оператор: {op}"

        return True, None

    # ── Бінарний оператор: треба 2 числа у стеку
    if len(stack) < 2:
        return False, "Помилка: недостатньо операндів."

    # Важливо: перше pop() — це правий операнд b
    #          друге pop() — лівий операнд a
    b = stack.pop()
    a = stack.pop()

    if op == "+":
        stack.append(a + b)
    elif op == "-":
        stack.append(a - b)
    elif op == "*":
        stack.append(a * b)
    elif op == "/":
        if b == 0:
            return False, "Ділення на нуль."
        stack.append(a / b)
    elif op == "//":
        if b == 0:
            return False, "Ділення на нуль."
        stack.append(a // b)
    elif op == "%":
        if b == 0:
            return False, "Ділення на нуль."
        stack.append(a % b)
    elif op == "**":
        stack.append(a ** b)
    else:
        return False, f"Невідомий оператор: {op}"

    return True, None


def eval_rpn(rpn: list[str]) -> tuple[bool, float | str]:
    """
    Обчислює RPN-вираз.

    ✅ Приклад "малюнка" роботи стеку:
    RPN: 2 3 4 * +

    Крок 1: токен 2  -> push
        stack: [2]
    Крок 2: токен 3  -> push
        stack: [2, 3]
    Крок 3: токен 4  -> push
        stack: [2, 3, 4]
    Крок 4: токен *  -> pop 4, pop 3, push 12
        stack: [2, 12]
    Крок 5: токен +  -> pop 12, pop 2, push 14
        stack: [14]
    Кінець: в стеку рівно 1 число -> відповідь
    """
    st: list[float] = []

    for tok in rpn:
        # Якщо токен число — кладемо у стек
        if is_number_token(tok):
            st.append(to_number(tok))
            continue

        # Якщо це не число — має бути оператор
        if tok not in OPS:
            return False, f"Невідомий токен в RPN: '{tok}'"

        ok, err = apply_op(tok, st)
        if not ok:
            return False, err

    # Після обробки всіх токенів має лишитись одне число
    if len(st) != 1:
        return False, "Помилка: вираз не згорнувся до одного значення."

    return True, st[0]


def evaluate(expr: str) -> tuple[bool, float | str]:
    """
    Головна функція "обчислити вираз".
    Тут зібрані всі три етапи пайплайну:
        expr -> tokens -> rpn -> result
    """
    ok, t = tokenize(expr)
    if not ok:
        return False, t

    ok, r = to_rpn(t)  # type: ignore[arg-type]
    if not ok:
        return False, r

    return eval_rpn(r)  # type: ignore[arg-type]


# ────────────────────────────────────────────────────────────
# 6) CLI: довідка + форматування + аргументи
# ────────────────────────────────────────────────────────────

def print_help() -> None:
    """
    Друкує довідку для користувача.
    """
    print("=" * 52)
    print("CLI Калькулятор — довідка")
    print("=" * 52)
    print("Підтримка:")
    print("  Оператори: +  -  *  /  //  %  **")
    print("  Дужки: ( )")
    print("  Числа: 2, 3.14, .5, 12., -5")
    print()
    print("Команди:")
    print("  help     — показати довідку")
    print("  history  — показати історію")
    print("  clear    — очистити історію")
    print("  exit     — вийти")
    print()
    print("Приклади:")
    print("  2 + 2 * 3")
    print("  (2 + 2) * 3")
    print("  -3 + 5 * 2")
    print("  2 ** 3 ** 2    # степінь правоасоціативний")
    print("=" * 52)


def format_number(x: float) -> str:
    """
    Робить красивий вивід числа.
    Наприклад:
        5.0 -> "5"
        5.25 -> "5.25"
    """
    if x == int(x):
        return str(int(x))
    return str(x)


def parse_args(argv: list[str]) -> dict:
    """
    Парсить аргументи командного рядка (sys.argv).

    Підтримка:
      --help
      --once "<expr>"
      --history N

    Повертає словник конфігурації:
      {
        "help": bool,
        "once": str | None,
        "history_n": int
      }
    """
    args = {"help": False, "once": None, "history_n": 20}

    # Якщо аргументів немає (тільки ім'я файлу) — повертаємо дефолти
    if len(argv) <= 1:
        return args

    i = 1
    while i < len(argv):
        a = argv[i]

        if a == "--help":
            args["help"] = True
            i += 1
            continue

        if a == "--once":
            # --once повинен мати наступний аргумент з виразом
            if i + 1 >= len(argv):
                args["once"] = ""
                i += 1
                continue

            args["once"] = argv[i + 1]
            i += 2
            continue

        if a == "--history":
            # якщо є наступне значення і воно ціле — приймаємо
            if i + 1 < len(argv) and is_unsigned_int(argv[i + 1]):
                args["history_n"] = int(argv[i + 1])
                i += 2
            else:
                # некоректно або нема значення — ігноруємо, лишаємо дефолт
                i += 1
            continue

        # невідомий аргумент — просто пропускаємо
        i += 1

    return args


# ────────────────────────────────────────────────────────────
# 7) MAIN: режим --once або інтерактивний режим
# ────────────────────────────────────────────────────────────

def main() -> None:
    """
    Точка запуску програми.
    """
    cfg = parse_args(sys.argv)

    # Якщо користувач попросив help — показуємо і завершуємо
    if cfg["help"]:
        print(__doc__)
        print_help()
        return

    # Історія: список кортежів (вираз, результат)
    history: list[tuple[str, str]] = []

    # Режим одноразового обчислення:
    #   python cli_calculator.py --once "2+2"
    if cfg["once"] is not None:
        expr = str(cfg["once"]).strip()
        if not expr:
            print("⚠️ Порожній вираз для --once.")
            return

        ok, res = evaluate(expr)
        if ok:
            out = format_number(res)  # type: ignore[arg-type]
            print(out)
        else:
            print("⚠️ Помилка:", res)
        return

    # Інакше — запускаємо інтерактивний режим
    print("=" * 52)
    print("  Повноцінний CLI Калькулятор")
    print("  Напишіть: help | history | clear | exit")
    print("=" * 52)

    while True:
        raw = input("\ncalc> ").strip()

        if not raw:
            print("⚠️ Введіть вираз або команду (help).")
            continue

        cmd = raw.lower()

        # ── Команда виходу
        if cmd == "exit":
            print("Роботу завершено. До побачення! 👋")
            break

        # ── Довідка
        if cmd == "help":
            print_help()
            continue

        # ── Очистити історію
        if cmd == "clear":
            history.clear()
            print("✅ Історію очищено.")
            continue

        # ── Показати історію
        if cmd == "history":
            if not history:
                print("Історія порожня.")
                continue

            n = cfg["history_n"]
            tail = history[-n:]

            print("=" * 52)
            # enumerate дає нам порядковий номер (idx) і значення (e, r)
            # start=... щоб нумерація відповідала глобальній історії
            for idx, (e, r) in enumerate(
                tail,
                start=max(1, len(history) - len(tail) + 1)
            ):
                print(f"{idx:>3}. {e} = {r}")
            print("=" * 52)
            continue

        # Якщо це не команда — вважаємо, що це вираз
        ok, res = evaluate(raw)

        if ok:
            out = format_number(res)  # type: ignore[arg-type]
            print(out)
            history.append((raw, out))
        else:
            print("⚠️ Помилка:", res)
            history.append((raw, f"ERROR: {res}"))


# ────────────────────────────────────────────────────────────
# 8) ТОЧКА ВХОДУ
# ────────────────────────────────────────────────────────────
# Це стандартний патерн Python:
#   якщо файл запускають напряму -> виконуємо main()
#   якщо файл імпортують -> main() НЕ запускається автоматично

if __name__ == "__main__":
    main()