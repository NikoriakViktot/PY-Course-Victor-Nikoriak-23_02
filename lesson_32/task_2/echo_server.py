import socket


HOST = "127.0.0.1"
PORT = 8889
BUFFER_SIZE = 1024


def caesar_encrypt(text, key):
    result = ""

    for char in text:
        if char.isalpha():
            if char.islower():
                start = ord("a")
            else:
                start = ord("A")

            result += chr((ord(char) - start + key) % 26 + start)
        else:
            result += char

    return result


def parse_message(message):
    parts = message.rsplit("|", 1)

    if len(parts) != 2:
        raise ValueError("Message format must be: text|key")

    text, key = parts
    return text, int(key)


def run_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((HOST, PORT))

    print(f"Caesar echo server is running on {HOST}:{PORT}")

    try:
        while True:
            data, address = server.recvfrom(BUFFER_SIZE)
            message = data.decode("utf-8", errors="replace")

            try:
                text, key = parse_message(message)
                encrypted_text = caesar_encrypt(text, key)
                server.sendto(encrypted_text.encode("utf-8"), address)
            except ValueError as error:
                server.sendto(str(error).encode("utf-8"), address)
    except KeyboardInterrupt:
        print("\nServer stopped")
    finally:
        server.close()


if __name__ == "__main__":
    run_server()
