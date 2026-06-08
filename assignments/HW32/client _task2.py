import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# приклад: ключ = 3, повідомлення = "Hello World"
message = "3;Hello World"
client_socket.sendto(message.encode(), ("127.0.0.1", 8080))

data, addr = client_socket.recvfrom(1024)
print("Відповідь від сервера:", data.decode())

client_socket.close()

