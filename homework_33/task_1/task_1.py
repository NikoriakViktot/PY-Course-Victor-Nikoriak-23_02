import requests


url = 'https://www.wikipedia.org/robots.txt'
response = requests.get(url)

with open('robots.txt', 'w', encoding ='utf-8') as f:
    f.write(response.text)