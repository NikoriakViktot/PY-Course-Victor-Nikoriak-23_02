import requests

url = "https://en.wikipedia.org/robots.txt"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
print(f"Надсилаємо запит до {url}...")

response = requests.get(url, headers=headers)

if response.status_code == 200:
    with open("wikipedia_robots.txt", "w", encoding="utf-8") as file:
        file.write(response.text)
    print("Файл успішно збережено як 'wikipedia_robots.txt'!")
else:
    print(f"Помилка завантаження! Статус код: {response.status_code}")