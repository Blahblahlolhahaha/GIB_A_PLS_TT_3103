import csv
import sender
import sender_unreliable
import random
import time
import json
import matplotlib

HEADERS = ["Throughput", "Packet Delivery Ratio","Latency", "Jitter"]
reli_res = []
unreli_res = []


def generate_testcase(n : int) -> list:
    res = []
    for i in range(n):
        x = random.randint(-255,255)
        y = random.randint(-255,255)
        res.append(json.dumps({"x": x, "y": y}).encode())
    return res

def get_performance_metrics(reliable: bool):
    buffers = generate_testcase(500)
    total_size = 0
    total_latency = 0
    latency_sq = 0
    lost = 0
    total_tries = 0
    success = 0
    start = time.perf_counter_ns() * (pow(10, -9))
    for buffer in buffers:
        if reliable:
            sent, tries, latency = sender.send("127.0.0.1", 5555, buffer)
        else:
            sent, tries, latency = sender_unreliable.send("127.0.0.1", 5555, buffer)
        total_tries += tries
        if sent:
            total_latency += latency
            #print(latency*1000)
            latency_sq += pow(latency * 1000, 2)
            total_size += len(buffer)
            success += 1
        else:
            lost += 1
    end = time.perf_counter_ns() * (pow(10, -9))
    duration = end - start
    tp = total_size / duration
    pdr = (1 - (lost/total_tries)) * 100
    latency_sq_mean = latency_sq/success
    avg_latency = total_latency * 1000 / success
    jitter = pow(latency_sq_mean - pow(avg_latency, 2), 0.5)
    
    if reliable:
        reli_res.append([tp, pdr, avg_latency, jitter])
    else:
        unreli_res.append([tp, pdr, avg_latency, jitter])

    #print(f"TP: {tp:.2f} bytes/s")
    #print(f"PDR: {pdr*100:.2f}%")
    #print(f"jitter: {jitter:.2f}ms")
    #print(f"Avg Latency: {total_latency*1000/success:.2f}ms")

for i in range(50):
    get_performance_metrics(True)
    get_performance_metrics(False)

reli_data = [HEADERS] + [x for x in reli_res]
unreli_data = [HEADERS] + [x for x in unreli_res]

with open("reli.csv","w",newline="") as f:
    writer = csv.writer(f)
    writer.writerows([HEADERS] + [x for x in reli_res])

with open("unreli.csv","w",newline="") as f:
    writer = csv.writer(f)
    writer.writerows([HEADERS] + [x for x in unreli_res])

