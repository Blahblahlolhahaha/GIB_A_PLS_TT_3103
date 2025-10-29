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
    total_tries = 0
    start = time.perf_counter_ns() * (pow(10, -9))
    for buffer in buffers:
        sent, tries, latency = sender.send("127.0.0.1", 5555, buffer)
        total_tries += tries
        if sent:
            total_latency += latency
            total_size += len(buffer)
            lost += tries - 1
        else:
            lost += tries
    end = time.perf_counter_ns() * (pow(10, -9))
    duration = end - start
    tp = total_size / duration
    pdr = 1 - (lost/total_tries)
    print(f"TP: {tp} bytes/s")
    print(f"PDR: {pdr*100}%")
get_performance_metrics()
