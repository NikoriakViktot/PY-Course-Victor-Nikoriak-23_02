import socket


HOST = "127.0.0.1"
PORT = 8888
BUFFER_SIZE = 1024


def run_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((HOST, PORT))

    print(f"UDP server is running on {HOST}:{PORT}")

    try:
        while True:
            data, address = server.recvfrom(BUFFER_SIZE)
            message = data.decode("utf-8", errors="replace")

            print(f"Message from {address}: {message}")

            response = f"Server received: {message}"
            server.sendto(response.encode("utf-8"), address)
    except KeyboardInterrupt:
        print("\nServer stopped")
    finally:
        server.close()


if __name__ == "__main__":
    run_server()
