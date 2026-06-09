import socket
# Адреса та порт сервера, якому ми надсилаємо пакети
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5002
# Створюємо UDP сокет (AF_INET = IPv4, SOCK_DGRAM = UDP)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Повідомлення, яке ми хочемо відправити
message_to_send = "Привіт від UDP Клієнта!"
try:
    print(f"[КЛІЄНТ] Надсилання пакета на {SERVER_HOST}:{SERVER_PORT}...")
    # Метод sendto приймає (байти, (IP, порт))
    client_socket.sendto(message_to_send.encode("utf-8"), (SERVER_HOST, SERVER_PORT))
    # Очікуємо відповідь від сервера (блокуюча операція)
    # Оскільки це UDP, ми також отримуємо адресу відправника відповіді
    response_data, server_address = client_socket.recvfrom(1024)
    print(f"[КЛІЄНТ] Отримано відповідь від сервера {server_address}:")
    print(f"-> {response_data.decode('utf-8')}")
except Exception as e:
    print(f"[КЛІЄНТ] Сталася помилка: {e}")
finally:
    # Обов'язково закриваємо сокет для звільнення системних ресурсів
    client_socket.close()
    print("[КЛІЄНТ] Сокет закрито.")