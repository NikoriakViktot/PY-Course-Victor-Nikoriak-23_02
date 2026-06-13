import requests

print("=== Консольний додаток погоди ===")

# Запитуємо назву міста у користувача
city = input("Введіть назву міста (бажано англійською, наприклад: Kyiv, London): ").strip()

if not city:
    print("Помилка: Назва міста не може бути порожньою.")
else:
    # wttr.in повертає погоду в текстовому форматі.
    # Параметр ?format=3 повертає компактний рядок: "City: ⛅️ +12°C ↙️ 14km/h"
    # Якщо хочеш повну таблицю з графікою, просто прибери "?format=3" з URL.
    url = f"https://wttr.in/{city}?format=3"

    # Налаштовуємо мову відповіді (українська) через заголовки
    headers = {
        "Accept-Language": "uk"
    }

    print(f"\nОтримання погоди для міста '{city}'...")

    try:
        # Виконуємо HTTP GET-запит
        response = requests.get(url, headers=headers, timeout=10)

        # Перевіряємо, чи запит успішний
        if response.status_code == 200:
            print("\nПоточна погода:")
            print(response.text.strip())
        elif response.status_code == 404:
            print("Помилка: Місто не знайдено. Перевірте правильність написання.")
        else:
            print(f"Помилка сервера. Статус-код: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"Помилка підключення до сервера погоди: {e}")
