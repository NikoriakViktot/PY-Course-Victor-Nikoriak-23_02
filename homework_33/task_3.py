import requests


API_KEY = 'f0bb56f38e1b242bd89dea7e0a02b192'
city = input('Введи місто: ')

url = 'https://api.openweathermap.org/data/2.5/weather'

params = {
    'q': city,
    'appid': API_KEY,
    'units': 'metric'
}

response = requests.get(url, params = params)
data = response.json()

if response.status_code != 200:
    print('Помилка:', data.get('message'))
    exit()

temp = data['main']['temp']
description = data['weather'][0]['description']


print(f'Місто: {city}')
print(f'Температура: {temp}°C')
print(f'Погода: {description}')