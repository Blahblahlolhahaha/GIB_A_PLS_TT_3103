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
                ch, seq, send_timestamp, payload = data

                if ch == CH_RELIABLE:
                    reliable_str = "reliable"
                else:
                    reliable_str = "unreliable"

                # TODO: Print logs showing SeqNo, ChannelType, Timestamp,
                #       Retransmissions, Packet Arrivals, RTT, etc
                # FIX: Get Retransmission count + RTT
                print(
                    f"Received packet with seqNo: {seq} from {reliable_str} channel, sent at {send_timestamp} with payload: {payload}"
                )


if __name__ == "__main__":
    receiver = Receiver("-m" in sys.argv)
    receiver.start()
