# 🧠 Ієрархія пошуку атрибутів у Python (`__getattribute__`)

## 🔍 Загальна ідея

```text
obj.attr → Python запускає алгоритм пошуку
```

---

## 🔁 Повний алгоритм

```mermaid
flowchart TD
    A[obj.attr] --> B{Data Descriptor?}
    B -- Yes --> B1[call __get__]
    B -- No --> C{instance dict has attr?}
    C -- Yes --> C1[return value]
    C -- No --> D{Non-data Descriptor?}
    D -- Yes --> D1[call __get__]
    D -- No --> E{class or MRO has attr?}
    E -- Yes --> E1[return value]
    E -- No --> F[AttributeError then getattr]
```

---

# 🥇 1. Data Descriptor (найвищий пріоритет)

👉 Атрибут у класі має:

* `__get__`
* і **`__set__` або `__delete__`**

---

### 💡 Приклад

```python
class A:
    @property
    def x(self):
        return 100

a = A()
a.x
```

---

### ⚠️ Навіть якщо:

```python
a.__dict__['x'] = 999
```

```python
print(a.x)  # → 100
```

---

### 🧠 Інсайт

```text
Data descriptor = повний контроль над атрибутом
```

---

## 🔁 Візуалізація

---

```mermaid
flowchart LR
    A["obj.attr"] --> B["Data Descriptor"]
    B --> C["call __get__"]
    C --> D["Result"]
```

---

# 🥈 2. instance.**dict**

👉 Якщо descriptor не знайдено:

```python
a.__dict__['x']
```

---

### 💡 Приклад

```python
class A:
    pass

a = A()
a.x = 10

print(a.x)  # → 10
```

---

### 🧠 Інсайт

```text
instance.__dict__ = реальний стан об’єкта
```

---

## 🔁 Візуалізація

```mermaid
flowchart LR
    A[obj.attr] --> B[instance.__dict__]
    B --> C[Return value]
```

---

# 🥉 3. Non-data Descriptor

👉 Має тільки `__get__`, без `__set__`

---

### 💡 Приклад

```python
class A:
    def method(self):
        return 42

a = A()
```

---

```python
print(a.method)  # bound method
```

---

### ⚠️ Можна перезаписати

```python
a.method = 100
print(a.method)  # → 100
```

---

### 🧠 Інсайт

```text
Non-data descriptor можна перекрити instance значенням
```

---

## 🔁 Візуалізація

```mermaid
flowchart LR
    A["obj.attr"] --> B["Non-data Descriptor"]
    B --> C["call __get__"]
    C --> D["Result"]
```

---


# 🏁 4. Class / MRO

👉 Якщо нічого не знайдено раніше:

```python
class A:
    x = 50

a = A()
print(a.x)
```

---

### 🧠 Інсайт

```text
class.__dict__ = fallback рівень
```

---

## 🔁 Візуалізація

```mermaid
flowchart LR
    A[obj.attr] --> B[class / MRO]
    B --> C[Return value]
```

---

# 💀 5. **getattr** (останній шанс)

```python
class A:
    def __getattr__(self, name):
        return "not found"
```

---

## 🔁 Візуалізація

```mermaid
flowchart LR
    A[AttributeError] --> B[__getattr__]
    B --> C[Return fallback]
```

---

# 🔥 Повна ієрархія (компактно)

```mermaid
flowchart TD
    A[obj.attr]

    A --> B1[1. Data Descriptor]
    B1 -->|yes| R1[__get__ → RETURN]

    B1 -->|no| B2[2. instance.__dict__]
    B2 -->|yes| R2[RETURN]

    B2 -->|no| B3[3. Non-data Descriptor]
    B3 -->|yes| R3[__get__ → RETURN]

    B3 -->|no| B4[4. class / MRO]
    B4 -->|yes| R4[RETURN]

    B4 -->|no| B5[5. __getattr__]
    B5 --> R5[RETURN or ERROR]
```

---

# 🧠 Супер-мнемоніка

```text
CONTROL → INSTANCE → FLEX → DEFAULT → FALLBACK
```

---

# 💣 Ключовий експеримент

```python
class A:
    @property
    def x(self):
        return 1

    def y(self):
        return 2

a = A()

a.__dict__['x'] = 999
a.__dict__['y'] = 999

print(a.x)  # → 1
print(a.y)  # → 999
```

---

# 🧠 Архітектурна модель

```mermaid
flowchart TD
    A[Access obj.attr]

    A --> B[Logic Layer]
    B -->|Data Descriptor| C[Validation / Control]

    A --> D[State Layer]
    D -->|instance dict| E[Stored Data]

    A --> F[Behavior Layer]
    F -->|Non-data descriptor| G[Methods]

    A --> H[Defaults]
    H -->|class dict| I[Static Values]

    A --> J[Fallback]
    J -->|__getattr__| K[Dynamic Handling]
```

---

```text
Python спочатку шукає логіку (descriptor), потім стан (instance), потім поведінку і лише в кінці дефолти
```

