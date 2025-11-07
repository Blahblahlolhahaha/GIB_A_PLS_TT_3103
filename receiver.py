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
        packet_count = 0
        
        print("=" * 80)
        print("RECEIVER LOG - Packet Reception Details")
        print("=" * 80)
        print(f"{'Pkt#':<6} {'SeqNo':<7} {'Channel':<12} {'Retries':<8} "
              f"{'SendTime(ms)':<15} {'RecvTime(ms)':<15} {'RTT(ms)':<10} {'Size':<6}")
        print("-" * 80)
        
        while self.gamenet.running:
            packets = self.gamenet.recv(timeout_ms=200)

            for data in packets:
                ch, seq, send_timestamp, payload, recv_timestamp, half_rtt, retries = data
                packet_count += 1

                if ch == CH_RELIABLE:
                    channel_str = "RELIABLE"
                else:
                    channel_str = "UNRELIABLE"

                rtt = 2 * half_rtt

                # Compact tabular logging format
                print(f"{packet_count:<6} {seq:<7} {channel_str:<12} {retries:<8} "
                      f"{send_timestamp:<15} {recv_timestamp:<15} {rtt:<10.2f} {len(payload):<6}")
                
                # Detailed verbose logging (can be commented out for cleaner output)
                if False:  # Set to True for verbose logging
                    print(
                        f"\n  Packet Details:\n"
                        f"    Packet Number:  {packet_count}\n"
                        f"    Sequence No:    {seq}\n"
                        f"    Channel Type:   {channel_str}\n"
                        f"    Retransmits:    {retries}\n"
                        f"    Send Timestamp: {send_timestamp} ms\n"
                        f"    Recv Timestamp: {recv_timestamp} ms\n"
                        f"    Estimated RTT:  {rtt:.2f} ms\n"
                        f"    Payload Size:   {len(payload)} bytes\n"
                        f"    Payload:        {payload[:50]}{'...' if len(payload) > 50 else ''}\n"
                    )


if __name__ == "__main__":
    if "-m" in sys.argv:
        is_metric_mode = True
    else:
        is_metric_mode = False

    receiver = Receiver(is_metric_mode)
    receiver.start()
