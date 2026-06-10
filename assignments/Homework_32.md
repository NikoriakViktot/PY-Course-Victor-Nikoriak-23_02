
## Task 1: UDP Клієнт та Сервер

На відміну від TCP, протокол **UDP (User Datagram Protocol)** не встановлює постійне з'єднання (connectionless). Він просто відправляє «датаграми» на потрібну адресу, не перевіряючи, чи дійшли вони. Через це ми використовуємо методи `sendto()` та `recvfrom()`.

### UDP Сервер (`udp_server.py`)

Python

```
import socket

# Створюємо UDP сокет (SOCK_DGRAM означає UDP)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Прив'язуємо сокет до адреси та порту
SERVER_ADDRESS = ('localhost', 12345)
server_socket.bind(SERVER_ADDRESS)

print(f"UDP Сервер запущено на {SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}...")

while True:
    # Очікуємо дані від клієнта (повертає самі дані та адресу відправника)
    data, client_address = server_socket.recvfrom(1024)
    message = data.decode('utf-8')
    print(f"Отримано від {client_address}: {message}")
    
    # Відправляємо відповідь назад клієнту
    response = f"Сервер отримав ваше повідомлення: '{message}'"
    server_socket.sendto(response.encode('utf-8'), client_address)
```

### UDP Клієнт (`udp_client.py`)

Python

```
import socket

# Створюємо UDP сокет
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
SERVER_ADDRESS = ('localhost', 12345)

try:
    message = "Привіт, UDP Сервер!"
    print(f"Надсилання: {message}")
    
    # Відправляємо дані (вказуючи адресу призначення)
    client_socket.sendto(message.encode('utf-8'), SERVER_ADDRESS)
    
    # Очікуємо відповідь від сервера
    data, server = client_socket.recvfrom(1024)
    print(f"Відповідь від сервера: {data.decode('utf-8')}")

finally:
    print("Закриття сокету.")
    client_socket.close()
```

## Task 2: Ехо-сервер з Шифром Цезаря

Тут ми розширимо класичний ехо-сервер (можна використати як TCP, так і UDP; зробимо на TCP для різноманітності).

**Логіка взаємодії:**

1. Клієнт підключається і надсилає повідомлення у форматі: `КЛЮЧ|ПОВІДОМЛЕННЯ` (наприклад, `3|HELLO`).
    
2. Сервер парсить ключ (зсув) та текст, шифрує текст алгоритмом Цезаря і повертає зашифрований результат назад клієнту.
    

### Функція шифрування (допоміжна)

Python

```
def caesar_cipher(text, shift):
    result = ""
    for char in text:
        if char.isalpha():
            # Визначаємо регістр (велика/мала літера)
            start = ord('A') if char.isupper() else ord('a')
            # Зсув у межах 26 літер латинського алфавіту
            result += chr((ord(char) - start + shift) % 26)
        else:
            result += char  # Пробіли та розділові знаки не шифруємо
    return result
```

### TCP Сервер з шифруванням (`caesar_server.py`)

Python

```
import socket

def caesar_cipher(text, shift):
    result = ""
    for char in text:
        if char.isalpha():
            start = ord('A') if char.isupper() else ord('a')
            result += chr((ord(char) - start + shift) % 26)
        else:
            result += char
    return result

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 12346))
server_socket.listen(1)

print("TCP Сервер Цезаря очікує на підключення...")

while True:
    client_socket, client_address = server_socket.accept()
    print(f"Підключено: {client_address}")
    
    try:
        data = client_socket.recv(1024).decode('utf-8')
        if data:
            print(f"Отримано сирі дані: {data}")
            
            # Очікуємо формат "ключ|повідомлення", наприклад "3|HELLO"
            if "|" in data:
                shift_str, text = data.split("|", 1)
                shift = int(shift_str)
                
                # Шифруємо
                encrypted_text = caesar_cipher(text, shift)
                
                # Відправляємо назад
                client_socket.sendall(encrypted_text.encode('utf-8'))
            else:
                client_socket.sendall("Помилка: Невірний формат. Використовуйте 'ключ|текст'".encode('utf-8'))
    except Exception as e:
        print(f"Помилка: {e}")
    finally:
        client_socket.close()
```

### TCP Клієнт (`caesar_client.py`)

Python

```
import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 12346))

try:
    # Задаємо ключ та повідомлення
    key = 3
    message = "Hello World"
    payload = f"{key}|{message}"
    
    print(f"Надсилання серверу: Ключ={key}, Текст='{message}'")
    client_socket.sendall(payload.encode('utf-8'))
    
    # Отримуємо зашифровану відповідь
    encrypted_response = client_socket.recv(1024).decode('utf-8')
    print(f"Зашифрована відповідь від сервера: {encrypted_response}")

finally:
    client_socket.close()
```

### Як це протестувати:

1. Запусти спочатку файл сервера (`udp_server.py` або `caesar_server.py`) у терміналі. Він перейде в режим очікування.
    
2. Відкрий **друге вікно терміналу** і запусти відповідний файл клієнта (`udp_client.py` або `caesar_client.py`).
    
3. У терміналах з'являться логи взаємодії! Поекспериментуй зі зміною ключів чи тексту в клієнті.