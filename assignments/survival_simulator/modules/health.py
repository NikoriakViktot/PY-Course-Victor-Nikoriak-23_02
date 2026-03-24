"""
╔══════════════════════════════════════════════════════╗
║  TEAM 3 — health.py                                 ║
╚══════════════════════════════════════════════════════╝

ЩО РОБИТЬ ЦЕЙ МОДУЛЬ:
  Перевіряє чи гравець поїв сьогодні і змінює його здоров'я.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ЗАВДАННЯ (виконуй по порядку):

  1. Перевір значення state["food"].

  2. Якщо food == 0  (гравець не знайшов їжу):
        Відніми 10 від state["health"]
        Виведи:  Health change: -10

  3. Якщо food > 0  (гравець поїв):
        Додай 5 до state["health"]
        Виведи:  Health change: +5

  4. Поверни state.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ПРИКЛАДИ:

  Приклад A — немає їжі:
    До:     state = {"health": 55, "energy": 30, "food": 0}
    Після:  state["health"] = 45
    Вивід:  Health change: -10

  Приклад B — є їжа:
    До:     state = {"health": 55, "energy": 30, "food": 7}
    Після:  state["health"] = 60
    Вивід:  Health change: +5

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ВАЖЛИВО:

  ✅ Змінюй тільки state["health"]
  ✅ state["food"] тільки читай — не змінюй його тут
  ✅ Не чіпай state["energy"]
  ✅ Обов'язково: return state

⚠️  Починаємо з health = 55. Якщо health <= 0 — гравець помирає!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GIT:

  Гілка:        team3/health
  Коміт:        feat: implement health module
  Потім:        відкрий Pull Request до main
"""


def run(state: dict) -> dict:
    if state['food'] == 0:
        state['health'] -= 10
        print('Health change: -10')

    else:
        state['health'] += 5
        print('Health change: +5')


    return state


def run1(state: dict) -> dict:
    if not state['food']:
        state['health'] -= 10
        print('Health change: -10')
        return state


    state['health'] += 5
    print('Health change: +5')


    return state