## Task 1: A shared counter

Python

```
import threading

# Глобальні змінні за умовою задачі
counter = 0
rounds = 100_000

class Counter(threading.Thread):
    def run(self):
        global counter
        for _ in range(rounds):
            # Операція counter += 1 не є атомарною!
            counter += 1

if __name__ == "__main__":
    # Створюємо 2 екземпляри потоку
    t1 = Counter()
    t2 = Counter()

    # Запускаємо потоки
    t1.start()
    t2.start()

    # Чекаємо на завершення обох потоків
    t1.join()
    t2.join()

    print(f"Фінальне значення counter: {counter}")
```

### Чому результат НЕ 200,000?

Якщо ти запустиш цей код кілька разів, ти побачиш цифри на кшталт `142384`, `118932` тощо. Чому так відбувається?

1. **Неатомарність операції:** Вираз `counter += 1` здається однією дією, але для процесора це три окремі кроки:
    
    - Зчитати поточне значення змінного `counter`.
        
    - Збільшити його на 1 у пам'яті потоку.
        
    - Записати нове значення назад у `counter`.
        
2. **Перемикання контексту (Context Switch):** Операційна система (або інтерпретатор Python) може перервати Потік 1 прямо посередині цих трьох кроків. Потік 2 зчитує те саме (старе) значення, теж збільшує його на 1 і записує. В результаті один з інкрементів просто «губиться».
    

## Task 2: Echo server with threading

Для створення ехо-сервера використаємо модуль `socket`. Кожне нове підключення клієнта ми будемо передавати в окремий потік, щоб сервер не блокувався і міг обслуговувати багатьох користувачів одночасно.

### Код сервера (`server.py`)

Python

```
import socket
import threading

def handle_client(client_socket, client_address):
    print(f"[NEW CONNECTION] Клієнт {client_address} підключився.")
    try:
        while True:
            # Отримуємо дані від клієнта (до 1024 байт)
            data = client_socket.recv(1024)
            if not data:
                # Клієнт закрив з'єднання
                break
            
            print(f"[{client_address}] Отримано: {data.decode('utf-8').strip()}")
            # Відправляємо дані назад (Echo)
            client_socket.sendall(data)
    except ConnectionResetError:
        print(f"[DISCONNECT] З'єднання з {client_address} було розірвано.")
    finally:
        client_socket.close()
        print(f"[CONNECTION CLOSED] З'єднання з {client_address} закрито.")

def start_server():
    host = '127.0.0.1'
    port = 55555

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Дозволяємо повторно використовувати порт відразу після перезапуску
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen()
    print(f"[STARTING] Сервер запущено на {host}:{port}")

    try:
        while True:
            # Очікуємо на нове підключення (це блокуюча операція)
            client_socket, client_address = server.accept()
            
            # Створюємо новий потік для обробки цього конкретного клієнта
            thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            # Робимо потік демоном, щоб він закривався при зупинці основного сервера
            thread.daemon = True 
            thread.start()
            
            print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
    except KeyboardInterrupt:
        print("\n[STOPPING] Сервер зупиняється...")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()
```

_Для перевірки можеш запустити цей скрипт, а в іншому терміналі підключитися за допомогою утиліти `telnet 127.0.0.1 55555` або `nc 127.0.0.1 55555`._

## Task 3: Requests using multithreading

Оскільки операції введення-виведення (I/O-bound), такі як HTTP-запити, змушують потік чекати на відповідь від сервера, використання потоків (Threads) тут дасть **величезний приріст швидкості**, бо поки один потік чекає відповіді, інший уже робить наступний запит.

### Код рішення

Python

```
import json
import threading
import time
import requests

# Список для збору результатів з усіх потоків
all_comments = []
# Lock (замок) потрібен для безпечного запису в спільний список all_comments
data_lock = threading.Lock()

def fetch_comments(subreddit, limit=50, before_timestamp=None):
    """Функція для одного потоку, що робить запит до API"""
    global all_comments
    
    # Використовуємо офіційний публічний JSON ендпоінт Reddit для демонстрації,
    # оскільки Pushshift часто офлайн.
    url = f"https://www.reddit.com/r/{subreddit}/comments.json?limit={limit}"
    if before_timestamp:
        url += f"&before={before_timestamp}"
        
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Витягуємо коментарі з JSON-структури Reddit
            children = data.get('data', {}).get('children', [])
            
            local_comments = []
            for item in children:
                comment_data = item.get('data', {})
                local_comments.append({
                    'id': comment_data.get('id'),
                    'author': comment_data.get('author'),
                    'body': comment_data.get('body'),
                    'created_utc': comment_data.get('created_utc')  # Timestamp для сортування
                })
            
            # Безпечно додаємо зібрані коментарі до загального списку
            with data_lock:
                all_comments.extend(local_comments)
                print(f"[УСПІХ] Потік завантажив {len(local_comments)} коментарів.")
        else:
            print(f"[ПОМИЛКА] Статус коду: {response.status_code}")
    except Exception as e:
        print(f"[ВИНЯТОК] Помилка під час запиту: {e}")

if __name__ == "__main__":
    target_subreddit = "python"  # Сабреддіт на вибір
    threads = []
    
    # Створимо 3 потоки, які нібито роблять запити на різні сторінки/пагінацію
    # (для демонстрації передамо різні параметри, хоча в реальному Pushshift ми б передавали різні часові проміжки)
    print("Запуск потоків для завантаження даних...")
    for i in range(3):
        # Створюємо потік
        t = threading.Thread(target=fetch_comments, args=(target_subreddit, 25))
        threads.append(t)
        t.start()
        # Маленька пауза, щоб не отримати бан за rate-limit від Reddit
        time.sleep(0.5)

    # Чекаємо, поки всі потоки завершать роботу
    for t in threads:
        t.join()

    print(f"Всього завантажено коментарів: {len(all_comments)}")

    # Сортування в хронологічному порядку (від найстаріших до найновіших) за ключем 'created_utc'
    # Якщо якихось значень немає, використовуємо 0 як дефолт
    all_comments.sort(key=lambda x: x.get('created_utc', 0))

    # Зберігаємо результат у JSON файл
    output_filename = "reddit_comments.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(all_comments, f, ensure_ascii=False, indent=4)
        
    print(f"Дані успішно збережено у файл {output_filename}")
```