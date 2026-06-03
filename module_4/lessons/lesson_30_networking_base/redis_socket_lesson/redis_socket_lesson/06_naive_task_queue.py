import json
import socket
import time
import uuid


HOST = "127.0.0.1"
PORT = 6379
QUEUE_NAME = "lesson_tasks"


def resp_command(*parts: str) -> bytes:
    """
    Кодує Redis command у RESP.

    Наприклад:

        resp_command("LPUSH", "lesson_tasks", '{"task": "resize"}')

    повертає RESP byte stream.
    """

    chunks = [f"*{len(parts)}\r\n".encode("utf-8")]

    for part in parts:
        data = part.encode("utf-8")
        chunks.append(f"${len(data)}\r\n".encode("utf-8"))
        chunks.append(data + b"\r\n")

    return b"".join(chunks)


def redis_request(command: bytes) -> bytes:
    """
    Відкриває TCP connection до Redis,
    відправляє command,
    читає response,
    закриває socket.

    Для уроку це простіше.

    У production clients використовують persistent connections
    і connection pool.
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((HOST, PORT))
        sock.sendall(command)
        return sock.recv(4096)

    finally:
        sock.close()


def enqueue_task(task_name: str, payload: dict) -> str:
    """
    Producer side.

    Імітує FastAPI / Celery producer.

    Створює JSON task і кладе його у Redis list через LPUSH.
    """

    task_id = str(uuid.uuid4())

    task = {
        "id": task_id,
        "task": task_name,
        "payload": payload,
        "created_at": time.time(),
    }

    task_json = json.dumps(task)

    command = resp_command("LPUSH", QUEUE_NAME, task_json)

    response = redis_request(command)

    print("[PRODUCER] Redis response:", response)
    print("[PRODUCER] Enqueued task:", task_json)

    return task_id


def main() -> None:
    enqueue_task(
        task_name="process_image",
        payload={
            "filename": "cat.png",
            "operation": "resize",
        },
    )


if __name__ == "__main__":
    main()
