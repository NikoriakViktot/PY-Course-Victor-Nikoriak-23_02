import time
import requests

# URL-адреси твого локального сервера Django
URL_INDEX = "http://127.0.0.1:8000/notes/"
URL_CREATE = "http://127.0.0.1:8000/notes/create/"


def run_benchmark():
    print("=== ЗАПУСК ВИМІРЮВАННЯ ШВИДКОСТІ ===")

    # Створюємо сесію, щоб імітувати авторизованого користувача
    session = requests.Session()

    # 1. Тест головної сторінки
    start_index = time.time()
    res_index = session.get(URL_INDEX)
    end_index = time.time()
    time_index = end_index - start_index
    print(f"Головна сторінка (index): {time_index:.4f} сек (Статус: {res_index.status_code})")

    # 2. Тест сторінки створення
    start_create = time.time()
    res_create = session.get(URL_CREATE)
    end_create = time.time()
    time_create = end_create - start_create
    print(f"Сторінка створення (create): {time_create:.4f} сек (Статус: {res_create.status_code})")

    # 3. Сумарний час
    total_time = time_index + time_create
    print("-----------------------------------")
    print(f"СУМАРНИЙ ЧАС НА ВСІ ЗАПИТИ: {total_time:.4f} сек\n")


if __name__ == "__main__":
    run_benchmark()