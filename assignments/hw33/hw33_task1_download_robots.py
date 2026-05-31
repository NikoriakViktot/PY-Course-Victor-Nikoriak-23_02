import requests

urls = {
    "wikipedia": "https://www.wikipedia.org/robots.txt",
    "twitter": "https://twitter.com/robots.txt"
}

for name, url in urls.items():
    response = requests.get(url)

    filename = f"{name}_robots.txt"

    with open(filename, "w", encoding="utf-8") as file:
        file.write(response.text)

    print(f"Saved {filename}")