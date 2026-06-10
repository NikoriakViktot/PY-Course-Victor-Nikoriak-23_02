"""
╔══════════════════════════════════════════════════════╗
║  TEAM 2 — weather.py                                ║
╚══════════════════════════════════════════════════════╝

ЩО РОБИТЬ ЦЕЙ МОДУЛЬ:
  Визначає погоду сьогоднішнього дня і змінює енергію гравця.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ЗАВДАННЯ (виконуй по порядку):

  1. Створи список з трьох варіантів погоди:
        ["Sunny", "Rainy", "Storm"]

  2. Випадково обери один варіант.
     Використай: random.choice(список)

  3. Застосуй ефект до state["energy"]:
        Sunny  →  +10 до energy
        Rainy  →  без змін
        Storm  →  -15 до energy

  4. Виведи повідомлення у форматі:
        Weather: Sunny

  5. Поверни state.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ПРИКЛАД:

  До виклику:   state["energy"] = 30
  Обрано:       Storm
  Після:        state["energy"] = 15
  Вивід:        Weather: Storm

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ВАЖЛИВО:

  ✅ Змінюй тільки state["energy"]
  ✅ Не чіпай state["health"] і state["food"]
  ✅ Обов'язково: return state

⚠️  Якщо energy <= 0 після твого модуля — гра закінчується!
    Починаємо з energy = 30, Storm забирає 15 — будь обережний.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GIT:

  Гілка:        team2/weather
  Коміт:        feat: implement weather module
  Потім:        відкрий Pull Request до main
"""

import random


def run(state: dict) -> dict:
    weather_option = ["Sunny", "Rainy", "Storm"]
    current_weather = random.choice(weather_option)
    if current_weather == "Sunny":
        state['energy'] += 10
    elif current_weather == "Rainy":
        pass
    elif current_weather == "Storm":
        state['energy'] -= 15

    print(f'weather: {current_weather}')

    return state

