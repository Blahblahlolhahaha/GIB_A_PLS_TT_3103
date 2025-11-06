import csv
import sys
import string
import random
import threading

from datetime import datetime

from gamenet_api import GameNetAPI, CH_RELIABLE, CH_UNRELIABLE


class Sender:
    def __init__(self, num_packets, reliability_probability) -> None:
        self.num_packets = num_packets
        self.reliability_probability = reliability_probability

        self.addr = "localhost"
        self.port = 8000

        self.dest_addr = "localhost"
        self.dest_port = 8001

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

        try:
            for i in range(self.num_packets):
                payload = self._gen_payload()
                send_thread = threading.Thread(target=self.send, args=(i, payload))

                self.buffers.append((i, send_thread))
                send_thread.start()
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
            size = random.randint(50, 100)

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

    # def write_metrics(self):
    #     # FIX: How to check unsuccessful?
    #     is_reliable = []
    #     latency = []
    #
    #     for i in range(self.num_packets):
    #         if self.reliable_time[i] is not None:
    #             s = self.reliable_time[i].seconds
    #             ms = self.reliable_time[i].microseconds
    #
    #             latency.append(f"{s}.{ms}")
    #             is_reliable.append(1)
    #
    #         else:
    #             s = self.unreliable_time[i].seconds
    #             ms = self.unreliable_time[i].microseconds
    #
    #             latency.append(f"{s}.{ms}")
    #             is_reliable.append(0)
    #
    #     # Collect and transpose data
    #     data = zip(*[is_reliable, latency])
    #
    #     with open("metrics.csv", "a", newline=" ") as file:
    #         writer = csv.writer(file)
    #         writer.writerows(data)


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
