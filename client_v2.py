import socket, sys

s = socket.socket()

hostname = "localhost"
port = 28000

s.connect((hostname, port))

while True:
    msg = sys.stdin.readline()
    s.send(msg.encode())

    reply = s.recv(1024)
    print(reply.decode())

s.close()