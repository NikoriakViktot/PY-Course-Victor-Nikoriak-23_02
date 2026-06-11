import asyncio


HOST = "127.0.0.1"
PORT = 8888


async def main():
    reader, writer = await asyncio.open_connection(HOST, PORT)

    message = input("Enter message: ")
    writer.write(message.encode())
    await writer.drain()

    data = await reader.read(1024)
    print("Echo response:", data.decode(errors="ignore"))

    writer.close()
    await writer.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
