import asyncio


HOST = "127.0.0.1"
PORT = 5000


async def handle_client(reader, writer):
    addr = writer.get_extra_info("peername")
    print(f"[CONNECTED] {addr}")

    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break

            writer.write(data)
            await writer.drain()

    except asyncio.CancelledError:
        pass
    finally:
        writer.close()
        await writer.wait_closed()
        print(f"[DISCONNECTED] {addr}")


async def main():
    server = await asyncio.start_server(handle_client, HOST, PORT)

    addr = server.sockets[0].getsockname()
    print(f"Server running on {addr}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())