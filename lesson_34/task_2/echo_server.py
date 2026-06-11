import socket
from threading import Thread


HOST = "127.0.0.1"
PORT = 9000


def handle_client(client_socket, client_address):
    print(f"Connected by {client_address}")

    try:
        while True:
            data = client_socket.recv(1024)

            if not data:
                break

            client_socket.sendall(data)
    finally:
        print(f"Disconnected by {client_address}")
        client_socket.close()


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    print(f"Threaded echo server started on {HOST}:{PORT}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            client_thread = Thread(
                target=handle_client,
                args=(client_socket, client_address),
                daemon=True,
            )
            client_thread.start()
    except KeyboardInterrupt:
        print("\nServer stopped")
    finally:
        server_socket.close()


if __name__ == "__main__":
    start_server()
