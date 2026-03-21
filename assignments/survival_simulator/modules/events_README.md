# 🧩 TEAM 4 — events.py

## 📖 Що робить цей модуль

Цей модуль симулює **випадкову подію** яка трапляється з гравцем протягом дня.

Іноді нічого не відбувається, іноді гравець отримує травму, а іноді — знаходить щось корисне.

---

## ⚙️ Що потрібно зробити

1. Створити список можливих подій: `["Nothing", "Injury", "Bonus"]`.
2. Випадково обрати одну за допомогою `random.choice()`.
3. Застосувати ефект:
   - `"Nothing"` → нічого не змінювати
   - `"Injury"` → відняти **10** від `state["health"]`
   - `"Bonus"` → додати **10** до `state["energy"]`
4. Надрукувати яка подія відбулась.
5. Повернути оновлений `state`.

---

## 🧠 Які знання використовуються

- `import random`
- `random.choice(list)` — обирає випадковий елемент зі списку
- `if / elif / else`
- `dict` — `state["health"]` і `state["energy"]` — цілі числа

---

## 🔗 Як цей модуль впливає на інші

👉 **Injury** зменшує `health` на 10 →
якщо `health.py` теж знімає HP (через відсутність їжі) →
за один день можна втратити **20 HP** одразу.

👉 **Bonus** дає +10 до `energy` →
це може врятувати від GAME OVER якщо після шторму залишилось мало сил.

👉 **Injury** кілька разів поспіль →
`health` може впасти до 0 → `"You died..."` → кінець гри.

---

## 📊 Приклади

**Приклад A — Injury:**

```python
state = {"health": 100, "energy": 90, "food": 5}
# event = "Injury" → health - 10
state["health"] = 90
print("Event: Injury")
```
```
Event: Injury
```

**Приклад B — Bonus:**

```python
state = {"health": 100, "energy": 90, "food": 5}
# event = "Bonus" → energy + 10
state["energy"] = 100
print("Event: Bonus")
```
```
Event: Bonus
```

**Приклад C — Nothing:**

```python
# нічого не змінюється
print("Event: Nothing")
```
```
Event: Nothing
```

---

## ❗ Важливо

- Не змінювати інші модулі — тільки свій файл `events.py`
- `"Injury"` змінює тільки `state["health"]`
- `"Bonus"` змінює тільки `state["energy"]`
- `"Nothing"` — жодних змін
- Обов'язково `return state` в кінці функції
- Назва функції залишається: `def run(state: dict) -> dict:`
