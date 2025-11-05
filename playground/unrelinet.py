import socket
import sys
import random
import threading
import time
from typing import Tuple

server_sock = None

def forward_packet(data: bytes, s: socket.socket, client_address: Tuple[str, int], server_port: int, p_loss: float, p_corrupt: float):
    server_addr = ("127.0.0.1", server_port)
    ss = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ss.sendto(data, server_addr)
    data, addr = ss.recvfrom(65536)
    time.sleep(random.randrange(0, 40)/1000)  # at most 40ms of delay
    if random.random() < p_loss:
        return
    s.sendto(data, client_address)


def help():
    print("Usage: python unrelinet.py <P-LOSS> <P-CORRUPT> <LISTEN-PORT> <SERVER-PORT>")


def start_server(p_loss, p_corrupt, listen_port, server_port):
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_sock.bind(("127.0.0.1", listen_port))

    while True:
        data, address = server_sock.recvfrom(65536)
        if random.random() < p_loss:
            continue
        handler_thread = threading.Thread(target=forward_packet, args=(data, server_sock, address, server_port, p_loss, p_corrupt))
        handler_thread.start()


def stop_server():
    server_sock.close()


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
