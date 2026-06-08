import socket
def caesar_cipher(text, key):
    result = []
    for char in text:
        if char.isalpha():
            start = ord('A') if char.isupper() else ord('a')
            new_char = chr(start + (ord(char) - start + key) % 26)
            result.append(new_char)
        else:
            result.append(char)
    return "".join(result)
HOST = "127.0.0.1"
PORT = 65432
# Створюємо TCP сокет
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()
print(f"[СЕРВЕР] Запущено. Очікування підключень на {HOST}:{PORT}...")
try:
    while True:
        conn, addr = server_socket.accept()
        print(f"[СЕРВЕР] Клієнт підключився з адреси: {addr}")
        with conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    break  # Клієнт закрив з'єднання
                try:
                    # Декодуємо отримані дані
                    received_str = data.decode("utf-8")
                    # Очікуваний формат: "KEY|TEXT" (наприклад, "3|Hello World")
                    if "|" in received_str:
                        key_part, text_to_encrypt = received_str.split("|", 1)
                        key = int(key_part)
                        print(f"[СЕРВЕР] Отримано текст: '{text_to_encrypt}' з ключем: {key}")
                        # Шифруємо текст
                        encrypted_text = caesar_cipher(text_to_encrypt, key)
                        # Відправляємо зашифрований ехо-результат назад
                        conn.sendall(encrypted_text.encode("utf-8"))
                        print(f"[СЕРВЕР] Відправлено клієнту: '{encrypted_text}'")
                    else:
                        error_msg = "Помилка: Неправильний формат даних. Використовуйте 'КЛЮЧ|ТЕКСТ'."
                        conn.sendall(error_msg.encode("utf-8"))
                except ValueError:
                    error_msg = "Помилка: Ключ повинен бути цілим числом."
                    conn.sendall(error_msg.encode("utf-8"))
                except Exception as e:
                    print(f"[СЕРВЕР] Помилка обробки: {e}")
                    break
        print(f"[СЕРВЕР] З'єднання з {addr} закрито.")
except KeyboardInterrupt:
    print("\n[СЕРВЕР] Зупинка роботи.")
finally:
    server_socket.close()