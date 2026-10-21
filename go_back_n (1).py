import time, threading, os
from common import *

CHUNK = 1024


def get_rto():
    """Fixed RTO for now. Replace with the adaptive RTO later."""
    return 0.2


class Sender:
    def __init__(self, channel, window=8, chunk=CHUNK, max_stalls=50):
        self.ch, self.window, self.chunk = channel, window, chunk
        self.max_stalls = max_stalls

    def send_file(self, path):
        # 1. Read the whole file into a list of chunks
        chunks = []
        with open(path, "rb") as f:
            while True:
                d = f.read(self.chunk)
                if not d:
                    break
                chunks.append(d)
        total = len(chunks)                # seq 0..total-1 are DATA, seq 'total' is FIN
        n_pkts = total + 1

        def make(seq):
            if seq < total:
                return make_packet(DATA, seq, chunks[seq])
            return make_packet(FIN, seq)

        stats = {"sent": 0, "retx": 0, "bytes": sum(map(len, chunks)),
                 "elapsed": 0.0, "goodput": 0.0}
        t0 = time.time()
        base, next_seq, timer, stalls = 0, 0, 0.0, 0

        while base < n_pkts:
            # 2. Fill the window: send new packets while there is room
            while next_seq < base + self.window and next_seq < n_pkts:
                self.ch.send(make(next_seq))
                stats["sent"] += 1
                if base == next_seq:
                    timer = time.time()    # timer runs for the oldest unACKed packet
                next_seq += 1

            # 3. Wait for an ACK, but only until the timer would expire
            wait = timer + get_rto() - time.time()
            raw = self.ch.recv(max(wait, 0.001))
            if raw:
                p = parse_packet(raw)
                if p and p[0] == ACK and p[1] > base:   # cumulative ACK: got all seq < p[1]
                    base = p[1]
                    timer = time.time()
                    stalls = 0

            # 4. Timeout: resend EVERYTHING from base up to next_seq-1
            if base < next_seq and time.time() - timer >= get_rto():
                stalls += 1
                if stalls > self.max_stalls:
                    if base >= total:   # only the FIN is unACKed: all data was delivered
                        break
                    raise TimeoutError(f"stuck at seq {base}")
                for s in range(base, next_seq):
                    self.ch.send(make(s))
                    stats["sent"] += 1
                    stats["retx"] += 1
                timer = time.time()

        stats["elapsed"] = time.time() - t0
        stats["goodput"] = stats["bytes"] / stats["elapsed"] if stats["elapsed"] else 0
        return stats


class Receiver:
    def __init__(self, channel, linger=1.0):
        self.ch, self.linger = channel, linger

    def receive_file(self, out_path, idle_timeout=10.0):
        expected = 0
        with open(out_path, "wb") as out:
            while True:
                raw = self.ch.recv(idle_timeout)
                if raw is None:
                    raise TimeoutError("sender went silent")
                p = parse_packet(raw)
                if p is None:
                    continue                       # corrupt: drop silently
                ptype, seq, payload = p
                if seq == expected:                # only accept the next in-order packet
                    if ptype == DATA:
                        out.write(payload)
                    expected += 1
                # ACK = "next seq I expect". Out-of-order packets are discarded.
                self.ch.send(make_packet(ACK, expected))
                if ptype == FIN and seq == expected - 1:
                    self._linger(expected)
                    return

    def _linger(self, expected):
        """Re-ACK retransmitted packets in case our last ACK was lost."""
        end = time.time() + self.linger
        while time.time() < end:
            raw = self.ch.recv(end - time.time())
            if raw and parse_packet(raw):
                self.ch.send(make_packet(ACK, expected))


def run_test(loss, window, seed=1, size=50_000):
    src, dst = f"/tmp/gbn_src_{seed}.bin", f"/tmp/gbn_dst_{seed}.bin"
    with open(src, "wb") as f:
        f.write(os.urandom(size))
    a, b = ("127.0.0.1", 9001), ("127.0.0.1", 9002)
    s_ch = LossyChannel(a, b, loss, seed)
    r_ch = LossyChannel(b, a, loss, seed + 100)
    rx = Receiver(r_ch)
    t = threading.Thread(target=rx.receive_file, args=(dst,))
    t.start()
    stats = Sender(s_ch, window=window).send_file(src)
    t.join()
    s_ch.close(); r_ch.close()
    ok = sha256_file(src) == sha256_file(dst)
    print(f"window={window} loss={loss:.0%} hash_ok={ok} sent={stats['sent']} "
          f"retx={stats['retx']} time={stats['elapsed']:.2f}s "
          f"goodput={stats['goodput']/1024:.1f} KB/s")
    return ok


if __name__ == "__main__":
    for window in (1, 8):
        for loss in (0.0, 0.05, 0.2):
            assert run_test(loss, window)
