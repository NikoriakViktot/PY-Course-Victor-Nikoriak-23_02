import socket

HOST = "127.0.0.1"
PORT = 12346

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    key = input("Enter Caesar key (or 'exit'): ")

    if key == "exit":
        break

    message = input("Enter message: ")

    full_message = f"{key}|{message}"

    client_socket.sendto(full_message.encode(), (HOST, PORT))

    data, _ = client_socket.recvfrom(1024)
    print("Encrypted response:", data.decode())

client_socket.close()