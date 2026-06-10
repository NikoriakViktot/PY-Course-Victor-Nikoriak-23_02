import socket

def caesar_encrypt(test, shift):
    result = ''

    for char in test:
        if char.isalpha():
            shift_base = ord('a') if char.islower() else ord('A')
            result += chr((ord(char) - shift_base + shift) % 26 + shift_base)

        else:
            result += char

    return result


HOST = '0.0.0.0'
PORT = 8888

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))

print("Сервер запущено...")


while True:
    data, addr = server.recvfrom(1024)
    message = data.decode()

    try:
        text, key = message.split("|")
        key = int(key)

        encrypted = caesar_encrypt(text, key)

        server.sendto(encrypted.encode(), addr)

    except Exception as e:
        server.sendto(str(e).encode(), addr)