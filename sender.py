import sys
import random
import threading
from gamenet_api import GameNetAPI, CH_RELIABLE, CH_UNRELIABLE

class Sender:
    def __init__(self, num_packets, reliability_probability) -> None:
        self.num_packets = num_packets
        self.reliability_probability = reliability_probability

        self.dest_addr = "localhost"
        self.dest_port = 8080

        self.buffers = []
        # TODO: Instantiate GameNetAPI

    def start(self):
        # Start up
        for i in range(self.num_packets):
            send_thread = threading.Thread(target=self.send)

            self.buffers.append((i, send_thread))
            send_thread.start()

        # TODO: Collect metrics and report (write to csv)
        # Metrics:
        #   - Reliable or not
        #   - Buffer size
        #   - Latency (If unsuccessful, latency = -1)

        # Shut down
        for buffer in self.buffers:
            i, send_thread = buffer
            send_thread.join()

    def send(self):
        """
        Calls GameNetAPI to build and send packet to Receiver (Each call = 1x packet to send)
        The GameNetAPI send() method should also return the ACK packet if received in the same function call?
            => Multithread the sending of each packet as seen in `start()`
        """

        is_reliable = True

        rdm_val = random.random()
        if rdm_val > self.reliability_probability:
            is_reliable = False

        # TODO: Call GameNetAPI with is_reliable, self.dest_addr, self.dest_port


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
