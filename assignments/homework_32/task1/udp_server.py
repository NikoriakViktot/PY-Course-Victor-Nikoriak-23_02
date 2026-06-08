import socket
# Визначаємо IP-адресу та порт сервера
SERVER_HOST = "127.0.0.1"  # Localhost (локальна машина)
SERVER_PORT = 5002  # Вільний порт для UDP
# Створюємо UDP сокет (AF_INET = IPv4, SOCK_DGRAM = UDP)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Прив'язуємо сокет до адреси та порту
server_socket.bind((SERVER_HOST, SERVER_PORT))
print(f"[CЕРВЕР] Запущено. Очікування UDP-пакетів на {SERVER_HOST}:{SERVER_PORT}...")
try:
    while True:
        # Очікуємо на дані від клієнта (розмір буфера — 1024 байти)
        # Метод recvfrom повертає кортеж: (дані, (ip_клієнта, порт_клієнта))
        data, client_address = server_socket.recvfrom(1024)
        # Декодуємо отримані біти в текст
        message = data.decode("utf-8")
        print(f"[СЕРВЕР] Отримано повідомлення від {client_address}: '{message}'")
        # Формуємо відповідь клієнту
        response_message = f"Привіт, клієнте! Твоє повідомлення '{message}' успішно отримано сервером."
        # Відправляємо відповідь назад саме на ту адресу, з якої прийшов пакет
        server_socket.sendto(response_message.encode("utf-8"), client_address)
        print(f"[СЕРВЕР] Відправлено відповідь до {client_address}")
except KeyboardInterrupt:
    print("\n[СЕРВЕР] Роботу зупинено користувачем.")
finally:
    # Закриваємо сокет після завершення роботи
    server_socket.close()