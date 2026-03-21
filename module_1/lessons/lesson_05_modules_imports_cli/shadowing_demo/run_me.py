"""
run_me.py — Демонстрація тіньового імпорту (import shadowing).

Запустіть з папки shadowing_demo/:
    python run_me.py

Показує два сценарії:
  1. Stdlib (random) — Python 3.10+ захищений від тіньового імпорту
  2. Власний модуль (myutils) — тіньовий імпорт досі можливий!
"""
import sys

print("=" * 55)
print(f"  Python {sys.version.split()[0]}")
print(f"  sys.path[0] = {sys.path[0]}")
print("=" * 55)

# ── Сценарій 1: спроба затінити стандартний random ──────────────
print("\n── Сценарій 1: тіньовий 'random.py' ──")
print("  У цій папці є random.py (без randint).")

import my_random
print(f"  Завантажено: {random.__file__}")

try:
    number = random.randint(1, 10)
    print(f"  random.randint(1,10) = {number}")
    print()
    print(f"  ✅ Python {sys.version_info.major}.{sys.version_info.minor} захищає stdlib від тіньового імпорту.")
    print("     Стандартна бібліотека завантажується навіть якщо")
    print("     у папці є файл з таким самим іменем.")
except AttributeError as e:
    print(f"  ❌ AttributeError: {e}")
    print(f"  Python {sys.version_info.major}.{sys.version_info.minor} не захищає stdlib.")
    print("  Перейменуйте random.py у цій папці.  (захист з'явився у Python 3.13)")

# ── Сценарій 2: тіньовий імпорт власного модуля ────────────────
print("\n── Сценарій 2: тіньовий 'myutils.py' (досі небезпечно!) ──")
print("  У цій папці є myutils.py — неповна версія без process().")

import myutils
print(f"  Завантажено: {myutils.__file__}")

try:
    result = myutils.process("hello")   # функції немає у тіньовому файлі
    print(f"  myutils.process('hello') = {result}")
except AttributeError as e:
    print(f"  ❌ AttributeError: {e}")
    print()
    print("  ПРИЧИНА: Python знайшов myutils.py у поточній папці")
    print("  (shadowing_demo/) і завантажив її замість повноцінної.")
    print()
    print("  Власні модулі Python 3.10 НЕ захищає!")
    print("  Якщо у sys.path є кілька папок з однойменними файлами —")
    print("  завантажиться той, що стоїть ПЕРШИМ.")
    print()
    print("  ВИПРАВЛЕННЯ: Слідкуйте за структурою проекту.")
    print("  Не дублюйте імена файлів у різних підпапках.")
