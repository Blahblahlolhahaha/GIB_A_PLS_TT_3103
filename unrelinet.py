import socket
import sys
import random
import threading
import time
from typing import Tuple


def forward_packet(data: bytes, s: socket.socket, client_address: Tuple[str, int], server_port: int, p_loss: float, p_corrupt: float):
    try:
        server_addr = ("127.0.0.1", server_port)
        time.sleep(random.randrange(0, 40)/1000)  # at most 40ms of delay
        ss = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ss.sendto(data, server_addr)
        ss.settimeout(0.05)
        data, addr = ss.recvfrom(65536)
        if random.random() < p_loss:
            return
        time.sleep(random.randrange(0, 40)/1000)  # at most 40ms of delay
        s.sendto(data, client_address)
    except TimeoutError:
        pass
    finally:
        ss.close()

def help():
    print("Usage: python unrelinet.py <P-LOSS> <P-CORRUPT> <LISTEN-PORT> <SERVER-PORT>")


def start_server(p_loss, p_corrupt, listen_port, server_port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", listen_port))

    while True:
        data, address = s.recvfrom(65536)
        if random.random() < p_loss:
            continue
        handler_thread = threading.Thread(target=forward_packet, args=(data, s, address, server_port, p_loss, p_corrupt))
        handler_thread.start()


def main():
    args = sys.argv
    if len(args) < 5:
        help()
        exit(0)
    p_loss = float(args[1])
    p_corrupt = float(args[2])
    listen_port = int(args[3])
    server_port = int(args[4])
    start_server(p_loss, p_corrupt, listen_port, server_port)


if __name__ == "__main__":
    main()
