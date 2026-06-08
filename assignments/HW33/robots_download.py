import requests

urls = [
    "https://www.wikipedia.org/robots.txt",
    "https://twitter.com/robots.txt"
]

headers = {
    "User-Agent": "Mozilla/5.0"
}

for url in urls:
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            domain = url.split("//")[1].split("/")[0]
            filename = f"{domain}_robots.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"✅ Збережено: {filename}")
        else:
            print(f"⚠️ Не вдалося отримати {url}, код: {response.status_code}")
    except Exception as e:
        print(f"❌ Помилка при доступі до {url}: {e}")

