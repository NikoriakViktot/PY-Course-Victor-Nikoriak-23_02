## Task 1: Завантаження `robots.txt`

Файл `robots.txt` містить правила для пошукових роботів (що можна індексувати на сайті, а що ні). Він завжди лежить у корені сайту.

Python

```
import requests

def download_robots_txt(url, filename):
    try:
        # Перевіряємо, чи URL правильно сформований (додаємо robots.txt у корінь)
        if not url.endswith('/robots.txt'):
            url = url.rstrip('/') + '/robots.txt'
            
        print(f"Завантаження з: {url}")
        # Робимо запит. Додаємо User-Agent, бо деякі сайти (як Twitter) блокують «голі» скрипти
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(response.text)
            print(f"Успішно збережено у файл: {filename}\n")
        else:
            print(f"Не вдалося завантажити. Статус код: {response.status_code}\n")
            
    except Exception as e:
        print(f"Сталася помилка: {e}\n")

# Тестуємо на Вікіпедії та Twitter
download_robots_txt('https://en.wikipedia.org', 'wikipedia_robots.txt')
download_robots_txt('https://twitter.com', 'twitter_robots.txt')
```

## Task 2: Завантаження коментарів з Reddit

Python

```
import requests
import json

def fetch_reddit_data(subreddit, filename):
    # Офіційне публічне посилання на сабреддіт у форматі JSON
    url = f"https://www.reddit.com/r/{subreddit}/comments.json?limit=50"
    headers = {'User-Agent': 'Mozilla/5.0 (MyCustomScript 1.0)'}
    
    print(f"Завантаження коментарів з r/{subreddit}...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Помилка запиту: {response.status_code}")
        return

    data = response.json()
    comments_list = []
    
    # Витягуємо коментарі з JSON структури Reddit
    for item in data['data']['children']:
        comment_data = item['data']
        
        # Створюємо чистий словник з потрібними полями
        clean_comment = {
            "id": comment_data.get("id"),
            "author": comment_data.get("author"),
            "body": comment_data.get("body", "[Порожній текст або це пост]"),
            "created_utc": comment_data.get("created_utc"), # Таймстамп для сортування
            "score": comment_data.get("score")
        }
        comments_list.append(clean_comment)
        
    # Сортуємо коментарі за хронологією (від найстаріших до найновіших)
    # Збільшення created_utc означає, що час іде вперед
    comments_list.sort(key=lambda x: x['created_utc'])
    
    # Зберігаємо у файл JSON
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(comments_list, f, indent=4, ensure_ascii=False)
        
    print(f"Збережено {len(comments_list)} коментарів у файл {filename} в хронологічному порядку!")

# Запуск (завантажимо коментарі з сабреддіту 'python')
fetch_reddit_data('python', 'reddit_comments.json')
```

## Task 3: Консольний додаток погоди

Для цього завдання найкраще підходить **OpenWeatherMap**.

1. Перейди на сайт [openweathermap.org](https://openweathermap.org/) та зареєструйся (це безкоштовно).
    
2. У профілі знайди вкладку **API keys** і згенеруй ключ.
    
3. Встав свій ключ у змінну `API_KEY` нижче.
    

Python

```
import requests

def get_weather(city_name):
    # Твій унікальний API ключ від OpenWeatherMap
    API_KEY = "ВСТАВ_СВІЙ_API_KEY_СЮДИ" 
    
    # URL для поточних погоди (Current Weather Data)
    # units=metric переводить температуру з Кельвінів у Цельсії
    # lang=uk вмикає опис погоди українською мовою
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={API_KEY}&units=metric&lang=uk"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            # Парсимо потрібні нам дані з JSON-відповіді
            city = data['name']
            country = data['sys']['country']
            temp = data['main']['temp']
            feels_like = data['main']['feels_like']
            humidity = data['main']['humidity']
            description = data['weather'][0]['description']
            wind_speed = data['wind']['speed']
            
            # Красиво виводимо в консоль
            print("\n" + "="*30)
            print(f"🌍 ПОГОДА В: {city}, {country}")
            print(="*30)
            print(f"Стан: {description.capitalize()}")
            print(f"Температура: {temp}°C (Відчувається як: {feels_like}°C)")
            print(f"Вологість: {humidity}%")
            print(f"Швидкість вітру: {wind_speed} м/с")
            print("="*30 + "\n")
            
        elif response.status_code == 404:
            print("❌ Помилка: Місто не знайдено. Перевірте правильність написання.")
        else:
            print(f"❌ Помилка API. Статус-код: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Щось пішло не так: {e}")

def main():
    print("--- Консольний додаток 'Погода' ---")
    while True:
        city = input("Введіть назву міста (або 'exit' для виходу): ").strip()
        if city.lower() == 'exit':
            print("Бувай! Гарної погоди!")
            break
        if city:
            get_weather(city)
        else:
            print("Назва міста не може бути порожньою.")

if __name__ == "__main__":
    main()
```