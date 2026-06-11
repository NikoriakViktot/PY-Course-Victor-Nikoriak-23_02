import asyncio


HOST = "127.0.0.1"
PORT = 8888


async def handle_client(reader, writer):
    address = writer.get_extra_info("peername")
    print(f"Client connected: {address}")

    try:
        while True:
            data = await reader.read(1024)

            if not data:
                break

            message = data.decode(errors="ignore")
            print(f"Received from {address}: {message}")
            writer.write(data)
            await writer.drain()
    finally:
        print(f"Client disconnected: {address}")
        writer.close()
        await writer.wait_closed()


async def main():
    server = await asyncio.start_server(handle_client, HOST, PORT)
    address = server.sockets[0].getsockname()
    print(f"Async echo server started on {address}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped")
