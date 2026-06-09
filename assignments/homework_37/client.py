import asyncio
import sys
async def listen_for_messages(reader):
    """корутина для постійного читання повідомлень від сервера."""
    try:
        while True:
            data = await reader.read(1024)
            if not data:
                print("\n[чат] з'єднання з сервером розірвано.")
                break
            # виводимо отримане повідомлення
            print(data.decode("utf-8").strip())
    except asyncio.CancelledError:
        pass
    except Exception as error:
        print(f"\n[помилка] читання з сервера: {error}")
async def send_messages(writer):
    """корутина для зчитування введення користувача та відправки на сервер."""
    try:
        while True:
            # asyncio.to_thread дозволяє запустити блокуючий input() без заморожування event loop
            user_input = await asyncio.to_thread(input)
            if not user_input.strip():
                continue
            # відправляємо текст на сервер
            writer.write(f"{user_input}\n".encode("utf-8"))
            await writer.drain()
            if user_input.strip() == "/вихід":
                break
    except Exception as error:
        print(f"[помилка] відправки повідомлення: {error}")
async def main():
    host_address = "127.0.0.1"
    port_number = 65432
    try:
        print("[підключення] підключаємось до чату...")
        reader, writer = await asyncio.open_connection(host_address, port_number)
        print("[успіх] підключено успішно!\n")
        # запускаємо паралельно два завдання: одне на читання, інше на запис
        listen_task = asyncio.create_task(listen_for_messages(reader))
        send_task = asyncio.create_task(send_messages(writer))
        # чекаємо, поки хоча б одне завдання завершиться (наприклад, користувач вийде)
        done, pending = await asyncio.wait(
            [listen_task, send_task], return_when=asyncio.FIRST_COMPLETED
        )
        # скасовуємо завдання, яке ще виконується
        for task in pending:
            task.cancel()
    except ConnectionRefusedError:
        print("[помилка] сервер недоступний. перевірте, чи запущений server.py")
    finally:
        print("[завершення] вихід з чату.")
        try:
            writer.close()
            await writer.wait_closed()
        except UnboundLocalError:
            pass
        sys.exit(0)
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[вихід] роботу програми завершено.")