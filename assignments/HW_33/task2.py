import json
import requests

url = "https://jsonplaceholder.typicode.com/comments"

print("Надсилаємо запит до API та завантажуємо коментарі...")
response = requests.get(url)

if response.status_code == 200:
    comments = response.json()
    print(f"Успішно завантажено {len(comments)} коментарів.")
    comments_sorted = sorted(comments, key=lambda x: x['id'])
    with open("reddit_comments.json", "w", encoding="utf-8") as file:
        json.dump(comments_sorted, file, ensure_ascii=False, indent=4)
    print("Дані успішно відсортовані та збережені у файл 'reddit_comments.json'!")
else:
    print(f"Помилка завантаження даних! Статус-код сервера: {response.status_code}")