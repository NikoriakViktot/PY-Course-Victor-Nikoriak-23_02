import socket


HOST = "127.0.0.1"
PORT = 6379


def check_redis_socket(host: str = HOST, port: int = PORT) -> None:
    """
    Перевіряє, що Redis доступний як TCP server.

    Це ще НЕ Redis command.
    Це лише TCP connection test.

    Якщо connect() успішний, це означає:
    - Docker port forwarding працює;
    - Redis container слухає 6379;
    - OS kernel дозволив TCP connection.
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        print(f"[CLIENT] Connecting to Redis at {host}:{port} ...")

        sock.connect((host, port))

        print("[CLIENT] TCP connection established")
        print("[CLIENT] Redis is reachable as a socket server")

    finally:
        sock.close()
        print("[CLIENT] Socket closed")


if __name__ == "__main__":
    check_redis_socket()
