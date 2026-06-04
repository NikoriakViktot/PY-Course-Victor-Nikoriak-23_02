import asyncio


async def handle_client(reader, writer):
    address = writer.get_extra_info('peername')
    print(f"[НОВЕ ПІДКЛЮЧЕННЯ] Клієнт {address} з'єднався.")

    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break

            writer.write(data)
            await writer.drain()

    except Exception as e:
        print(f"Помилка під час обробки клієнта {address}: {e}")
    finally:
        print(f"[ВІДКЛЮЧЕННЯ] Клієнт {address} відключився.")
        writer.close()
        await writer.wait_closed()


async def main():
    server = await asyncio.start_server(handle_client, '127.0.0.1', 55555)

    print("[СТАРТ] Асинхронний ехо-сервер запущено на 127.0.0.1:55555...")

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[ЗУПИНКА] Сервер вимкнено користувачем.")