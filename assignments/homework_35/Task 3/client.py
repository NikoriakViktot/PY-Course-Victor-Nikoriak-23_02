import socket
import time
HOST = "127.0.0.1"
PORT = 65432
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    client_socket.connect((HOST, PORT))
    print("[ПІДКЛЮЧЕНО] Успішне підключення до багатопроцесорного ехо-сервера.")
    for i in range(3):
        message = f"Повідомлення клієнта ({i + 1})"
        print(f"[ВІДПРАВКА] Надсилаю: '{message}'")
        client_socket.sendall(message.encode("utf-8"))
        # Очікуємо ехо-відповідь
        data = client_socket.recv(1024)
        print(f"[ВІДПОВІДЬ] Отримано ехо: '{data.decode('utf-8')}'")
        time.sleep(2)