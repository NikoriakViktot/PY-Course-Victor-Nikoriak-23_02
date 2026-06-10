import socket

HOST = '0.0.0.0'
PORT = 8888


server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))
print(f'UDP сервер запущено на {HOST}:{PORT}')


try:
    while True:
        data, addr = server.recvfrom(1024)
        message = data.decode(errors='ignore')

        print(f'[Отримано від {addr}]: {message}')

        response = f'Ти написала {message}'
        server.sendto(response.encode(), addr)


except KeyboardInterrupt:
    print('\nСервер зупинено')


finally:
    server.close()