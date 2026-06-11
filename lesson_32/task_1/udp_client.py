import socket


SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8888
BUFFER_SIZE = 1024


def run_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(5)

    try:
        message = input("Enter message: ")
        client.sendto(message.encode("utf-8"), (SERVER_HOST, SERVER_PORT))

        response, _ = client.recvfrom(BUFFER_SIZE)
        print(f"Server response: {response.decode('utf-8', errors='replace')}")
    except socket.timeout:
        print("Server did not respond")
    finally:
        client.close()


if __name__ == "__main__":
    run_client()
