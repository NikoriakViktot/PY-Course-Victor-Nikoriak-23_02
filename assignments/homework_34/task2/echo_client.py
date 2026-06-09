import socket
import sys
host = "127.0.0.1"
port = 65435
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client_socket.connect((host, port))
    print(f"[УСПІХ] Підключено до ехо-сервера {host}:{port}")
    print("Введіть ваше повідомлення. Для виходу введіть 'exit'.\n")
    while True:
        message = input("Ви: ").strip()
        if not message:
            continue
        if message.lower() == 'exit':
            print("Завершення сесії.")
            break
        # Надсилаємо дані
        client_socket.sendall(message.encode("utf-8"))
        # Отримуємо ехо-відповідь
        response = client_socket.recv(1024)
        print(f"Сервер повернув: {response.decode('utf-8')}")
except Exception as e:
    print(f"[ПОМИЛКА] Не вдалося зв'язатися з сервером: {e}")
finally:
    client_socket.close()
    print("[КЛІЄНТ] Сокет закрито.")