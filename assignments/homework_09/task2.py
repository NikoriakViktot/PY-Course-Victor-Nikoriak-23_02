import sys

# 1. Початковий sys.path

print("--- Початковий sys.path ---")
for path in sys.path:
    print(path)

# 2. Оновлений sys.path

new_path = "/Users/alla/my_python_modules"
sys.path.append(new_path)

print("\n--- Оновлений sys.path ---")
if new_path in sys.path:
    print(f"Успішно додано: {sys.path[-1]}")

# 3. Відповідь на питання завдання:
# Чи впливає це на пошук? Так. Якщо ми додамо шлях до папки,
# Python почне шукати модулі і в ній також.