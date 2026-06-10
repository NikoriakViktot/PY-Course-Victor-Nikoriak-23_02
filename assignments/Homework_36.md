## Task 1: Asyncio vs Multiprocessing (Fibonacci, Factorial, etc.)

### Реалізація 1: `asyncio`

Оскільки стандартні математичні обчислення в Python є синхронними та блокуючими, просто додавання `async/await` не зробить їх паралельними. Вони все одно виконуватимуться послідовно в одному потоці.

Python

```
import asyncio
import time

# Обчислювальні функції
def fibonacci(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def factorial(n):
    res = 1
    for i in range(2, n + 1):
        res *= i
    return res

def square(n):
    return n ** 2

def cubic(n):
    return n ** 3

# Асинхронні обгортки
async def async_fib(n): return fibonacci(n)
async def async_fact(n): return factorial(n)
async def async_sq(n): return square(n)
async def async_cube(n): return cubic(n)

async def run_asyncio(numbers):
    # Створюємо завдання для кожного числа
    fib_tasks = [async_fib(n) for n in numbers]
    fact_tasks = [async_fact(n) for n in numbers]
    sq_tasks = [async_sq(n) for n in numbers]
    cube_tasks = [async_cube(n) for n in numbers]
    
    # Збираємо результати (всього 4 списки результатів)
    results = await asyncio.gather(
        asyncio.gather(*fib_tasks),
        asyncio.gather(*fact_tasks),
        asyncio.gather(*sq_tasks),
        asyncio.gather(*cube_tasks)
    )
    return results

if __name__ == "__main__":
    numbers = list(range(1, 11))
    
    start = time.perf_counter()
    fibs, facts, squares, cubes = asyncio.run(run_asyncio(numbers))
    end = time.perf_counter()
    
    print(f"[Asyncio] Час виконання: {end - start:.6f} сек")
```

### Реалізація 2: `multiprocessing`

Тут ми використовуємо пул процесів (`Pool`), щоб обійти GIL та задіяти кілька ядер процесора.

Python

```
from multiprocessing import Pool
import time
# Імпортуємо функції з попереднього прикладу або перевизначаємо їх тут

def run_multiprocessing(numbers):
    with Pool() as pool:
        # Обчислюємо кожен тип завдань паралельно
        fibs = pool.map(fibonacci, numbers)
        facts = pool.map(factorial, numbers)
        squares = pool.map(square, numbers)
        cubes = pool.map(cubic, numbers)
    return fibs, facts, squares, cubes

if __name__ == "__main__":
    numbers = list(range(1, 11))
    
    start = time.perf_counter()
    fibs, facts, squares, cubes = run_multiprocessing(numbers)
    end = time.perf_counter()
    
    print(f"[Multiprocessing] Час виконання: {end - start:.6f} сек")
```

## Task 2: Requests за допомогою asyncio та aiohttp


Зсув за часом (хронологію) зазвичай реалізують через пагінацію параметром `before` або `after` (Unix timestamp).

Python

```
import asyncio
import aiohttp
import json
import time

URL = "https://api.pushshift.io/reddit/comment/search/"
SUBREDDIT = "python"

async def fetch_comments(session, subreddit, before_timestamp):
    params = {
        'subreddit': subreddit,
        'size': 100,  # Ліміт на один запит
        'before': before_timestamp
    }
    try:
        async with session.get(URL, params=params, timeout=10) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('data', [])
            else:
                print(f"Помилка API: {response.status}")
                return []
    except Exception as e:
        print(f"Помилка мережі: {e}")
        return []

async def main():
    all_comments = []
    # Починаємо з поточного часу
    current_before = int(time.time())
    
    async with aiohttp.ClientSession() as session:
        # Зробимо для прикладу 3 послідовні сторінки (імітація пагінації)
        for page in range(3):
            print(f"Завантаження сторінки {page + 1}...")
            comments = await fetch_comments(session, SUBREDDIT, current_before)
            
            if not comments:
                break
                
            all_comments.extend(comments)
            # Оновлюємо мітку часу на створення найстарішого коментаря з отриманих, 
            # щоб наступний запит дістав ще старіші дані
            current_before = comments[-1]['created_utc']
            
            # Невеликий таймаут, щоб не забанили (Rate Limit)
            await asyncio.sleep(1)

    # Сортуємо коментарі за часом в хронологічному порядку (від старих до нових)
    # В Pushshift вони зазвичай йдуть reverse-chronological, тому сортуємо вручну:
    all_comments.sort(key=lambda x: x.get('created_utc', 0))

    # Запис у JSON файл
    with open("reddit_comments.json", "w", encoding="utf-8") as f:
        json.dump(all_comments, f, ensure_ascii=False, indent=4)
        
    print(f"Успішно збережено {len(all_comments)} коментарів у reddit_comments.json")

if __name__ == "__main__":
    asyncio.run(main())
```

## Task 3: Echo Server на asyncio Tasks

Для створення сокет-сервера в `asyncio` найкраще використовувати високорівневі `asyncio.start_server`. Він автоматично керує клієнтськими з'єднаннями та запускає їх як окремі асинхронні `Task`.

Python

```
import asyncio

async def handle_echo(reader, writer):
    """
    Ця функція викликається автоматично при кожному новому підключенні.
    Кожне з'єднання обробляється у власній asyncio.Task.
    """
    address = writer.get_extra_info('peername')
    print(f"[*] Нове підключення від {address}")

    try:
        while True:
            # Читаємо дані з сокету буфером до 1024 байт
            data = await reader.read(1024)
            if not data:
                print(f"[-] Клієнт {address} розірвав з'єднання")
                break

            message = data.decode('utf-8').strip()
            print(f"[{address}] Отримано: {message}")

            # Відправляємо назад (Echo)
            writer.write(data)
            await writer.drain()  # Очікуємо, поки буфер очиститься
            
    except asyncio.CancelledError:
        print(f"[-] Завдання для {address} було скасовано")
    except Exception as e:
        print(f"[!] Помилка при роботі з {address}: {e}")
    finally:
        print(f"[*] Закриття сокету для {address}")
        writer.close()
        await writer.wait_closed()

async def main():
    host = '127.0.0.1'
    port = 8888
    
    # Запуск сервера
    server = await asyncio.start_server(handle_echo, host, port)
    
    addr = server.sockets[0].getsockname()
    print(f"[*] Сервер запущено на {addr}")

    # Змушуємо сервер працювати нескінченно
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Сервер зупинено користувачем.")
```