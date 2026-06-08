import socket
import threading
def handle_client(client_socket, client_address):
    """Функція для обробки взаємодії з конкретним клієнтом в окремому потоці."""
    print(f"[НОВЕ ПІДКЛЮЧЕННЯ] Клієнт {client_address} підключився.")
    # Використовуємо контекстний менеджер для автоматичного закриття сокета клієнта
    with client_socket:
        while True:
            try:
                # Очікуємо дані від клієнта (розмір буфера — 1024 байти)
                data = client_socket.recv(1024)
                # Якщо дані порожні, це означає, що клієнт розірвав з'єднання
                if not data:
                    break
                print(f"[{client_address}] Отримано: {data.decode('utf-8')}")
                # Відправляємо ехо-відповідь (ті самі дані) назад клієнту
                client_socket.sendall(data)
            except ConnectionResetError:
                # Обробка випадку, коли клієнт раптово закрив програму
                break
            except Exception as e:
                print(f"[ПОМИЛКА] Збій під час роботи з {client_address}: {e}")
                break
    print(f"[ВІДКЛЮЧЕННЯ] З'єднання з клієнтом {client_address} закрито.")
    # Виводимо поточну кількість активних потоків (включаючи головний потік)
    print(f"[ІНФО] Активних потоків у системі: {threading.active_count() - 1}")
def start_server():
    host = "127.0.0.1"  # Локальна адреса
    port = 65435  # Вільний порт
    # Створюємо TCP сокет
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Налаштування для повторного використання порту без очікування тайм-аутів OS
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen()
    print(f"[ЗАПУСК] Ехо-сервер запущено на {host}:{port}")
    print("[ОЧІКУВАННЯ] Чекаємо на підключення клієнтів...")
    try:
        while True:
            # Блокуючий виклик, чекаємо на нового клієнта
            client_socket, client_address = server_socket.accept()
            # Створюємо новий потік для обслуговування цього клієнта
            # target — функція, яку треба запустити, args — аргументи для неї
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address)
            )
            # Робимо потік демоном, щоб він автоматично закривався при зупинці сервера
            client_thread.daemon = True
            # Стартуємо потік
            client_thread.start()
            # Виводимо кількість клієнтів (активні потоки мінус 1 головний потік)
            print(f"[ІНФО] Потік створено. Клієнтів онлайн: {threading.active_count() - 1}")
    except KeyboardInterrupt:
        print("\n[ЗУПИНКА] Сервер зупиняє роботу за командою користувача.")
    finally:
        server_socket.close()
if __name__ == "__main__":
    start_server()