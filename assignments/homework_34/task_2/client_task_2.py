import socket
import time

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER_ADDRESS = ("127.0.0.1", 65432)

try:
    client_socket.connect(SERVER_ADDRESS)
    print("Успішно підключено до багатопоточного сервера!")

    # Надішлемо кілька повідомлень з паузою, щоб імітувати тривалу роботу
    messages = ["Привіт!", "Як справи?", "Тест багатопоточності працює."]

    for msg in messages:
        print(f"Відправка: {msg}")
        client_socket.sendall(msg.encode("utf-8"))

        # Очікуємо відповідь
        data = client_socket.recv(1024)
        print(f"Отримано від сервера: {data.decode('utf-8')}\n")

        time.sleep(2)  # Пауза 2 секунди перед наступним повідомленням

finally:
    client_socket.close()
    print("З'єднання закрито.")
