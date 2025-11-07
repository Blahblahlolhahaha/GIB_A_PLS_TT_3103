import csv
import sys
import string
import random
import threading
import time

from datetime import datetime

from gamenet_api import GameNetAPI, CH_RELIABLE, CH_UNRELIABLE

# Test Reproducibility Parameters
PACKET_SIZE_MIN = 50  # bytes
PACKET_SIZE_MAX = 100  # bytes
SEND_RATE_DELAY_MS = 20  # milliseconds between packets (50 packets/sec)
# Total duration = num_packets * SEND_RATE_DELAY_MS / 1000 seconds


class Sender:
    def __init__(self, num_packets, reliability_probability) -> None:
        self.num_packets = num_packets
        self.reliability_probability = reliability_probability

        self.addr = "localhost"
        self.port = 8000

        self.dest_addr = "localhost"
        self.dest_port = 8002

        self.buffers = []

        self.num_reliable = 0
        self.reliable_responses = []
        self.reliable_time = []

        self.num_unreliable = 0
        self.unreliable_responses = []
        self.unreliable_time = []

        self.gamenet = GameNetAPI(
            (self.addr, self.port), (self.dest_addr, self.dest_port)
        )

    def start(self):
        self._init_arrays()
        print(f"Starting sender with {self.num_packets} packets")
        print(f"Packet size: {PACKET_SIZE_MIN}-{PACKET_SIZE_MAX} bytes")
        print(f"Send rate: {1000/SEND_RATE_DELAY_MS:.1f} packets/sec ({SEND_RATE_DELAY_MS}ms delay)")
        estimated_duration = self.num_packets * SEND_RATE_DELAY_MS / 1000
        print(f"Estimated test duration: {estimated_duration:.1f} seconds")
        print()
        
        try:
            self.gamenet.start()
            for i in range(self.num_packets):
                payload = self._gen_payload()
                send_thread = threading.Thread(target=self.send, args=(i, payload))

                self.buffers.append((i, send_thread))
                send_thread.start()
                
                # Rate limiting: wait between packet sends
                time.sleep(SEND_RATE_DELAY_MS / 1000.0)
        finally:
            # Gracefully Shut down
            for buffer in self.buffers:
                i, send_thread = buffer
                send_thread.join()
            self.gamenet.close()

        # self.write_metrics()

    def _init_arrays(self):
        for _ in range(self.num_packets):
            self.reliable_responses.append(None)
            self.reliable_time.append(None)

            self.unreliable_responses.append(None)
            self.unreliable_time.append(None)

    def _gen_payload(self, size: int = -1):
        if size == -1:
            size = random.randint(PACKET_SIZE_MIN, PACKET_SIZE_MAX)

        valid_characters = string.ascii_letters + string.digits
        payload = "".join(random.choice(valid_characters) for _ in range(size))

        return payload

    def send(self, idx: int, payload: str):
        """
        Calls GameNetAPI to build and send packet to Receiver (Each call = 1x packet to send)
        The GameNetAPI send() method should also return the ACK packet if received in the same function call?
            => Multithread the sending of each packet as seen in `start()`
        """

        is_reliable = True
        self.num_reliable += 1

        rdm_val = random.random()
        if rdm_val > self.reliability_probability:
            is_reliable = False

            self.num_reliable -= 1
            self.num_unreliable -= 1

        b_payload = bytes(payload, "utf-8")

        if is_reliable:
            self.reliable_time[idx] = datetime.now()
        else:
            self.unreliable_time[idx] = datetime.now()

        # Will block here until response (seq) returned from gamenet
        # I dont think I need sequence number?
        self.gamenet.send(payload=b_payload, reliable=is_reliable)

        if is_reliable:
            self.reliable_time[idx] = datetime.now() - self.reliable_time[idx]
        else:
            self.unreliable_time[idx] = datetime.now() - self.unreliable_time[idx]

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            "Expected 2 arguments: number of packets to send and reliability probability"
        )
        print("[USAGE] python3 sender.py <num_packets> <reliability_probability>")
    else:
        num_packets = int(sys.argv[1])
        reliability_probability = float(sys.argv[2])
        sender = Sender(num_packets, reliability_probability)
        sender.start()
