import socket

# створюємо UDP сокет
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# прив’язуємо до адреси та порту
server_socket.bind(("127.0.0.1", 8080))
print("UDP сервер запущено на порту 8080...")

while True:
    data, addr = server_socket.recvfrom(1024)  # отримуємо повідомлення
    print(f"Отримано від {addr}: {data.decode()}")

    # надсилаємо відповідь клієнту
    server_socket.sendto(b"Hello from server!", addr)