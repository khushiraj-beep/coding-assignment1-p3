import socket, random, hashlib
from packet import encode_packet, decode_packet   # Ankita's packet format

DATA, ACK, FIN = 0, 1, 2
_NAME = {DATA: "DATA", ACK: "ACK", FIN: "END"}
_CODE = {v: k for k, v in _NAME.items()}


def make_packet(ptype, seq, payload=b""):
    """Build a packet using Ankita's format. For ACKs, 'seq' is stored in ack_num."""
    if ptype == ACK:
        return encode_packet({"type": "ACK", "seq_num": 0, "ack_num": seq, "payload": b""})
    return encode_packet({"type": _NAME[ptype], "seq_num": seq, "ack_num": None, "payload": payload})


def parse_packet(raw):
    """Returns (ptype, seq, payload) or None if corrupt/invalid. For ACKs, seq = ack_num."""
    try:
        p = decode_packet(raw)
    except (ValueError, KeyError, TypeError, UnicodeDecodeError):
        return None
    ptype = _CODE[p["type"]]
    if ptype == ACK:
        if p["ack_num"] is None:
            return None
        return ACK, p["ack_num"], b""
    return ptype, p["seq_num"], p["payload"]


class UdpChannel:
    """Swap for the team's emulator later; keep send()/recv()."""
    def __init__(self, local, remote):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.bind(local)
        self.remote = remote

    def send(self, pkt):
        self.s.sendto(pkt, self.remote)

    def recv(self, timeout):
        self.s.settimeout(max(timeout, 0.001))
        try:
            return self.s.recvfrom(65535)[0]
        except socket.timeout:
            return None

    def close(self):
        self.s.close()


class LossyChannel(UdpChannel):
    """Temporary stand-in for the emulator: seeded random packet loss."""
    def __init__(self, local, remote, loss=0.0, seed=0):
        super().__init__(local, remote)
        self.loss, self.rng = loss, random.Random(seed)

    def send(self, pkt):
        if self.rng.random() >= self.loss:
            super().send(pkt)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(65536), b""):
            h.update(blk)
    return h.hexdigest()
