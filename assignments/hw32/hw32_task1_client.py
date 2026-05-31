import socket

HOST = "127.0.0.1"
PORT = 12345

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    message = input("Enter message (or 'exit'): ")

    if message == "exit":
        break

    client_socket.sendto(message.encode(), (HOST, PORT))

    data, _ = client_socket.recvfrom(1024)
    print("Server response:", data.decode())

client_socket.close()