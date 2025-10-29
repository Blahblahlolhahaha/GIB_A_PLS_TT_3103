import sender
import random
import time
import json

def generate_testcase(n : int) -> list:
    res = []
    for i in range(n):
        x = random.randint(-255,255)
        y = random.randint(-255,255)
        res.append(json.dumps({"x": x, "y": y}).encode())
    return res

def get_performance_metrics():
    buffers = generate_testcase(1000)
    total_size = 0
    total_latency = 0
    lost = 0
    start = time.perf_counter_ns() * (pow(10, -9))
    for buffer in buffers:
        sent, latency = sender.send("127.0.0.1", 5555, buffer)
        if sent:
            total_latency += latency
            total_size += len(buffer)
        else:
            lost += 1

    end = time.perf_counter_ns() * (pow(10, -9))
    duration = end - start
    tp = total_size / duration
    pdr = 1 - (lost/len(buffers))
    print(f"TP: {tp} bytes/s")
    print(f"PDR: {pdr*100}%")
get_performance_metrics()
