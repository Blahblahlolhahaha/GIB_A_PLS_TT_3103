import random

from datetime import datetime


class Sender:
    def __init__(self) -> None:
        # TODO: Instantiate GameNetAPI

        self.seqNo = 0

    def _update_seqNo(self):
        # 2B max --> 2^16 - 1 = 65535
        self.seqNo = (self.seqNo + 1) % 65535

    def _checksum(self, packet):
        return

    def _build_packet(self):
        # TODO: Generate packet
        # Packet specifications:
        #   Channel Type - 1B: 0/1 for Reliable / Unreliable
        #   SeqNo - 2B
        #   Timestamp - 4B
        #   Checksum - 2B
        #   Total: 9B

        is_reliable = random.choice([True, False])
        timestamp = datetime.now()

        return

    def send(self):
        packet = self._build_packet()

        # TODO: Pass to GameNetAPI

        # After sending, update seqNo for next packet
        self._update_seqNo()

    def receive(self):
        # TODO: Listen for  ACK

        # TODO: Collect metrics and report (write to csv? Check with Jess)
        return


if __name__ == "__main__":
    sender = Sender()
