import socket
import time
from typing import Tuple


def checksum(buf: bytes) -> bool:
    checksum = 0
    for i in range(0,len(buf), 2):
        number = int(buf[i]) << 8 + int(buf[i])
        checksum = checksum + number
        checksum = (checksum >> 16) + (checksum & 0xffff)
        checksum += checksum >> 16
    checksum = (~checksum) & 0xffff
    return checksum.to_bytes(2, byteorder="big")

def send(addr: str, port: int, buf: bytes) -> Tuple[bool, float]:
    start = time.perf_counter_ns() * (pow(10, -9))
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.05)
            buf += checksum(buf)
            s.sendto(buf, (addr, port))
            actual_end = 0.0
            while True:
                data, address = s.recvfrom(2048)
                if data == b"no":
                    continue
                end = time.perf_counter_ns() * (pow(10, -9))
                if address == (addr, port):
                    actual_end = end
                    break
                if end - start >= 0.2:
                    return (False, -1)
            return (True, actual_end - start)
        except socket.timeout:
            continue


