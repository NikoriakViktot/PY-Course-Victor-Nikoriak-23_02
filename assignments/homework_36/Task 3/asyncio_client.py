import asyncio
async def start_client():
    host_address = "127.0.0.1"
    port_number = 65432
    print("[підключення] спроба підключитися до асинхронного сервера...")
    reader, writer = await asyncio.open_connection(host_address, port_number)
    print("[успіх] ви підключилися до ехо-сервера.")
    for i in range(3):
        message = f"асинхронне повідомлення №{i+1}\n"
        print(f"[відправка] надсилаю: '{message.strip()}'")
        writer.write(message.encode("utf-8"))
        await writer.drain()
        # очікуємо відповідь від сервера
        data = await reader.read(1024)
        print(f"[відповідь] отримано ехо: '{data.decode('utf-8').strip()}'")
        await asyncio.sleep(2)
    print("[завершення] закриваємо клієнтський сокет.")
    writer.close()
    await writer.wait_closed()
if __name__ == "__main__":
    asyncio.run(start_client())