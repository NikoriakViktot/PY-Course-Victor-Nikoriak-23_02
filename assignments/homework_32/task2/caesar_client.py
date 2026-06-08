import socket
HOST = "127.0.0.1"
PORT = 65432
# Створюємо TCP сокет
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client_socket.connect((HOST, PORT))
    print(f"[КЛІЄНТ] Успішно підключено до сервера {HOST}:{PORT}")
    # Інтерактивне введення даних користувачем
    text = input("Введіть текст для шифрування (англійською): ")
    while True:
        try:
            key = int(input("Введіть секретний ключ (ціле число зсуву): "))
            break
        except ValueError:
            print("Будь ласка, введіть коректне ціле число.")
    # Формуємо рядок згідно з протоколом "КЛЮЧ|ТЕКСТ"
    payload = f"{key}|{text}"
    # Надсилаємо дані серверу
    client_socket.sendall(payload.encode("utf-8"))
    print("[КЛІЄНТ] Дані відправлено. Очікування відповіді...")
    # Отримуємо зашифровану відповідь
    response = client_socket.recv(1024)
    print(f"[КЛІЄНТ] Відповідь від сервера (Зашифрований ехо-текст):")
    print(f"-> {response.decode('utf-8')}")
except Exception as e:
    print(f"[КЛІЄНТ] Помилка мережі: {e}")
finally:
    client_socket.close()
    print("[КЛІЄНТ] З'єднання закрито.")