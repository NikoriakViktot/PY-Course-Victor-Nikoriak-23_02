import socket


HOST = "127.0.0.1"
PORT = 9000


def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))

    try:
        while True:
            message = input("Enter message or 'exit': ")

            if message.lower() == "exit":
                break

            client_socket.sendall(message.encode("utf-8"))
            response = client_socket.recv(1024)

            print(f"Echo from server: {response.decode('utf-8')}")
    finally:
        client_socket.close()


if __name__ == "__main__":
    start_client()
