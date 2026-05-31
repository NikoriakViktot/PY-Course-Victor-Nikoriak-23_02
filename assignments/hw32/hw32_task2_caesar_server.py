import socket

HOST = "127.0.0.1"
PORT = 12346


def caesar_cipher(text, key):
    result = ""

    for char in text:
        if char.isalpha():
            shift = 65 if char.isupper() else 97
            result += chr((ord(char) - shift + key) % 26 + shift)
        else:
            result += char

    return result


server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((HOST, PORT))

print("Caesar UDP Server is running...")

while True:
    data, addr = server_socket.recvfrom(1024)

    message = data.decode()

    # expected format: "key|message"
    try:
        key_str, text = message.split("|", 1)
        key = int(key_str)

        encrypted = caesar_cipher(text, key)

        server_socket.sendto(encrypted.encode(), addr)

    except Exception as e:
        error_msg = "Invalid format. Use: key|message"
        server_socket.sendto(error_msg.encode(), addr)