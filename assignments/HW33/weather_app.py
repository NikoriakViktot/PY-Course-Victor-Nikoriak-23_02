import requests
from datetime import datetime

API_KEY = "81fa787e7fa88623a2bc5919f2849f16"  # твій новий ключ
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# словник транслітерацій для основних міст України
cities = {
    "Київ": "Kyiv",
    "Полтава": "Poltava",
    "Львів": "Lviv",
    "Харків": "Kharkiv",
    "Одеса": "Odesa",
    "Дніпро": "Dnipro",
    "Запоріжжя": "Zaporizhzhia",
    "Чернігів": "Chernihiv",
    "Черкаси": "Cherkasy",
    "Суми": "Sumy",
    "Вінниця": "Vinnytsia",
    "Івано-Франківськ": "Ivano-Frankivsk",
    "Тернопіль": "Ternopil",
    "Ужгород": "Uzhhorod",
    "Херсон": "Kherson",
    "Миколаїв": "Mykolaiv",
    "Кропивницький": "Kropyvnytskyi",
    "Рівне": "Rivne",
    "Житомир": "Zhytomyr",
    "Луцьк": "Lutsk"
}

while True:
    city_input = input("Введіть назву міста (або 'вихід' для завершення): ")
    if city_input.lower() == "вихід":
        break

    city = cities.get(city_input, city_input)

    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "ua"
    }

    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]
        weather = data["weather"][0]["description"]

        # додаємо дату
        today = datetime.now().strftime("%d.%m.%Y %H:%M")

        print("\n==============================")
        print(f"📅 Дата: {today}")
        print(f"🌤 Погода у {city_input}: {weather}")
        print(f"🌡 Температура: {temp}°C (відчувається як {feels_like}°C)")
        print(f"💧 Вологість: {humidity}%")
        print(f"🌬 Вітер: {wind} м/с")
        print("==============================\n")
        print("➡️ Введіть наступне місто або 'вихід' для завершення.\n")

    else:
        print("⚠️ Не вдалося отримати дані. Перевірте назву міста або ключ API.\n")
