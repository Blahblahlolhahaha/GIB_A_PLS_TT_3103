import socket
import threading
import time
import zlib
from collections import deque
from typing import Optional, Tuple, List

"""
Hybrid UDP transport (H-UDP) with:
  - Reliable channel (0): retransmission (timer-based), in-order delivery, skip-after-t
  - Unreliable channel (1): no retransmit, freshest-wins, no reordering
  - ACK control type (2): internal control, not delivered to the app
  - No callbacks; apps poll with recv(timeout_ms).
  - Uses selective repeat instead of go back n

Header layout (big-endian), 11 Bytes: | Channel (1B) | Sequence (2B) | Timestamp ms (4B) | CRC32 (4B) |
"""

CH_RELIABLE = 0
CH_UNRELIABLE = 1
CH_ACK = 2

SEQ_MOD = 65536
HEADER_SIZE = 1 + 2 + 4 + 4  # 11 bytes

def now_ms() -> int:
    return int(time.time() * 1000)

class GameNetAPI:
    def __init__(
        self,
        local_addr: Tuple[str, int],
        peer_addr: Tuple[str, int],
        retry_wait_duration_ms: int = 200
    ):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(local_addr)
        self.sock.settimeout(0.2)
        self.peer_addr = peer_addr

        # rx: receive, retx: retransmit
        self.retry_wait_duration_ms = retry_wait_duration_ms
        self.running = False
        self.rx_thread = None
        self.retx_thread = None

        # reliable send
        self.send_lock = threading.Lock()
        self.next_reliable_seq = 0
        self.pkts_pending_ack = {}  # seq -> {payload, send_timestamp, last_tx, retries}
        self.last_unreliable_seq_tx = None  # TX-side seq for unreliable sends

        # reliable recv
        self.recv_lock = threading.Lock()
        self.expected_seq = 0
        self.buffer = {}  # seq -> (ts_ms, payload)
        self.gap_since_ms: Optional[int] = None

        # unreliable recv
        self.last_unreliable_seq_rx = None

        # messages ready to be delivered to the application: (channel, seq, ts_ms, payload)
        self.app_recv_q = deque()
        self.app_recv_q_lock = threading.Lock()


    def start(self):
        self.running = True
        self.rx_thread = threading.Thread(target=self._rx_worker, daemon=True)
        self.rx_thread.start()
        self.retx_thread = threading.Thread(target=self._retx_worker, daemon=True)
        self.retx_thread.start()

    def close(self):
        self.running = False
        try:
            self.sock.close()
        except Exception:
            print("Failed to close sock")
            pass

    def send(self, payload: bytes, reliable: bool = True) -> int:
        return self._send_reliable(payload) if reliable else self._send_unreliable(payload)

    def _send_reliable(self, payload: bytes) -> int:
        with self.send_lock:
            seq = self.next_reliable_seq
            self.next_reliable_seq = (self.next_reliable_seq + 1) % SEQ_MOD

            pkt = self._build_packet(CH_RELIABLE, seq, payload)
            self.sock.sendto(pkt, self.peer_addr)
            now = now_ms()

            # Add to packet to pending ack queue
            self.pkts_pending_ack[seq] = {
                "payload": payload,
                "send_timestamp": now,
                "last_tx": now,
                "retries": 0,
            }
            return seq

    def _send_unreliable(self, payload: bytes) -> int:
        with self.send_lock:
            seq = 0 if self.last_unreliable_seq_tx is None else (self.last_unreliable_seq_tx + 1) % SEQ_MOD
            self.last_unreliable_seq_tx = seq
            pkt = self._build_packet(CH_UNRELIABLE, seq, payload)
            self.sock.sendto(pkt, self.peer_addr)
            return seq

    def recv(self, timeout_ms: int = 100) -> List[Tuple[int, int, int, bytes]]:
        # Polls for delivered msgs and returns a list of (channel, seq, timestamp_ms, payload)
        end_time = now_ms() + max(0, timeout_ms)

        received_packets = []
        while now_ms() < end_time:
            with self.app_recv_q_lock:
                if self.app_recv_q:
                    received_packets.append(self.app_recv_q.popleft())
                    break # return as soon as one packet arrives
            time.sleep(0.005)

        # Drain a small batch of requests (batched to reduce syscalls)
        with self.app_recv_q_lock:
            while self.app_recv_q and len(received_packets) < 64:
                received_packets.append(self.app_recv_q.popleft())
        return received_packets

    def _build_packet(self, chan: int, seq: int, payload: bytes) -> bytes:
        timestamp = now_ms()
        head_without_crc = chan.to_bytes(1, "big") + seq.to_bytes(2, "big") + timestamp.to_bytes(4, "big")
        crc = zlib.crc32(head_without_crc + payload) & 0xFFFFFFFF
        header = head_without_crc + crc.to_bytes(4, "big")
        return header + payload

    def _parse_packet(self, data: bytes) -> Tuple[int, int, int,  bytes]:
        if len(data) < HEADER_SIZE:
            raise ValueError("packet is too small (packet size < header size)")

        ch = int.from_bytes(data[0:1], "big")
        seq = int.from_bytes(data[1:3], "big")
        timestamp = int.from_bytes(data[3:7], "big")
        crc = int.from_bytes(data[7:11], "big")
        payload = data[11:]

        computed_crc = zlib.crc32(data[0:7] + payload) & 0xFFFFFFFF
        if computed_crc != crc:
            raise ValueError("bad crc")

        return ch, seq, timestamp, payload

    def _rx_worker(self):
        while self.running:
            try:
                data, _ = self.sock.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError:
                break

            recv_timestamp = now_ms()
            try:
                ch, seq, send_timestamp, payload = self._parse_packet(data)
            except Exception as e:
                print(f"Dropped bad packet with error: {e}")
                continue

            if ch == CH_ACK:
                # Consume ACK (not delivered to app)
                with self.send_lock:
                    packet_awaiting_ack = self.pkts_pending_ack.pop(seq, None)
                    if packet_awaiting_ack:
                        rtt = recv_timestamp - packet_awaiting_ack["send_timestamp"]
                        print("ack", "rx", CH_RELIABLE, seq, packet_awaiting_ack["send_timestamp"], recv_timestamp, rtt, packet_awaiting_ack["retries"], 0)
                continue

            if ch == CH_RELIABLE:
                # ACK it
                self._send_ack(seq)
                print("data", "rx", CH_RELIABLE, seq, send_timestamp, recv_timestamp, recv_timestamp - send_timestamp, 0, len(payload))
                self._handle_reliable_rx(seq, send_timestamp, payload)
            elif ch == CH_UNRELIABLE:
                # retain only freshest data
                to_deliver_to_app = False
                if self.last_unreliable_seq_rx is None:
                    to_deliver_to_app = True
                else:
                    diff = (seq - self.last_unreliable_seq_rx + SEQ_MOD) % SEQ_MOD
                    if 0 < diff < SEQ_MOD // 2:
                        to_deliver_to_app = True
                if to_deliver_to_app:
                    self.last_unreliable_seq_rx = seq
                    with self.app_recv_q_lock:
                        self.app_recv_q.append((CH_UNRELIABLE, seq, send_timestamp, payload))
                else:
                    print(f"UNRELIABLE CHANNEL: dropped old seq={seq}")
            else:
                print(f"Unknown channel: {ch}")

    def _is_seq_behind(self, a: int, b: int) -> bool:
        # True if 'a' is older than 'b' in modulo space (within half-range)
        return 0 < (b - a + SEQ_MOD) % SEQ_MOD < (SEQ_MOD // 2)

    def _handle_reliable_rx(self, seq: int, ts_ms: int, payload: bytes):
        # buffer out of order packets
        # deliver in order at expected_seq
        with self.recv_lock:
            # drop late arrivals for already skipped heads
            if self._is_seq_behind(seq, self.expected_seq):
                return

            # Duplicate data detected. We drop it as we use a (modified) selective repeat.
            if seq in self.buffer:
                return

            # Buffer this out-of-order or head candidate
            self.buffer[seq] = (ts_ms, payload)

            while True:
                # If the current head-of-line is present, deliver it and advance
                if self.expected_seq in self.buffer:
                    head_timestamp_ms, head_payload = self.buffer.pop(self.expected_seq)
                    with self.app_recv_q_lock:
                        self.app_recv_q.append((CH_RELIABLE, self.expected_seq, head_timestamp_ms, head_payload))

                    # Delivered head, so we clear gap timer and move expected forward
                    self.gap_since_ms = None
                    self.expected_seq = (self.expected_seq + 1) % SEQ_MOD
                    continue

                # Missing head-of-line (gap)
                now = now_ms()
                if self.gap_since_ms is None:
                    # Start gap timer
                    self.gap_since_ms = now
                    break
                else:
                    # If we've waited long enough, skip the missing head to keep moving, we expect to receive
                    # the missing packet later handled by retransmit worker.
                    if now - self.gap_since_ms >= self.retry_wait_duration_ms:
                        print(f"RELIABLE skip seq={self.expected_seq}")
                        self.expected_seq = (self.expected_seq + 1) % SEQ_MOD
                        self.gap_since_ms = now # restart gap timer for the new head
                        continue
                    break

    def _send_ack(self, seq: int):
        pkt = self._build_packet(CH_ACK, seq, b"")
        self.sock.sendto(pkt, self.peer_addr)

    def _retx_worker(self):
        while self.running:
            now = now_ms()
            to_retx = []
            with self.send_lock:
                for seq, ent in list(self.pkts_pending_ack.items()):
                    if now - ent["last_tx"] >= self.retry_wait_duration_ms:
                        to_retx.append((seq, ent))

            for seq, ent in to_retx:
                pkt = self._build_packet(CH_RELIABLE, seq, ent["payload"])
                try:
                    self.sock.sendto(pkt, self.peer_addr)
                except OSError:
                    return
                now2 = now_ms()
                # Update bookkeeping under lock in case ACK popped it simultaneously
                with self.send_lock:
                    cur = self.pkts_pending_ack.get(seq)
                    if cur is not None:
                        cur["last_tx"] = now2
                        cur["retries"] += 1
                        retries_print = cur["retries"]
                        send_ts_print = cur["send_timestamp"]
                    else:
                        # entry was ACKed and removed, skip printing
                        retries_print = None
                        send_ts_print = None
                if retries_print is not None:
                    print("data_retx", "tx", CH_RELIABLE, seq, send_ts_print, "", "", retries_print, len(ent["payload"]))
            time.sleep(0.01)

