import atexit
import sys
from gamenet_api import GameNetAPI, CH_RELIABLE, CH_UNRELIABLE


class Receiver:
    def __init__(self, metric: bool) -> None:
        self.addr = "localhost"
        self.port = 8001

        self.dest_addr = "localhost"
        self.dest_port = 8000

        self.gamenet = GameNetAPI(
            (self.addr, self.port), (self.dest_addr, self.dest_port), metric = metric
        )
        atexit.register(self.gamenet.on_exit)

    def start(self):
        self.gamenet.start()
        while self.gamenet.running:
            packets = self.gamenet.recv(timeout_ms=200)

            for data in packets:
                ch, seq, send_timestamp, payload, recv_timestamp, half_rtt, retries = data

                if ch == CH_RELIABLE:
                    reliable_str = "reliable"
                else:
                    reliable_str = "unreliable"

                rtt = 2 * half_rtt

                # Logging as requested in the specs
                print(
                        f"Received packet with following details: \n    seqNo: {seq} \n" + 
                        f"    Channel Type: {reliable_str} \n    Retries: {retries} \n"
                        f"    Sent at {send_timestamp} \n    Received at: {recv_timestamp} \n"
                        f"    Payload: {payload} \n    Estimated RTT: {rtt}"
                )
                print()


if __name__ == "__main__":
    if "-m" in sys.argv:
        is_metric_mode = True
    else:
        is_metric_mode = False

    receiver = Receiver(is_metric_mode)
    receiver.start()
