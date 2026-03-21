# 📘 Git Cheatsheet для студентів

## Що таке Git

**Git** — це система контролю версій.

Вона дозволяє:

* зберігати історію змін коду
* працювати у команді
* повернутись до попередніх версій
* відправляти код на GitHub
* співпрацювати через Pull Request

Git використовують **усі IT-компанії**.

---

# Як Git зберігає історію

Git не зберігає просто файли.

Він створює **ланцюжок commit**.

```mermaid
gitGraph
   commit id: "init"
   commit id: "lesson 01"
   commit id: "lesson 02"
   commit id: "lesson 03"
```

Кожен commit — це **знімок проєкту у певний момент часу**.

---

# Що таке commit

Commit — це **збереження змін у репозиторії**.

Кожен commit має:

* автора
* дату
* опис
* список змінених файлів

Приклад:

```
commit 91ab21
Author: Student
Message: Homework 04
```

---

# Що таке branch

Branch — це **окрема гілка розробки**.

```mermaid
gitGraph
   commit id: "lesson 01"
   commit id: "lesson 02"
   branch homework-01
   commit id: "task1"
   commit id: "task2"
   checkout main
   commit id: "lesson 03"
```

Це дозволяє:

* працювати над новим кодом
* не ламати основний код

---

# Структура курсу

У курсі використовується такий workflow.

```mermaid
flowchart LR

A[Teacher Repository<br>course materials]
--> B[Student Fork]

B --> C[Local Repository]

C --> D[Homework Branch]

D --> E[Commit]

E --> F[Push]

F --> G[Pull Request]

G --> H[Review]

H --> I[Feedback]
```

---

# Репозиторії у курсі

У студентів є **два remote**.

```mermaid
flowchart LR

A[Teacher Repository<br>upstream]
--> B[Student Fork<br>origin]

B --> C[Local Repository<br>your computer]
```

---

# Remote repositories

Перевірити remote:

```bash
git remote -v
```

Приклад:

```
origin   → ваш fork
upstream → repo викладача
```

| remote   | значення               |
| -------- | ---------------------- |
| origin   | ваш GitHub репозиторій |
| upstream | репозиторій викладача  |

---

# Найважливіші команди Git

Для роботи на курсі студентам достатньо знати **8 базових команд Git**.

| Команда           | Короткий опис              |
| ----------------- | -------------------------- |
| `git status`      | показує стан репозиторію   |
| `git branch`      | показує список гілок       |
| `git switch`      | переключає між гілками     |
| `git checkout -b` | створює нову гілку         |
| `git add`         | додає файли до commit      |
| `git commit`      | зберігає зміни             |
| `git push`        | відправляє зміни на GitHub |
| `git pull`        | отримує зміни з GitHub     |

Ці команди покривають **приблизно 90% роботи з Git**.

---

# 1️⃣ git status

```bash
git status
```

### Що робить команда

Показує **поточний стан репозиторію**.

Git повідомляє:

* у якій гілці ви знаходитесь
* які файли змінені
* які файли нові
* які файли готові до commit

---

### Приклад

```
On branch homework-01

Changes not staged for commit:
  modified: task1.py

Untracked files:
  test.py
```

---

# 2️⃣ git branch

```bash
git branch
```

Показує всі **гілки репозиторію**.

```
* main
homework-01
homework-02
```

`*` означає **активну гілку**.

---

# 3️⃣ git switch

```bash
git switch branch_name
```

Переключає на іншу гілку.

```
git switch main
```

---

# 4️⃣ git checkout -b

```bash
git checkout -b branch_name
```

Створює нову гілку **і одразу переходить у неї**.

```
git checkout -b homework-05
```

```mermaid
gitGraph
   commit id: "lesson"
   branch homework-05
   commit id: "task1"
```

---

# 5️⃣ git add

```bash
git add file_name
```

або

```
git add .
```

Додає файли у **staging area**.

```mermaid
flowchart LR

A[Working Directory<br>ваші файли]
--> |git add| B[Staging Area<br>підготовлені зміни]
```

---

# 6️⃣ git commit

```bash
git commit -m "message"
```

Створює **commit** — збереження змін у історії Git.

```
git commit -m "Homework 01"
```

```mermaid
gitGraph
   commit id: "lesson"
   commit id: "homework"
```

---

# 7️⃣ git push

```bash
git push origin branch_name
```

Відправляє commit **на GitHub**.

```mermaid
flowchart LR

A[Local Repository]
-- git push -->
B[GitHub Repository]
```

---

# 8️⃣ git pull

```bash
git pull
```

Отримує нові зміни **з GitHub**.

Фактично:

```
git fetch
git merge
```

```mermaid
flowchart LR

A[GitHub Repository]
-- git pull -->
B[Local Repository]
```

---

# Повний workflow студента

```mermaid
flowchart LR

A[Update main<br>git pull upstream main]
--> B[Create branch<br>git checkout -b homework]

B --> C[Write code]

C --> D[git add]

D --> E[git commit]

E --> F[git push]

F --> G[Pull Request]

G --> H[Review]

H --> I[Feedback]
```

---

# Merge

Merge — це **об'єднання гілок**.

```mermaid
gitGraph
   commit
   commit
   branch homework
   commit
   commit
   checkout main
   merge homework
```

---

# Головне правило Git

Перед будь-якою роботою перевіряйте:

```
git status
```

---

# Порада

Git здається складним лише на початку.

Через кілька тижнів роботи ці команди стають **повністю автоматичними**.

---

# Корисні ресурси

Git documentation
[https://git-scm.com/docs](https://git-scm.com/docs)

Git visualization
[https://git-school.github.io/visualizing-git/](https://git-school.github.io/visualizing-git/)

---

