import requests

city = input("Введіть назву міста (наприклад, Kyiv): ").strip()

if not city:
    print("Помилка: Назва міста не може бути порожньою!")
else:
    url = f"https://wttr.in/{city}?format=3"

    print(f"Отримуємо дані про погоду для міста {city}...")

    try:
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            print("\n☀️ Результат запиту:")
            print(response.text.strip())
        else:
            print(f"Не вдалося знайти місто '{city}' або сервер повернув помилку {response.status_code}.")

    except requests.exceptions.RequestException as e:
        print(f"Помилка з'єднання з сервером погоди: {e}")