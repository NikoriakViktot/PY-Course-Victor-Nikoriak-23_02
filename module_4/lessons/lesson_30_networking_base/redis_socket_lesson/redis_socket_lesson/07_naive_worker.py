import json
import socket
import time


HOST = "127.0.0.1"
PORT = 6379
QUEUE_NAME = "lesson_tasks"


def resp_command(*parts: str) -> bytes:
    chunks = [f"*{len(parts)}\r\n".encode("utf-8")]

    for part in parts:
        data = part.encode("utf-8")
        chunks.append(f"${len(data)}\r\n".encode("utf-8"))
        chunks.append(data + b"\r\n")

    return b"".join(chunks)


def parse_bulk_string_response(response: bytes) -> str | None:
    """
    Дуже спрощений RESP parser для bulk string.

    Redis response для RPOP виглядає так:

        $89\r\n{"id": "..."}\r\n

    Якщо queue порожня:

        $-1\r\n

    Це навчальна версія, не production parser.
    """

    if response.startswith(b"$-1"):
        return None

    header, body = response.split(b"\r\n", maxsplit=1)

    size = int(header[1:])

    data = body[:size]

    return data.decode("utf-8")


def redis_request(command: bytes) -> bytes:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((HOST, PORT))
        sock.sendall(command)
        return sock.recv(4096)

    finally:
        sock.close()


def consume_once() -> None:
    """
    Consumer side.

    Імітує Celery worker.

    Worker читає task з Redis queue через RPOP.
    """

    command = resp_command("RPOP", QUEUE_NAME)

    response = redis_request(command)

    print("[WORKER] Raw Redis response:", response)

    task_json = parse_bulk_string_response(response)

    if task_json is None:
        print("[WORKER] Queue is empty")
        return

    task = json.loads(task_json)

    print("[WORKER] Received task:")
    print(task)

    print("[WORKER] Executing task...")
    time.sleep(2)

    print("[WORKER] Done:", task["id"])


def main() -> None:
    consume_once()


if __name__ == "__main__":
    main()
