import socket

HOST = "127.0.0.1"
PORT = 12345

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

while True:
    msg = input("Enter message (or exit): ")
    if msg == "exit":
        break

    client.send(msg.encode())
    response = client.recv(1024)
    print(response.decode())

client.close()