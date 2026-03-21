# 🧠 Python Mental Model
## Як насправді працює Python

Більшість проблем початківців виникає не через синтаксис Python,  
а через нерозуміння **що саме запускається на комп’ютері**.

Цей документ пояснює базову модель.

---

# 🧩 Велика картина

У Python є **5 різних речей**, які часто плутають:

```

IDE
↓
Interpreter
↓
Virtual Environment (venv)
↓
pip
↓
Libraries

```

Розглянемо кожну окремо.

---

# 🐍 1. Python Interpreter

## Що це?

Python Interpreter — це **програма**, яка виконує Python код.

Файл:

```
python.exe
```

або

```
python
````

---

## Що відбувається

Коли ви пишете:

```python
print("Hello")
````

інтерпретатор:

1. читає код
2. перекладає його
3. виконує інструкції

---

- ✅ Python = програма
- ❌ Python ≠ IDE
- ❌ Python ≠ бібліотеки

---

# 📦 2. pip

## Що таке pip?

`pip` — це **менеджер пакетів**.

Він встановлює бібліотеки.

---

Приклад:

```bash
pip install numpy
```

pip:

* завантажує пакет з інтернету
* копіює його у Python environment

---

- ✅ pip встановлює бібліотеки
- ❌ pip НЕ запускає Python

---

# 🧪 3. Virtual Environment (venv)

## Проблема без venv

Якщо встановлювати бібліотеки глобально:

```
Python
 ├ numpy v1
 ├ pandas v2
 └ matplotlib v3
```

Інший проєкт може вимагати інші версії.

💥 конфлікт.

---

## Рішення — venv

`venv` створює **окремий Python** для проєкту.

```
Project A
 └ .venv → власний Python

Project B
 └ .venv → інший Python
```

---

### Створення

```bash
python -m venv .venv
```

---

### Активація

Windows:

```bash
.venv\Scripts\activate
```

macOS / Linux:

```bash
source .venv/bin/activate
```

---

- ✅ venv ізолює бібліотеки
- ❌ venv НЕ змінює Python мову

---

# 🔧 4. IDE (PyCharm / VS Code)

IDE — це **редактор коду**.

Вона:

* допомагає писати код
* підсвічує синтаксис
* запускає Python

---

ВАЖЛИВО:

IDE **сама не виконує код**.

Вона просто викликає:

```
Python Interpreter
```

---

## Реальна схема

```
PyCharm
   ↓
Python Interpreter
   ↓
venv
   ↓
installed libraries
```

---

# 📓 5. Jupyter Notebook

Notebook — це інтерфейс запуску Python.

Він працює через:

```
Kernel
```

Kernel = Python interpreter з environment.

---

Тому потрібно вибирати правильний kernel:

```
Python Course (.venv)
```

---

# 🚨 Найчастіші помилки

---

## ❌ "Я встановив бібліотеку, але import не працює"

Причина:

pip встановив пакет в інший Python.

---

## ❌ "У PyCharm працює, а в Notebook ні"

Причина:

різні interpreter / kernel.

---

## ❌ "Python зламався"

Зазвичай:

environment не активований.

---

# ✅ Золоте правило Python

Перед роботою:

```
Activate environment → Install packages → Run code
```

---

# 🧠 Фінальна модель

Уявіть Python як кухню:

| Річ       | Аналогія           |
| --------- | ------------------ |
| Python    | кухня              |
| pip       | доставка продуктів |
| venv      | окрема кухня       |
| libraries | інгредієнти        |
| IDE       | робочий стіл       |
| Notebook  | кулінарна книга    |

---

# ✅ Головна ідея

- Python = Interpreter
- pip = Package manager
- venv = Isolation
- IDE = Tool
- Notebook = Interface
---
## Якщо це зрозуміло — 80% проблем з Python зникають.




