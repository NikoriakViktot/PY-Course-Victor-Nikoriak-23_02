import multiprocessing
import socket
import sys
def handle_client(client_socket, client_address):
    """Функція для обробки з'єднання з клієнтом в окремому процесі ОС."""
    print(
        f"[НОВИЙ ПРОЦЕС] Клієнт {client_address} обслуговується процесом PID: {multiprocessing.current_process().pid}")
    try:
        while True:
            # Очікуємо дані від клієнта (розмір буфера 1024 байти)
            data = client_socket.recv(1024)
            # Якщо дані порожні — клієнт закрив з'єднання
            if not data:
                break
            print(
                f"[PID {multiprocessing.current_process().pid}] Отримано від {client_address}: {data.decode('utf-8').strip()}")
            # Відправляємо отримані дані назад клієнту (ехо)
            client_socket.sendall(data)
    except ConnectionResetError:
        print(f"[УВАГА] Клієнт {client_address} раптово розірвав з'єднання.")
    except Exception as e:
        print(f"[ПОМИЛКА] У процесі клієнта {client_address} сталася помилка: {e}")
    finally:
        # Обов'язково закриваємо сокет всередині процесу
        client_socket.close()
        print(f"[ВІДКЛЮЧЕННЯ] З'єднання з {client_address} закрито. Процес завершує роботу.")
        sys.exit(0)  # Завершуємо дочірній процес
def start_server(host="127.0.0.1", port=65432):
    """Запуск головного серверного сокета, який створює процеси."""
    # Створюємо TCP сокет (AF_INET = IPv4, SOCK_STREAM = TCP)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Дозволяємо повторно використовувати порт відразу після перезапуску сервера
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Прив'язуємо сокет до адреси та порту
    server_socket.bind((host, port))
    # Переводимо сокет у режим прослуховування
    server_socket.listen()
    print(f"[СТАРТ] Багатопроцесорний сервер запущено на {host}:{port}")
    print(f"[ГОЛОВНИЙ ПІДПИС] Головний процес сервера має PID: {multiprocessing.current_process().pid}")
    print("Очікування підключень...\n")
    try:
        while True:
            # Приймаємо нове підключення (блокуючий виклик)
            client_socket, client_address = server_socket.accept()
            # Створюємо новий процес для цього клієнта
            client_process = multiprocessing.Process(
                target=handle_client,
                args=(client_socket, client_address)
            )
            # Запускаємо процес на рівні ОС
            client_process.start()
            # Закриваємо копію сокета в головному процесі!
            # Це критично для multiprocessing: ОС копіює дескриптор сокета в дочірній процес.
            # Якщо не закрити його тут, сокет залишатиметься відкритим, навіть коли клієнт відключиться.
            client_socket.close()
    except KeyboardInterrupt:
        print("\n[ЗУПИНКА] Сервер зупиняється користувачем...")
    finally:
        server_socket.close()
if __name__ == "__main__":
    start_server()