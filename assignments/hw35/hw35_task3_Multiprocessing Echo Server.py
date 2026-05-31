import socket
from multiprocessing import Process


HOST = "127.0.0.1"
PORT = 5000


def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr}")

    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            conn.sendall(data)

    print(f"[DISCONNECTED] {addr}")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"Server running on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()

        process = Process(target=handle_client, args=(conn, addr))
        process.daemon = True
        process.start()

        conn.close()


if __name__ == "__main__":
    main()