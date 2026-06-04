import socket
import threading


def handle_client(client_socket, client_address):
    print(f"[НОВЕ З'ЄДНАННЯ] Клієнт {client_address} підключився.")
    with client_socket:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            client_socket.sendall(data)
    print(f"[ВІДКЛЮЧЕННЯ] Клієнт {client_address} відключився.")


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind(('127.0.0.1', 55555))
    server.listen()
    print("[СТАРТ] Сервер запущено на 127.0.0.1:55555. Очікування клієнтів...")

    try:
        while True:
            client_socket, client_address = server.accept()
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address)
            )
            client_thread.start()
    except KeyboardInterrupt:
        print("\n[ЗУПИНКА] Сервер зупинено.")
    finally:
        server.close()


if __name__ == "__main__":
    start_server()