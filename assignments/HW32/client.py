import socket

# створюємо UDP сокет
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# надсилаємо повідомлення серверу
client_socket.sendto(b"Hello, server!", ("127.0.0.1", 8080))

# отримуємо відповідь
data, addr = client_socket.recvfrom(1024)
print("Відповідь від сервера:", data.decode())

client_socket.close()
