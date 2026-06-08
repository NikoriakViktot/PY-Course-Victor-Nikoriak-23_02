# Task 3
# Додаток «Погода»
# Напишіть консольну програму, яка приймає в якості вхідних даних назву міста та
# повертає інформацію про поточну погоду у вибраному вами форматі. Для виконання цього
# завдання ви можете скористатися будь-яким API або вебсайтом з даними про погоду, а
# також вебсайтом openweathermap.org
import requests
def get_current_weather(city_name):
    # API КЛЮЧ
    api_key = "952cab2db13dc4cb65676acd88d3bd2e"
    # Базовий URL для запиту поточних погодних умов
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    # Формуємо параметри запиту:
    # q - назва міста, appid - токен, units=metric - градуси Цельсія, lang=uk - українська мова
    params = {
        "q": city_name,
        "appid": api_key,
        "units": "metric",
        "lang": "uk",
    }
    try:
        # Надсилаємо GET-запит до API
        response = requests.get(base_url, params=params, timeout=10)
        # Перевіряємо статус відповіді
        if response.status_code == 200:
            data = response.json()
            # Парсимо необхідні дані зі структури JSON
            city = data["name"]
            country = data["sys"]["country"]
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]
            description = data["weather"][0]["description"].capitalize()
            # Виводимо результат у гарному форматованому вигляді
            print(f"\n========================================")
            print(f" 🌍 Погода в місті: {city}, {country}")
            print(f"========================================")
            print(f" 📝 Стан:          {description}")
            print(f" 🌡️ Температура:   {temp}°C")
            print(f" 🤔 Відчувається як: {feels_like}°C")
            print(f" 💧 Вологість:       {humidity}%")
            print(f" 💨 Швидкість вітру: {wind_speed} м/с")
            print(f"========================================\n")
        elif response.status_code == 404:
            print(
                f"\n❌ Помилка: Місто '{city_name}' не знайдено. Перевірте правильність написання."
            )
        elif response.status_code == 401:
            print(
                "\n❌ Помилка авторизації: Ваш API-ключ недійсний або ще не активувався (активація зазвичай займає від 10 хв до кількох годин)."
            )
        else:
            print(
                f"\n❌ Щось пішло не так. Статус-код від сервера: {response.status_code}"
            )
    except requests.exceptions.RequestException as e:
        print(f"\n💥 Помилка мережі: Не вдалося з'єднатися з сервером. ({e})")
def main():
    print("--- Консольний додаток 'Погода' ---")
    while True:
        # Зчитуємо назву міста з консолі
        city_input = input(
            "Введіть назву міста (або 'вихід' для завершення): "
        ).strip()
        if city_input.lower() in ["вихід", "exit", "quit"]:
            print("Дякуємо за використання програми. Бувай!")
            break
        if not city_input:
            print("Назва міста не може бути порожньою. Спробуйте ще раз.")
            continue
        get_current_weather(city_input)
if __name__ == "__main__":
    main()