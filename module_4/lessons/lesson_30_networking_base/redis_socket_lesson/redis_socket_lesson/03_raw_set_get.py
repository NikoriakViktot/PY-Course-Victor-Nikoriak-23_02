import socket


HOST = "127.0.0.1"
PORT = 6379


def send_command(sock: socket.socket, command: bytes) -> bytes:
    """
    Відправляє одну raw RESP command і читає одну відповідь.

    Обмеження:
    - це навчальна функція;
    - вона читає recv(1024) один раз;
    - для великих відповідей production client має читати stream циклом.
    """

    print("\n[CLIENT] Sending:")
    print(command)

    sock.sendall(command)

    response = sock.recv(1024)

    print("[CLIENT] Response:")
    print(response)

    return response


def raw_set_get(host: str = HOST, port: int = PORT) -> None:
    """
    Демонструє SET і GET через raw TCP.

    Команда:

        SET lesson redis

    RESP форма:

        *3\r\n
        $3\r\n
        SET\r\n
        $6\r\n
        lesson\r\n
        $5\r\n
        redis\r\n

    Потім:

        GET lesson
    """

    set_command = (
        b"*3\r\n"
        b"$3\r\n"
        b"SET\r\n"
        b"$6\r\n"
        b"lesson\r\n"
        b"$5\r\n"
        b"redis\r\n"
    )

    get_command = (
        b"*2\r\n"
        b"$3\r\n"
        b"GET\r\n"
        b"$6\r\n"
        b"lesson\r\n"
    )

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        print("[CLIENT] Connecting to Redis...")
        sock.connect((host, port))

        send_command(sock, set_command)
        send_command(sock, get_command)

    finally:
        sock.close()
        print("\n[CLIENT] Socket closed")


if __name__ == "__main__":
    raw_set_get()
