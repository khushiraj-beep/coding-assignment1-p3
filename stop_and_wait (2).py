import time, threading, os
from common import *

CHUNK = 1024


def get_rto():
    """Fixed RTO for now. Replace with the adaptive RTO (Jacobson/Karels) later."""
    return 0.2


class Sender:
    def __init__(self, channel, chunk=CHUNK, max_retries=50):
        self.ch, self.chunk, self.max_retries = channel, chunk, max_retries

    def send_file(self, path):
        stats = {"sent": 0, "retx": 0, "bytes": 0, "elapsed": 0.0, "goodput": 0.0}
        t0, seq = time.time(), 0
        with open(path, "rb") as f:
            while True:
                data = f.read(self.chunk)
                if not data:
                    break
                self._send_reliable(DATA, seq, data, stats)
                stats["bytes"] += len(data)
                seq ^= 1                      # alternating bit
        self._send_reliable(FIN, seq, b"", stats)
        stats["elapsed"] = time.time() - t0
        stats["goodput"] = stats["bytes"] / stats["elapsed"] if stats["elapsed"] else 0
        return stats

    def _send_reliable(self, ptype, seq, payload, stats):
        pkt = make_packet(ptype, seq, payload)
        for attempt in range(self.max_retries):
            self.ch.send(pkt)
            stats["sent"] += 1
            if attempt > 0:
                stats["retx"] += 1
            deadline = time.time() + get_rto()
            while True:
                remaining = deadline - time.time()
                if remaining <= 0:
                    break                      # timeout -> retransmit
                raw = self.ch.recv(remaining)
                if raw is None:
                    break
                p = parse_packet(raw)
                if p and p[0] == ACK and p[1] == seq:
                    return                     # correct ACK
                # corrupt / wrong ACK: ignore, keep waiting until timeout
        raise TimeoutError(f"no ACK for seq {seq} after {self.max_retries} tries")


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
                    continue                   # corrupt: drop silently
                ptype, seq, payload = p
                if seq == expected:
                    if ptype == FIN:
                        self.ch.send(make_packet(ACK, seq))
                        self._linger(seq)
                        return
                    out.write(payload)
                    expected ^= 1
                # new or duplicate: always ACK the seq we received
                self.ch.send(make_packet(ACK, seq))

    def _linger(self, fin_seq):
        """Re-ACK retransmitted FINs in case our final ACK was lost."""
        end = time.time() + self.linger
        while time.time() < end:
            raw = self.ch.recv(end - time.time())
            p = parse_packet(raw) if raw else None
            if p and p[0] == FIN:
                self.ch.send(make_packet(ACK, p[1]))


def run_test(loss, seed=1, size=50_000):
    src, dst = f"/tmp/src_{seed}.bin", f"/tmp/dst_{seed}.bin"
    with open(src, "wb") as f:
        f.write(os.urandom(size))
    a, b = ("127.0.0.1", 9001), ("127.0.0.1", 9002)
    s_ch = LossyChannel(a, b, loss, seed)
    r_ch = LossyChannel(b, a, loss, seed + 100)
    rx = Receiver(r_ch)
    t = threading.Thread(target=rx.receive_file, args=(dst,))
    t.start()
    stats = Sender(s_ch).send_file(src)
    t.join()
    s_ch.close(); r_ch.close()
    ok = sha256_file(src) == sha256_file(dst)
    print(f"loss={loss:.0%} hash_ok={ok} sent={stats['sent']} "
          f"retx={stats['retx']} time={stats['elapsed']:.2f}s "
          f"goodput={stats['goodput']/1024:.1f} KB/s")
    return ok


if __name__ == "__main__":
    for loss in (0.0, 0.05, 0.2):
        assert run_test(loss)
