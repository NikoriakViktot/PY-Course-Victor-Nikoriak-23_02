import socket
import time


HOST = "127.0.0.1"
PORT = 6379


def partial_send_demo(host: str = HOST, port: int = PORT) -> None:
    """
    Демонструє головну ідею TCP byte stream.

    Ми НЕ відправляємо RESP command одним sendall().

    Ми розрізаємо команду на частини:

        part1
        part2
        part3

    Redis все одно зможе виконати команду,
    бо його parser збирає stream і чекає повну RESP structure.

    Це показує:
    - TCP може доставляти bytes частинами;
    - Redis не довіряє одному recv();
    - Redis має protocol parser поверх TCP stream.
    """

    parts = [
        b"*3\r\n$3\r\nSE",
        b"T\r\n$4\r\nname\r\n",
        b"$6\r\nViktor\r\n",
    ]

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        print("[CLIENT] Connecting to Redis...")
        sock.connect((host, port))

        for i, part in enumerate(parts, start=1):
            print(f"\n[CLIENT] Sending part #{i}:")
            print(part)
            sock.sendall(part)
            time.sleep(1)

        print("\n[CLIENT] Waiting for Redis response...")
        response = sock.recv(1024)

        print("[CLIENT] Response:")
        print(response)

        get_command = (
            b"*2\r\n"
            b"$3\r\n"
            b"GET\r\n"
            b"$4\r\n"
            b"name\r\n"
        )

        print("\n[CLIENT] Sending GET name:")
        print(get_command)

        sock.sendall(get_command)

        response = sock.recv(1024)

        print("[CLIENT] GET Response:")
        print(response)

    finally:
        sock.close()
        print("\n[CLIENT] Socket closed")


if __name__ == "__main__":
    partial_send_demo()
