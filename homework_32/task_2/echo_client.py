import socket

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

message = input("Введи: текст|ключ (наприклад hello|3): ")

client.sendto(message.encode(), ("127.0.0.1", 8888))

response, _ = client.recvfrom(1024)
print("Відповідь:", response.decode())

client.close()