"""
╔══════════════════════════════════════════════════════╗
║  TEAM 4 — events.py                                 ║
╚══════════════════════════════════════════════════════╝

ЩО РОБИТЬ ЦЕЙ МОДУЛЬ:
  Визначає випадкову подію дня і застосовує її наслідки.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ЗАВДАННЯ (виконуй по порядку):

  1. Створи список з трьох можливих подій:
        ["Nothing", "Injury", "Bonus"]

  2. Випадково обери одну.
     Використай: random.choice(список)

  3. Застосуй ефект:
        Nothing  →  нічого не змінюється
        Injury   →  -10 до state["health"]
        Bonus    →  +10 до state["energy"]

  4. Виведи повідомлення у форматі:
        Event: Injury

  5. Поверни state.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ПРИКЛАДИ:

  Приклад A — Injury:
    До:     state["health"] = 55
    Після:  state["health"] = 45
    Вивід:  Event: Injury

  Приклад B — Bonus:
    До:     state["energy"] = 30
    Після:  state["energy"] = 40
    Вивід:  Event: Bonus

  Приклад C — Nothing:
    Жодних змін.
    Вивід:  Event: Nothing

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ВАЖЛИВО:

  ✅ Injury  — змінюй тільки state["health"]
  ✅ Bonus   — змінюй тільки state["energy"]
  ✅ Nothing — нічого не змінюй
  ✅ Обов'язково: return state

⚠️  Починаємо з health = 55 і energy = 30.
    Injury може наблизити кінець гри — особливо в поєднанні з Team 3!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GIT:

  Гілка:        team4/events
  Коміт:        feat: implement events module
  Потім:        відкрий Pull Request до main
"""

import random


def run(state: dict) -> dict:
    # Пиши свій код тут
    events = ["Nothing", "Injury", "Bonus"]
    event = random.choice(events)
    if event == "Injury":
        state["health"] -= 10
    elif event == "Bonus":
        state["energy"] += 10
    elif event == "Nothing":
        pass  # ничего не происходит
    print(f"Event: {event}")
    return state
