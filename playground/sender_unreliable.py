import socket
import time
from typing import Tuple


def send(addr: str, port: int, buf: bytes) -> Tuple[bool,int, float]:
    start = time.perf_counter_ns() * (pow(10, -9))
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.sendto(buf, (addr, port))
        actual_end = 0.0
        while True:
            data, address = s.recvfrom(2048)
            end = time.perf_counter_ns() * (pow(10, -9))
            if address == (addr, port):
                actual_end = end
                break
            if end - start >= 0.2:
                return (False, 1, -1)
        return (True, 1, actual_end - start)
    except socket.timeout:
        return (False, 1, -1)
