# Task 1
# Robots.txt
# Завантажте та збережіть у файл robots.txt з веб-сайтів Вікіпедії, Twitter тощо.
import requests
def download_robots_txt(url, save_filename):
    """Завантажує файл robots.txt за вказаним URL та зберігає його локально."""
    # Імітуємо реальний браузер за допомогою заголовка User-Agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        print(f"Запитуємо файл з: {url}...")
        response = requests.get(url, headers=headers, timeout=10)
        # Перевіряємо, чи успішний статус-код (200 OK)
        if response.status_code == 200:
            # Зберігаємо вміст відповіді (текст) у файл
            with open(save_filename, "w", encoding="utf-8") as file:
                file.write(response.text)
            print(f"✅ Успішно збережено: {save_filename}\n")
        else:
            print(
                f"❌ Не вдалося завантажити. Статус-код від сервера: {response.status_code}\n"
            )
    except requests.exceptions.RequestException as e:
        print(f"💥 Сталася помилка мережі: {e}\n")
# Використання функції для Wikipedia та Twitter (X)
if __name__ == "__main__":
    # 1. Завантаження з Wikipedia
    wiki_url = "https://wikipedia.org"
    download_robots_txt(wiki_url, "wikipedia_robots.txt")
    # 2. Завантаження з Twitter (X)
    twitter_url = "https://x.com"
    download_robots_txt(twitter_url, "twitter_robots.txt")

