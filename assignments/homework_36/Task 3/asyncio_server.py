import asyncio
async def handle_client(reader, writer):
    """Корутина для обробки з'єднання з окремим клієнтом.
    Кожне підключення автоматично запускається як окреме asyncio.Task.
    """
    client_address = writer.get_extra_info("peername")
    print(f"[нове з'єднання] клієнт {client_address} підключився.")
    try:
        while True:
            # асинхронно очікуємо дані від клієнта (буфер 1024 байти)
            data = await reader.read(1024)
            # якщо дані порожні — клієнт закрив сокет
            if not data:
                break
            message = data.decode("utf-8").strip()
            print(f"[{client_address}] отримано: {message}")
            # відправляємо отримані дані назад клієнту (ехо)
            writer.write(data)
            # чекаємо, поки дані гарантовано відправляться в мережевий буфер
            await writer.drain()
    except asyncio.CancelledError:
        print(f"[скасовано] завдання для клієнта {client_address} було скасовано.")
    except Exception as error:
        print(f"[помилка] у з'єднанні з клієнтом {client_address}: {error}")
    finally:
        # закриваємо з'єднання та звільняємо ресурси
        writer.close()
        await writer.wait_closed()
        print(f"[відключення] з'єднання з {client_address} закрито.")
async def start_server():
    """Корутина для налаштування та запуску головного асинхронного сервера."""
    host_address = "127.0.0.1"
    port_number = 65432
    # створюємо та запускаємо сервер, передаючи обробник корутини
    server = await asyncio.start_server(handle_client, host_address, port_number)
    server_addresses = ", ".join(
        str(socket.getsockname()) for socket in server.sockets
    )
    print(f"[старт] асинхронний ехо-сервер запущено на {server_addresses}")
    # запускаємо нескінченний цикл прослуховування портів
    async with server:
        await server.serve_forever()
if __name__ == "__main__":
    try:
        # запускаємо головний асинхронний цикл подій (event loop)
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("\n[зупинка] сервер зупинено користувачем.")