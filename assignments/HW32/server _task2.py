import socket

def caesar_cipher(text, shift):
    result = ""
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            result += chr((ord(char) - base + shift) % 26 + base)
        else:
            result += char
    return result

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(("127.0.0.1", 8080))
print("UDP сервер запущено на порту 8080...")

while True:
    data, addr = server_socket.recvfrom(1024)
    message = data.decode()

    # очікуємо формат "ключ;текст"
    try:
        key_str, text = message.split(";", 1)
        key = int(key_str)
        encrypted = caesar_cipher(text, key)
        server_socket.sendto(encrypted.encode(), addr)
    except Exception as e:
        server_socket.sendto(f"Помилка: {e}".encode(), addr)
