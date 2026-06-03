import socket
from typing import Iterable


HOST = "127.0.0.1"
PORT = 6379


class MiniRedisClient:
    """
    Навчальний Redis client поверх raw TCP socket.

    Його ціль:
    - показати, що Redis client — це socket + RESP encoder;
    - показати, що Redis protocol просто перетворює command у bytes.

    Це НЕ production client.
    Production client має:
    - повний RESP parser;
    - connection pooling;
    - timeout;
    - retry logic;
    - auth;
    - error handling;
    - pipeline support.
    """

    def __init__(self, host: str = HOST, port: int = PORT) -> None:
        self.host = host
        self.port = port
        self.sock: socket.socket | None = None

    def connect(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

    def close(self) -> None:
        if self.sock is not None:
            self.sock.close()
            self.sock = None

    def encode_command(self, parts: Iterable[str]) -> bytes:
        """
        Перетворює команду Redis у RESP bytes.

        ["SET", "name", "Viktor"]

        стає:

        *3\r\n
        $3\r\n
        SET\r\n
        $4\r\n
        name\r\n
        $6\r\n
        Viktor\r\n
        """

        encoded_parts = []

        parts = list(parts)

        encoded_parts.append(f"*{len(parts)}\r\n".encode("utf-8"))

        for part in parts:
            data = part.encode("utf-8")
            encoded_parts.append(f"${len(data)}\r\n".encode("utf-8"))
            encoded_parts.append(data + b"\r\n")

        return b"".join(encoded_parts)

    def execute(self, *parts: str) -> bytes:
        if self.sock is None:
            raise RuntimeError("Client is not connected. Call connect() first.")

        command = self.encode_command(parts)

        print("\n[RESP COMMAND]")
        print(command)

        self.sock.sendall(command)

        response = self.sock.recv(4096)

        print("[RAW RESPONSE]")
        print(response)

        return response


def main() -> None:
    client = MiniRedisClient()

    try:
        client.connect()

        client.execute("PING")
        client.execute("SET", "course", "networking")
        client.execute("GET", "course")
        client.execute("INCR", "counter")
        client.execute("GET", "counter")

    finally:
        client.close()


if __name__ == "__main__":
    main()
