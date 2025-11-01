import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

s.bind(("127.0.0.1",5556))

while True:
    data, addr = s.recvfrom(2048)
    s.sendto(b"yay!", addr)
