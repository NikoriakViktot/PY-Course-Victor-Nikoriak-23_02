import socket

SERVER_HOST = 'localhost'
SERVER_PORT = 8888


client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

message = input("Ваше повідомлення: ")
client.sendto(message.encode(), (SERVER_HOST, SERVER_PORT))


client.settimeout(2.0)
try:
    response, _ = client.recvfrom(1024)
    print(f"Відповідь сервера: {response.decode()}")

except socket.timeout:
    print("Сервер не відповів вчасно")

finally:
    client.close()