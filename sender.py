import random


class Sender:
    def __init__(self) -> None:
        # TODO: Instantiate GameNetAPI
        pass

    def send(self):
        # TODO: What parameters to define?
        is_reliable = random.choice([True, False])

        # TODO: Call GameNetAPI to build and send packet to Receiver

        return

    def receive(self):
        # TODO: Listen for  ACK

        # TODO: Collect metrics and report (write to csv? Check with Jess)
        return


if __name__ == "__main__":
    sender = Sender()
