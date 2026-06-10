import socket


HOST = "127.0.0.1"
PORT = 6379


def send_raw_ping(host: str = HOST, port: int = PORT) -> None:
    """
    Надсилає Redis команду PING напряму через TCP socket.

    Redis НЕ отримує Python object.

    Redis отримує RESP bytes:

        *1\r\n
        $4\r\n
        PING\r\n

    Пояснення:
    - *1    => array з 1 елемента
    - $4    => bulk string довжиною 4 bytes
    - PING  => сама команда
    """

    command = (
        b"*1\r\n"
        b"$4\r\n"
        b"PING\r\n"
    )

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        print("[CLIENT] Connecting to Redis...")
        sock.connect((host, port))

        print("[CLIENT] Sending raw RESP command:")
        print(command)

        sock.sendall(command)

        print("[CLIENT] Waiting for Redis response...")
        response = sock.recv(1024)

        print("[CLIENT] Raw response:")
        print(response)

        print("[CLIENT] Decoded response:")
        print(response.decode("utf-8"))

    finally:
        sock.close()
        print("[CLIENT] Socket closed")


if __name__ == "__main__":
    send_raw_ping()
