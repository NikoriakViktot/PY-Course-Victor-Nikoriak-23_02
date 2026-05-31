import requests

API_KEY = "YOUR_API_KEY"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

def get_weather(city):
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    response = requests.get(BASE_URL, params=params)
    data = response.json()

    if response.status_code != 200:
        return f"Error: {data.get('message', 'Unknown error')}"

    weather = data["weather"][0]["description"]
    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    humidity = data["main"]["humidity"]

    return (
        f"City: {city}\n"
        f"Weather: {weather}\n"
        f"Temperature: {temp}°C\n"
        f"Feels like: {feels_like}°C\n"
        f"Humidity: {humidity}%"
    )


if __name__ == "__main__":
    city = input("Enter city name: ")
    print(get_weather(city))