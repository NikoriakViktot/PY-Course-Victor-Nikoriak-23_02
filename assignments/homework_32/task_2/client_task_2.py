import socket


def caesar_encrypt(text, key):
    """Зашифровує текст шифром Цезаря (підтримує англійський алфавіт)."""
    encrypted_text = []
    for char in text:
        if char.isalpha():
            start = ord("A") if char.isupper() else ord("a")
            # Зсуваємо вперед для шифрування
            new_char = chr((ord(char) - start + key) % 26 + start)
            encrypted_text.append(new_char)
        else:
            encrypted_text.append(char)
    return "".join(encrypted_text)


client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ("127.0.0.1", 65432)

# Параметри повідомлення
key = 3
original_text = "Hello World!"

# Шифруємо текст перед відправкою
secret_text = caesar_encrypt(original_text, key)
print(f"Оригінальний текст: {original_text}")
print(f"Зашифрований текст: {secret_text}")

# Формуємо пакет: "ключ:зашифрований_текст"
package = f"{key}:{secret_text}"

try:
    print(f"Відправка пакету на сервер: {package}")
    client_socket.sendto(package.encode("utf-8"), server_address)

    # Очікуємо розшифровану відповідь від сервера
    data, server = client_socket.recvfrom(1024)
    print(f"Відповідь від ехо-сервера: {data.decode('utf-8')}")

finally:
    client_socket.close()
