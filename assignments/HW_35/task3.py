import socket
import multiprocessing

def handle_client(client_socket, client_address):
    print(f"[НОВИЙ ПРОЦЕС] Клієнт {client_address} обслуговується в процесі {multiprocessing.current_process().pid}")
    with client_socket:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            client_socket.sendall(data)
    print(f"[ВІДКЛЮЧЕННЯ] Клієнт {client_address} пішов.")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', 55555))
    server.listen()
    print("[СТАРТ] Мультипроцесорний сервер запущено на 127.0.0.1:55555...")

    try:
        while True:
            client_socket, client_address = server.accept()
            process = multiprocessing.Process(
                target=handle_client,
                args=(client_socket, client_address)
            )
            process.start()
            client_socket.close()
    except KeyboardInterrupt:
        print("\n[ЗУПИНКА] Сервер зупинено.")
    finally:
        server.close()

if __name__ == '__main__':
    start_server()