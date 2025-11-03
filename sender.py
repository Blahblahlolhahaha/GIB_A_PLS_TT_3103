import sys
import random
import threading


class Sender:
    def __init__(self, num_packets) -> None:
        self.num_packets = num_packets

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

        is_reliable = random.choice([True, False])

        # TODO: Call GameNetAPI with is_reliable, self.dest_addr, self.dest_port


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Expected 1 argument: number of packets to send")

    num_packets = int(sys.argv[1])

    sender = Sender(num_packets)
    sender.start()
