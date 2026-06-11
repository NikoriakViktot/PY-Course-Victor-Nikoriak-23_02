import socket
from multiprocessing import Process


HOST = "127.0.0.1"
PORT = 8888
BUFFER_SIZE = 1024


def handle_client(client_socket, client_address):
    print(f"Client connected: {client_address}")

    with client_socket:
        while True:
            data = client_socket.recv(BUFFER_SIZE)

            if not data:
                break

            message = data.decode("utf-8", errors="ignore")
            print(f"Received from {client_address}: {message}")
            client_socket.sendall(data)

    print(f"Client disconnected: {client_address}")


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    print(f"Multiprocessing echo server is running on {HOST}:{PORT}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            process = Process(target=handle_client, args=(client_socket, client_address))
            process.daemon = True
            process.start()
            client_socket.close()
    except KeyboardInterrupt:
        print("\nServer stopped")
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
