import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
HOST = "127.0.0.1"
PORT = 65432
server_socket.bind((HOST, PORT))

print(f"UDP-сервер запущено на {HOST}:{PORT}. Очікування повідомлень...")

while True:
    data, client_address = server_socket.recvfrom(1024)
    message = data.decode("utf-8")
    print(f"Отримано від {client_address}: {message}")

    response = f"Сервер отримав ваше повідомлення: '{message}'"
    server_socket.sendto(response.encode("utf-8"), client_address)
