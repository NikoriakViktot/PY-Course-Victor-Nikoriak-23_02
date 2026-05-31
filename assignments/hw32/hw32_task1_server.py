import socket

HOST = "127.0.0.1"
PORT = 12345

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((HOST, PORT))

print("UDP Server is running...")

while True:
    data, addr = server_socket.recvfrom(1024)
    message = data.decode()

    print(f"Received from {addr}: {message}")

    response = f"Server received: {message}"
    server_socket.sendto(response.encode(), addr)