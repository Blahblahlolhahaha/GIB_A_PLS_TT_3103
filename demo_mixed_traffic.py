#!/usr/bin/env python3
"""
Demo script showing mixed reliable/unreliable traffic support.
This demonstrates that the sender can randomly tag packets as reliable or unreliable
as required by the assignment specification.
"""

import random
import string
import time
from gamenet_api import GameNetAPI, CH_RELIABLE, CH_UNRELIABLE

# Demo parameters
NUM_PACKETS = 20
RELIABLE_PROBABILITY = 0.6  # 60% reliable, 40% unreliable
PACKET_SIZE = 64
SEND_DELAY_MS = 100  # Send one packet every 100ms

def generate_payload(size: int = PACKET_SIZE) -> bytes:
    """Generate random payload of specified size."""
    valid_characters = string.ascii_letters + string.digits
    payload = "".join(random.choice(valid_characters) for _ in range(size))
    return payload.encode('utf-8')

def main():
    print("=" * 70)
    print("MIXED TRAFFIC DEMO - Random Reliable/Unreliable Packet Tagging")
    print("=" * 70)
    print(f"Sending {NUM_PACKETS} packets with {RELIABLE_PROBABILITY*100:.0f}% reliable probability")
    print(f"Packet size: {PACKET_SIZE} bytes")
    print(f"Send rate: {1000/SEND_DELAY_MS:.1f} packets/sec\n")
    
    # Initialize sender
    gamenet = GameNetAPI(
        local_addr=("localhost", 9000),
        peer_addr=("localhost", 9001),
        metric=False,
        retransmission_timeout_ms=50,
        gap_skip_timeout_ms=200
    )
    
    gamenet.start()
    
    reliable_count = 0
    unreliable_count = 0
    
    try:
        for i in range(NUM_PACKETS):
            payload = generate_payload()
            
            # Randomly decide if this packet should be reliable or unreliable
            is_reliable = random.random() < RELIABLE_PROBABILITY
            
            if is_reliable:
                channel_type = "RELIABLE"
                reliable_count += 1
            else:
                channel_type = "UNRELIABLE"
                unreliable_count += 1
            
            # Send packet with chosen reliability
            seq = gamenet.send(payload, reliable=is_reliable)
            
            # Log the transmission
            print(f"[TX] Packet #{i:02d} | SeqNo: {seq:5d} | Channel: {channel_type:10s} | "
                  f"Size: {len(payload):3d} bytes | Payload: {payload[:20].decode()}...")
            
            time.sleep(SEND_DELAY_MS / 1000.0)
        
        print("\n" + "=" * 70)
        print("TRANSMISSION SUMMARY")
        print("=" * 70)
        print(f"Total packets sent: {NUM_PACKETS}")
        print(f"Reliable packets:   {reliable_count} ({reliable_count/NUM_PACKETS*100:.1f}%)")
        print(f"Unreliable packets: {unreliable_count} ({unreliable_count/NUM_PACKETS*100:.1f}%)")
        print("\nThis demonstrates that the sender supports mixed traffic,")
        print("randomly tagging packets as reliable or unreliable as per spec.")
        print("=" * 70)
        
    finally:
        time.sleep(1)  # Allow time for final transmissions
        gamenet.close()

if __name__ == "__main__":
    main()
