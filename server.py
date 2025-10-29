import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

s.bind(("127.0.0.1",5556))

def checksum(buf: bytes) -> bool:
    checksum = 0
    for i in range(0,len(buf) - 2,2):
        number = int(buf[i]) << 8 + int(buf[i])
        checksum = checksum + number
        checksum = (checksum >> 16) + (checksum & 0xffff)
        checksum += checksum >> 16
    checksum = (~checksum) & 0xffff
    return checksum == int.from_bytes(buf[-2:],byteorder="big")

while True:
    data, addr = s.recvfrom(2048)
    if not checksum(data):
        s.sendto(b"no", addr)
        continue
    s.sendto(b"yay!", addr)
