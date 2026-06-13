import socket
import threading


def handle_client(client_socket, client_address):
    """Функція для обробки конкретного клієнта в окремому потоці."""
    print(f"[НОВЕ ПІДКЛЮЧЕННЯ] Клієнт {client_address} підключився.")

    try:
        while True:
            # Очікуємо дані від клієнта (блокуюча операція)
            data = client_socket.recv(1024)

            # Якщо дані порожні, клієнт відключився
            if not data:
                break

            message = data.decode("utf-8")
            print(f"[{client_address}] Отримано: {message}")

            # Відправляємо луну (ехо) назад клієнту
            response = f"Ехо: {message}"
            client_socket.sendall(response.encode("utf-8"))

    except ConnectionResetError:
        print(f"[ЗБІЙ] Клієнт {client_address} різко розірвав з'єднання.")
    finally:
        # Обов'язково закриваємо сокет після завершення роботи
        client_socket.close()
        print(f"[ВІДКЛЮЧЕННЯ] З'єднання з {client_address} закрито.")


def start_server():
    # Створюємо TCP-сокет
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Дозволяємо повторно використовувати порт відразу після перезапуску сервера
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    HOST, PORT = "127.0.0.1", 65432
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    print(f"[ЗАПУСК] TCP Ехо-сервер працює на {HOST}:{PORT}")
    print("[ОЧІКУВАННЯ] Чекаємо на підключення клієнтів...")

    while True:
        # Приймаємо нове з'єднання
        client_socket, client_address = server_socket.accept()

        # Створюємо новий потік для обслуговування цього клієнта
        # daemon=True дозволяє серверу закритися, навіть якщо потоки клієнтів ще активні
        client_thread = threading.Thread(
            target=handle_client, args=(client_socket, client_address), daemon=True
        )

        # Запускаємо потік
        client_thread.start()

        # Виводимо кількість активних потоків (мінус один головний потік)
        print(f"[АКТИВНІ КЛІЄНТИ] {threading.active_count() - 1}")


if __name__ == "__main__":
    start_server()
