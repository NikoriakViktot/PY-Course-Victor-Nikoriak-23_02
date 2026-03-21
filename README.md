# 🐍 Python Programming 

## Python Course Beetroot Academy   — 23.02.2026

Ласкаво просимо 👋  

Цей репозиторій містить:

✅ матеріали занять  
✅ практичні завдання  
✅ домашні роботи  
✅ workflow роботи через GitHub (як у реальній IT-команді)

---

# ⚙️ 0. Встановлення Git (ОБОВʼЯЗКОВО)

Git — це система контролю версій, через яку ми:

- отримуємо матеріали курсу
- здаємо домашні завдання
- отримуємо фідбек

---

## 🪟 Windows

🔗 Офіційна сторінка:
https://git-scm.com/install/windows

🔗 Пряме завантаження:
https://github.com/git-for-windows/git/releases/latest

Завантажте:

```

Git for Windows/x64 Setup

````

### Під час встановлення
✅ Просто натискайте **Next** (налаштування за замовчуванням).

---

## 🍎 macOS

🔗 Інструкція:
https://git-scm.com/install/mac

Відкрийте Terminal:

```bash
xcode-select --install
````

---

## 🐧 Linux

🔗 Інструкція:
[https://git-scm.com/install/linux](https://git-scm.com/install/linux)

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install git
```

### Fedora

```bash
sudo dnf install git
```

### Arch

```bash
sudo pacman -S git
```

---

## ✅ Перевірка встановлення

```bash
git --version
```

Очікуваний результат:

```
git version 2.xx.x
```

---

## ✅ Перше налаштування Git (1 раз)

```bash
git config --global user.name "Your Name"
git config --global user.email "your_email@example.com"
```

⚠️ Email має співпадати з GitHub.

---

# 🧭 Як працює курс

* `main` → матеріали курсу (оновлює викладач)
* домашні роботи → окремі гілки
* здача → Pull Request (PR)
* студентський код **не додається** у main

👉 Pull Request = здача домашнього завдання.

---

# 🚀 Швидкий старт

---

# 1️⃣ Створіть Fork репозиторію

Перейдіть у репозиторій курсу:

```
https://github.com/NikoriakViktot/PY-Course-Victor-Nikoriak-23_02
```

Натисніть кнопку:

```
Fork
```

---

## У вікні **Create a new fork**

Вам потрібно:

**Owner**

```
ваш GitHub акаунт
```

**Repository name**

```
PY-Course-Victor-Nikoriak-23_02
```

---

### Обовʼязково перевірте

✅ **Copy the main branch only** — увімкнено

---

Після цього натисніть:

```
Create fork
```

---

## Що відбудеться

GitHub створить **копію репозиторію у вашому акаунті**.

Вона буде виглядати так:

```
https://github.com/<your-username>/PY-Course-Victor-Nikoriak-23_02
```

Приклад:

```
https://github.com/student123/PY-Course-Victor-Nikoriak-23_02
```

---

## Важливо

Ви **працюєте тільки у своєму fork**.

```
NikoriakViktot/PY-Course-Victor-Nikoriak-23_02  → repo викладача
your-username/PY-Course-Victor-Nikoriak-23_02 → ваш fork
```

---

# 2️⃣ Clone у PyCharm

PyCharm →

```
File → New Project from Version Control
```

Вставте **URL вашого fork**.

```
github.com/<your-username>/PY_Course_Victor-Nikoriak-23_02
```

---


## 3️⃣ Додати upstream (ОДИН РАЗ)

В Terminal:

```bash
git remote add upstream https://github.com/NikoriakViktot/PY-Course-Victor-Nikoriak-23_02.git
```

Перевірка:

```bash
git remote -v
```

Повинно бути:

```
origin   → ваш repo
upstream → repo викладача
```

---


# 🔄 Перед кожним заняттям

Оновлення матеріалів:

```bash
git checkout main
git pull upstream main
git push origin main
```
___
Детальна інструкція по - [Git](module_1/docs/git-cheatsheet.md)
___
# 🚀 Quick Start (Виконання завдань та тестів)

---

## 🪟 Windows (найпростіший спосіб)

1️⃣ Відкрийте папку проєкту  
2️⃣ Двічі натисніть:

- install_course.bat (перший запуск)
- start_course.bat (кожен раз для запуску)

Після запуску з’явиться меню:

----------------------------------------
Python Course -- Select Lesson
----------------------------------------

Введіть номер уроку → натисніть Enter → відкриється браузер.

---

## 🍎 macOS / 🐧 Linux

Відкрийте Terminal у папці проєкту та виконайте:

python3 install_course.py
python3 start_course.py

Після цього оберіть номер уроку.

---

📖 Детальна інструкція з поясненням режимів роботи:

👉 Відкрийте файл [SETUP.md](SETUP.md)
---

# 📚 Домашнє завдання

## ❗ НЕ працюємо у main

---

## Кроки

### 1. Створити гілку

```bash
git checkout -b homework-01
```

---

### 2. Виконати завдання

Редагуйте файли або notebook.

---

### 3. Commit

```bash
git add .
git commit -m "Homework 01"
```

---

### 4. Push

```bash
git push origin homework-01
```

---
## 5️⃣ Здати домашню роботу через Pull Request

### Кроки на GitHub

1️⃣ Відкрити репозиторій на **GitHub**

2️⃣ GitHub часто автоматично покаже кнопку:

```

Compare & pull request

```

Якщо ні — натиснути:

```

New pull request

```

3️⃣ Обрати гілки:

```

base: main
compare: homework-01

```

Тобто:

```

homework-01 → main

```

4️⃣ Натиснути:

```

Create pull request

````

---

## ✅ Отримання фідбеку

Після створення Pull Request:

- викладач перегляне код
- залишить **коментарі**
- запропонує **покращення**

Якщо потрібно внести зміни — просто:

```bash
git add .
git commit -m "fix review comments"
git push
````

Pull Request **оновиться автоматично**.

📖 Детальніше про структуру репозиторію:

👉 [Архітектура репозиторію](architecture.md)

---

# 📏 Правила курсу

- ✅ 1 домашка = 1 гілка
- ✅ нормальні commit messages
- ✅ оновлювати main перед заняттям
---
- ❌ не працювати в main
- ❌ не merge PR
- ❌ не видаляти матеріали курсу

---

# 🧯 Часті проблеми

## Не бачу нові уроки

```bash
git checkout main
git pull upstream main
```

---

## Зробив домашку в main

```bash
git checkout -b homework-XX
git checkout main
git pull upstream main
```

---

## Permission denied

Ви клонували repo викладача замість fork.

Переклонуйте свій fork.

---

# 🧰 Git шпаргалка

```bash
git status
git branch
git checkout branch_name
git log --oneline
```

---

# 🆘 Питання

Надсилайте:

* скрін помилки
* `git status`
* `git remote -v`

І проблема вирішиться швидко 🙂
___

# 🧪 Налаштування середовища Python (venv)

Для кожного проєкту ми використовуємо **віртуальне середовище (venv)**.

👉 Це ізольований Python, який містить **тільки бібліотеки курсу**.

Це потрібно щоб:

* ✅ бібліотеки не конфліктували між проєктами
* ✅ у всіх студентів було однакове середовище
* ✅ ноутбуки працювали однаково

---

## ✅ 1. Перевірка встановленого Python

Відкрийте **Terminal / PowerShell** і виконайте:

```bash
python --version
```

Якщо команда не працює:

```bash
python3 --version
```

Рекомендована версія:

```
Python 3.10+
```

---

# 🪟🍎🐧2. Створення віртуального середовища

Перейдіть у **корінь проєкту**:

```bash
cd your_project_folder
```

Створіть середовище:

```bash
python -m venv .venv
```

(якщо не працює → використайте `python3`)

Буде створено папку:

```
.venv/
```

⚠️ **Цю папку НЕ потрібно додавати в Git.**

---

## ✅ 3. Активація середовища

---

### 🪟 Windows (PowerShell)

```bash
.venv\Scripts\activate
```

### ⚠️ Якщо виникла помилка виконання скриптів:

Виконайте **ОДИН раз**:

```bash
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Після цього повторіть активацію.

---

### 🍎 macOS / 🐧 Linux

```bash
source .venv/bin/activate
```

---

Після успішної активації у терміналі з’явиться:

```
(.venv)
```

✅ Це означає, що середовище активне.

---

## ✅ 4. Встановлення бібліотек курсу

Викладач надає файл:

```
requirements.txt
```

Встановлення:

```bash
pip install -r requirements.txt
```

---

## ✅ 5. Перевірка встановлення

```bash
pip list
```

Ви повинні побачити список встановлених бібліотек.

---

# 🧠 6. Підключення venv у PyCharm

1. **File → Settings**
2. **Project → Python Interpreter**
3. **Add Interpreter**
4. **Existing Environment**
5. Оберіть:

### Windows

```
project_folder/.venv/Scripts/python.exe
```

### macOS / Linux

```
project_folder/.venv/bin/python
```

Натисніть **OK**.

---

# 📓 7. Використання venv у Jupyter Notebook

Встановіть Jupyter kernel:

```bash
pip install ipykernel
```

Додайте середовище як kernel:

```bash
python -m ipykernel install \
--user \
--name python-course \
--display-name "Python Course (.venv)"
```

---

У Notebook:

```
Kernel → Change Kernel → Python Course (.venv)
```

---

# 🔒 8. Ноутбуки із захищеними клітинками

На заняттях використовуються **protected cells**.

Студенти:

✅ можуть запускати код
✅ можуть редагувати дозволені клітинки

❌ не повинні змінювати системні клітинки

Позначення:

```
🔒 DO NOT EDIT
```

---

# 🧹 9. Деактивація середовища

Після завершення роботи:

```bash
deactivate
```

---

# 🚫 10. Важливо для Git (.gitignore)

Віртуальне середовище **НЕ потрібно додавати у Git**.

📖 Офіційна рекомендація GitHub:
https://docs.github.com/en/get-started/getting-started-with-git/ignoring-files
___
Причина:

- `.venv/` містить локальні файли Python
- вони відрізняються на Windows / macOS / Linux
- можуть займати сотні мегабайт
- відтворюються автоматично через `requirements.txt`
___
👉 У репозиторій додається **тільки код**, а не середовище.
---

## ✅ Створіть файл `.gitignore`

У корені проєкту створіть файл:

```

.gitignore

````

І додайте:

```gitignore
# Virtual environment
.venv/

# PyCharm
.idea/

# Python cache
__pycache__/
*.pyc

# Jupyter
.ipynb_checkpoints/
````

---

- ✅ Це стандартна практика у всіх Python-проєктах.

___

# ✅ Готово

Тепер ваше середовище повністю налаштоване і готове до роботи з курсом.

---


## Instructor

Viktor Nikoriak

Hydrologist and Python developer working at the intersection
of hydrology, geospatial analysis and data science.

More information:

- [Instructor profile](instructor.md)

## Certificates

- [Certificates](certificates/beetroot_python_2021.md)
