import socket


HOST = "127.0.0.1"
PORT = 8888
BUFFER_SIZE = 1024


def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    with client_socket:
        client_socket.connect((HOST, PORT))

        while True:
            message = input("Enter message or 'exit': ")

            if message.lower() == "exit":
                break

            client_socket.sendall(message.encode("utf-8"))
            response = client_socket.recv(BUFFER_SIZE)
            print(f"Echo response: {response.decode('utf-8', errors='ignore')}")


if __name__ == "__main__":
    main()
