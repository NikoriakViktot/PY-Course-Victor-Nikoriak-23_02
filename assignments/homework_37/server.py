import asyncio
# глобальний словник для зберігання активних клієнтів
# структура: {writer: "нікнейм"}
connected_clients = {}
async def broadcast_message(sender_writer, message_text):
    """асинхронна функція для розсилки повідомлення всім, крім відправника."""
    for client_writer in connected_clients:
        if client_writer != sender_writer:
            try:
                client_writer.write(f"{message_text}\n".encode("utf-8"))
                await client_writer.drain()
            except Exception:
                # якщо відправити не вдалося, видалення клієнта відбудеться в його handle_client
                pass
async def handle_client(reader, writer):
    """обробка підключення кожного окремого клієнта."""
    client_address = writer.get_extra_info("peername")
    # генеруємо початкове ім'я на основі порту клієнта
    default_nickname = f"користувач_{client_address[1]}"
    connected_clients[writer] = default_nickname
    print(f"[підключення] {default_nickname} приєднався з адреси {client_address}")
    # вітання для нового клієнта та інструкція
    welcome_msg = (
        f"ласкаво просимо до чату! ваш нікнейм: {default_nickname}\n"
        "щоб змінити ім'я, введіть: /ім_я нове_імя"
    )
    writer.write(f"{welcome_msg}\n".encode("utf-8"))
    await writer.drain()
    # сповіщаємо всіх про нового учасника
    await broadcast_message(writer, f"📢 {default_nickname} увійшов до чату.")
    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break
            message = data.decode("utf-8").strip()
            if not message:
                continue
            current_nickname = connected_clients[writer]
            # перевірка на команду зміни імені
            if message.startswith("/ім_я "):
                new_nickname = message.split(" ", 1)[1].strip()
                if new_nickname:
                    connected_clients[writer] = new_nickname
                    print(
                        f"[перейменування] {current_nickname} змінив ім'я на {new_nickname}"
                    )
                    writer.write(
                        f"система: ваше ім'я змінено на {new_nickname}\n".encode(
                            "utf-8"
                        )
                    )
                    await writer.drain()
                    await broadcast_message(
                        writer,
                        f"🔄 {current_nickname} змінює ім'я на {new_nickname}.",
                    )
                else:
                    writer.write(
                        "система: ім'я не може бути порожнім.\n".encode("utf-8")
                    )
                    await writer.drain()
            # звичайне повідомлення в чат
            else:
                print(f"[{current_nickname}]: {message}")
                await broadcast_message(writer, f"[{current_nickname}]: {message}")
    except Exception as error:
        print(f"[помилка] з клієнтом {connected_clients.get(writer)}: {error}")
    finally:
        # при відключенні видаляємо клієнта та сповіщаємо чат
        leaving_nickname = connected_clients.pop(writer, "невідомий")
        print(f"[відключення] {leaving_nickname} залишив чат.")
        await broadcast_message(writer, f"🚪 {leaving_nickname} залишив чат.")
        writer.close()
        await writer.wait_closed()
async def main():
    host_address = "127.0.0.1"
    port_number = 65432
    server = await asyncio.start_server(handle_client, host_address, port_number)
    print(f"[старт] сервер чату запущено на {host_address}:{port_number}")
    async with server:
        await server.serve_forever()
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[зупинка] сервер зупинено користувачем.")