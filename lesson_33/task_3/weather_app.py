import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


def get_weather(city):
    encoded_city = quote(city)
    url = f"https://wttr.in/{encoded_city}?format=j1"

    request = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
    )

    with urlopen(request, timeout=10) as response:
        response_data = response.read().decode("utf-8", errors="ignore")

    data = json.loads(response_data)
    current_weather = data["current_condition"][0]

    return {
        "city": city,
        "temperature": current_weather["temp_C"],
        "feels_like": current_weather["FeelsLikeC"],
        "description": current_weather["weatherDesc"][0]["value"],
        "humidity": current_weather["humidity"],
        "wind_speed": current_weather["windspeedKmph"],
    }


def print_weather(weather):
    print(f"City: {weather['city']}")
    print(f"Temperature: {weather['temperature']}°C")
    print(f"Feels like: {weather['feels_like']}°C")
    print(f"Weather: {weather['description']}")
    print(f"Humidity: {weather['humidity']}%")
    print(f"Wind speed: {weather['wind_speed']} km/h")


def main():
    city = input("Enter city name: ").strip()

    try:
        weather = get_weather(city)
        print_weather(weather)
    except HTTPError as error:
        print(f"HTTP error: {error}")
    except URLError as error:
        print(f"URL error: {error}")
    except TimeoutError:
        print("Request timeout")
    except (KeyError, IndexError, json.JSONDecodeError):
        print("Could not get weather for this city")


if __name__ == "__main__":
    main()
