import socket


def caesar_decrypt(text, key):
    """Розшифровує текст шифром Цезаря (підтримує англійський алфавіт)."""
    decrypted_text = []
    for char in text:
        if char.isalpha():
            # Визначаємо базовий ASCII-код (для великих або малих літер)
            start = ord("A") if char.isupper() else ord("a")
            # Зсуваємо назад для дешифрування
            new_char = chr((ord(char) - start - key) % 26 + start)
            decrypted_text.append(new_char)
        else:
            # Символи пунктуації, цифри та пробіли залишаємо без змін
            decrypted_text.append(char)
    return "".join(decrypted_text)


server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
HOST, PORT = "127.0.0.1", 65432
server_socket.bind((HOST, PORT))

print(f"UDP Ехо-сервер Цезаря запущено на {HOST}:{PORT}...")

while True:
    data, client_address = server_socket.recvfrom(1024)
    raw_message = data.decode("utf-8")

    try:
        # Розділяємо повідомлення на ключ та зашифрований текст
        key_str, encrypted_text = raw_message.split(":", 1)
        key = int(key_str)

        print(f"Отримано від {client_address}: Ключ={key}, Текст='{encrypted_text}'")

        # Розшифровуємо текст
        decrypted_text = caesar_decrypt(encrypted_text, key)

        # Відправляємо розшифрований текст назад клієнту (ехо-відповідь)
        response = f"Розшифровано: {decrypted_text}"
        server_socket.sendto(response.encode("utf-8"), client_address)

    except (ValueError, IndexError):
        # Якщо клієнт надіслав дані у невірному форматі
        error_msg = "Помилка: Невірний формат. Використовуйте 'ключ:текст'"
        server_socket.sendto(error_msg.encode("utf-8"), client_address)
