import urllib.request
import urllib.error

# Список сайтів для завантаження robots.txt
urls = {
    "wikipedia": "https://wikipedia.org",
    "twitter": "https://twitter.com",
    "google": "https://google.com"
}

# Налаштовуємо User-Agent, оскільки деякі сайти (наприклад, Twitter)
# блокують стандартні запити від роботів Python (повертають помилку 403)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

for name, url in urls.items():
    print(f"Завантаження {url}...")

    try:
        # Створюємо об'єкт запиту з користувацьким User-Agent
        req = urllib.request.Request(url, headers=headers)

        # Виконуємо HTTP-запит
        with urllib.request.urlopen(req) as response:
            # Читаємо бінарні дані та декодуємо їх у текст
            robots_content = response.read().decode('utf-8')

            # Назва файлу для збереження (наприклад, wikipedia_robots.txt)
            filename = f"{name}_robots.txt"

            # Записуємо отриманий текст у файл
            with open(filename, "w", encoding="utf-8") as file:
                file.write(robots_content)

            print(f"Збережено успішно як: {filename}\n")

    except urllib.error.HTTPError as e:
        print(f"Помилка HTTP для {name}: {e.code} {e.reason}\n")
    except urllib.error.URLError as e:
        print(f"Помилка з'єднання для {name}: {e.reason}\n")
    except Exception as e:
        print(f"Сталася непередбачувана помилка для {name}: {e}\n")
