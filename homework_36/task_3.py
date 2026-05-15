import asyncio


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info('peername')
    print(f'Connection from {addr}')

    try:
        while True:
            data = await reader.readline()

            if not data:
                break

            message = data.decode().strip()
            print(f'Received: {message}')

            reply = f'Echo: {message}\n'
            writer.write(reply.encode())
            await writer.drain()

    except asyncio.CancelledError:
        print(f'Connection cancelled: {addr}')

    finally:
        print(f'Closing connection: {addr}')
        writer.close()
        await writer.wait_closed()


async def main():
    server = await asyncio.start_server(
        handle_client,
        host='127.0.0.1',
        port=8888
    )

    addr = server.sockets[0].getsockname()
    print(f'Server running on {addr}')

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())