import matplotlib.pyplot as plt
import csv
import numpy as np

HEADERS = ["Throughput", "Packet Delivery Ratio","Latency", "Jitter"]

def main():
    reliable_low = []
    reliable_high = []
    unreliable_low = []
    unreliable_high = []

    with open("reli.csv","r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample = dict()
            for x in HEADERS:
                sample[x] = float(row[x])
            if row["Channel"] == "1":
                reliable_high.append(sample)
            else:
                reliable_low.append(sample)

    with open("unreli.csv","r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample = dict()
            for x in HEADERS:
                sample[x] = float(row[x])
            if row["Channel"] == "1":
                unreliable_high.append(sample)
            else:
                unreliable_low.append(sample)
    for x in HEADERS:
        print(f"Average {x} (Reliable, low loss): {np.mean([y[x] for y in reliable_low])}")
        print(f"Average {x} (Reliable, high loss): {np.mean([y[x] for y in reliable_high])}")
        print(f"Average {x} (Unreliable, low loss): {np.mean([y[x] for y in unreliable_low])}")
        print(f"Average {x} (Unreliable, high loss): {np.mean([y[x] for y in unreliable_high])}\n")     
        plt.bar(
            ["Reliable, low loss", "Reliable, high loss", "Unreliable, low loss", "Unreliable, high loss"],
            [np.mean([y[x] for y in reliable_low]), np.mean([y[x] for y in reliable_high]), np.mean([y[x] for y in unreliable_low]), np.mean([y[x] for y in unreliable_high])],
            color=["skyblue", "violet", "pink", "red"]
        )           
        plt.xlabel("Channel, environment")
        plt.ylabel("Value")
        plt.title(f"Average {x}")
        plt.show()

main()