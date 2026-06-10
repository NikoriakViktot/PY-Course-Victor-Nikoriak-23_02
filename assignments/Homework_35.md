## Task 1: Primes (Thread vs Process)

Для перевірки великих чисел на простоту потрібні чисті обчислення (**CPU-bound** task). В Python через наявність **GIL (Global Interpreter Lock)** потоки (`ThreadPoolExecutor`) виконуються по черзі на одному ядрі, тоді як процеси (`ProcessPoolExecutor`) обходять GIL, створюючи окремі інстанси інтерпретатора на різних ядрах CPU.

Python

```
import math
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

NUMBERS = [
   2, 1099726899285419, 1570341764013157, 1637027521802551,
   1880450821379411, 1893530391196711, 2447109360961063, 3,
   2772290760589219, 3033700317376073, 4350190374376723,
   4350190491008389, 4350190491008390, 4350222956688319,
   2447120421950803, 5,
]

def is_prime(n: int) -> bool:
    """Утиліта для перевірки, чи є число простим."""
    if n < 2:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    # Оптимізований перебір до квадратного кореня (крок 6)
    for i in range(5, int(math.isqrt(n)) + 1, 6):
        if n % i == 0 or n % (i + 2) == 0:
            return False
    return True

def run_executor(executor_class, max_workers=None):
    start_time = time.perf_counter()
    with executor_class(max_workers=max_workers) as executor:
        # Використовуємо map для збереження порядку результатів
        results = list(executor.map(is_prime, NUMBERS))
    end_time = time.perf_counter()
    return results, end_time - start_time

if __name__ == '__main__':
    print("--- Порівняння продуктивності ---")
    
    # Тест ThreadPoolExecutor
    thread_res, thread_time = run_executor(ThreadPoolExecutor)
    print(f"ThreadPoolExecutor: {thread_time:.4f} секунд")
    
    # Тест ProcessPoolExecutor
    process_res, process_time = run_executor(ProcessPoolExecutor)
    print(f"ProcessPoolExecutor: {process_time:.4f} секунд")
    
    # Перевірка правильності фільтрації
    primes = [num for num, is_p in zip(NUMBERS, process_res) if is_p]
    print(f"\nЗнайдені прості числа ({len(primes)} шт): {primes}")
```

### Порівняння результатів:

- **`ProcessPoolExecutor`** покаже значно кращий результат (швидше у кілька разів, залежно від кількості ядер твого процесора). Оскільки задача CPU-bound, розподіл чисел між ядрами дає чистий приріст швидкості.
    
- **`ThreadPoolExecutor`** працюватиме приблизно так само (або навіть трохи повільніше), як звичайний послідовний цикл `for`, через те що потоки постійно блокуються GIL і змагаються за одне ядро.
    

## Task 2: Requests за допомогою concurrent та multiprocessing

> ⚠️ **Важлива примітка щодо API:** Оригінальний Pushshift API (`api.pushshift.io`) вже тривалий час не працює в публічному режимі без спеціальних токенів модератора. Крім того, офіційний Reddit API вимагає OAuth-авторизації.
> 
> Для того, щоб код точно запустився без реєстрації додаткових ключів, у прикладі нижче використано відкритий ендпоінт **JSON-пагінації самого Reddit** (додавання `.json` до URL сабреддіту). Оскільки це задача **I/O-bound** (очікування відповіді від мережі), тут ми використовуємо `threading` (через `concurrent.futures`) та стандартний `multiprocessing`.

Python

```
import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp

# Використовуємо відкритий URL для демонстрації пагінації (сортування за новизною)
# Зробимо 5 запитів, отримуючи "хвости" (after) для імітації збору великої бази
URLS = [
    "https://www.reddit.com/r/python/new.json?limit=25",
    "https://www.reddit.com/r/python/new.json?limit=25&after=t3_1", 
    "https://www.reddit.com/r/python/new.json?limit=25&after=t3_2",
    "https://www.reddit.com/r/python/new.json?limit=25&after=t3_3",
    "https://www.reddit.com/r/python/new.json?limit=25&after=t3_4"
]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def fetch_comments(url):
    """Скачує дані та витягує коментарі/пости."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            items = []
            # Парсимо стандартну структуру відповіді Reddit Reddit
            for child in data.get('data', {}).get('children', []):
                item_data = child.get('data', {})
                items.append({
                    "id": item_data.get("id"),
                    "created_utc": item_data.get("created_utc"),
                    "author": item_data.get("author"),
                    "title_or_body": item_data.get("title") or item_data.get("body")
                })
            return items
    except Exception as e:
        print(f"Помилка при запиті {url}: {e}")
    return []

if __name__ == '__main__':
    # --- 1. Concurrent Implementation (Threads для I/O) ---
    print("Запуск через ThreadPoolExecutor...")
    start = time.perf_counter()
    all_data = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(fetch_comments, URLS)
        for res in results:
            all_data.extend(res)
            
    print(f"Зібрано {len(all_data)} елементів за {time.perf_counter() - start:.2f} сек.")

    # --- 2. Multiprocessing Implementation ---
    print("\nЗапуск через multiprocessing.Pool...")
    start = time.perf_counter()
    
    with mp.Pool(processes=mp.cpu_count()) as pool:
        mp_results = pool.map(fetch_comments, URLS)
    
    all_data_mp = []
    for res in mp_results:
        all_data_mp.extend(res)
        
    print(f"Зібрано {len(all_data_mp)} елементів за {time.perf_counter() - start:.2f} сек.")

    # --- 3. Сортування в хронологічному порядку та збереження ---
    # Фільтруємо None на випадок помилок мережі та сортуємо за таймстемпом
    valid_data = [item for item in all_data if item.get('created_utc') is not None]
    sorted_data = sorted(valid_data, key=lambda x: x['created_utc'])

    output_file = "reddit_comments.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(sorted_data, f, ensure_ascii=False, indent=4)
        
    print(f"\nДані успішно відсортовано та збережено у файл '{output_file}'")
```

> **Висновок по Task 2:** Для мережевих запитів (`I/O-bound`) потоки (`ThreadPoolExecutor`) часто працюють вигідніше, оскільки вони «легші» за процеси і не витрачають ресурси ОС на копіювання пам'яті інтерпретатора.

## Task 3: Echo server з multiprocessing

Для того, щоб сервер міг одночасно обробляти підключення від багатьох клієнтів і при цьому не блокував головний цикл прийняття нових з'єднань (`accept`), ми будемо форкати (створювати) новий `multiprocessing.Process` на кожного клієнта.

Python

```
import socket
import sys
import multiprocessing as mp

HOST = '127.0.0.1'
PORT = 65432

def handle_client(conn, addr):
    """Функція виконується в окремому процесі для кожного клієнта."""
    print(f"[НОВЕ ПІДКЛЮЧЕННЯ] Клієнт {addr} обслуговується процесом {mp.current_process().pid}")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                # Клієнт закрив з'єднання
                break
            print(f"[{addr}]: {data.decode('utf-8').strip()}")
            # Відправляємо луну (echo) назад
            conn.sendall(data)
    except ConnectionResetError:
        print(f"[ЗБІЙ] Клієнт {addr} раптово розірвав з'єднання.")
    finally:
        conn.close()
        print(f"[ВІДКЛЮЧЕНО] З'єднання з {addr} закрито.")

def start_server():
    # Створюємо TCP сокет
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Дозволяємо повторне використання адреси (щоб уникнути OSError: [Errno 98] Address already in use)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"[ЗАПУСК] Ехо-сервер працює на {HOST}:{PORT}")
        
        while True:
            # Приймаємо нове з'єднання (блокуючий виклик)
            conn, addr = server_socket.accept()
            
            # Створюємо окремий процес для обробки клієнта
            p = mp.Process(target=handle_client, args=(conn, addr))
            # Робимо процес демоном, щоб він закривався при зупинці головного сервера
            p.daemon = True 
            p.start()
            
            # Важливо закрити копію дескриптора сокета в головному процесі,
            # оскільки процес-нащадок скопіював його собі.
            conn.close()
            
    except KeyboardInterrupt:
        print("\n[ЗУПИНКА] Сервер зупиняє роботу...")
    finally:
        server_socket.close()

if __name__ == '__main__':
    start_server()
```