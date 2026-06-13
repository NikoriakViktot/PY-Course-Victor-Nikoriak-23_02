import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 65432
server_address = (SERVER_HOST, SERVER_PORT)

message = "Привіт, UDP-сервер!"

try:
    print(f"Відправка повідомлення: {message}")
    client_socket.sendto(message.encode("utf-8"), server_address)

    data, server = client_socket.recvfrom(1024)
    print(f"Відповідь від сервера: {data.decode('utf-8')}")

finally:
    print("Закриття сокету.")
    client_socket.close()
