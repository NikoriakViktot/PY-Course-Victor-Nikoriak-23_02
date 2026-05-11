import socket
from multiprocessing import Process


HOST = "127.0.0.1"
PORT = 5000


def handle_client(conn, addr):

    print(f"[NEW CONNECTION] {addr}")

    while True:

        data = conn.recv(1024).decode()

        if not data:
            break

        print(f"Received from {addr}: {data}")

        conn.send(data.encode())

    conn.close()

    print(f"[DISCONNECTED] {addr}")


if __name__ == "__main__":

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.bind((HOST, PORT))

    server.listen()

    print(f"Server running on {HOST}:{PORT}")


    while True:

        conn, addr = server.accept()

        process = Process(
            target=handle_client,
            args=(conn, addr)
        )

        process.start()