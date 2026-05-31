import socket
import threading

HOST = "127.0.0.1"
PORT = 12345


def handle_client(conn, addr):
    print(f"Connected: {addr}")

    while True:
        data = conn.recv(1024)
        if not data:
            break

        message = data.decode()
        print(f"{addr}: {message}")

        conn.sendall(f"ECHO: {message}".encode())

    conn.close()
    print(f"Disconnected: {addr}")


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

print("Threaded Echo Server running...")

while True:
    conn, addr = server.accept()
    thread = threading.Thread(target=handle_client, args=(conn, addr))
    thread.start()