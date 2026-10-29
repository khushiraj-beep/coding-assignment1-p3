
import argparse
import socket
import time

from packet import encode_packet, decode_packet

HOST = "127.0.0.1"
PORT = 5000
CHUNK_SIZE = 1024
WINDOW_SIZE = 4
TIMEOUT = 0.5
MAX_RETRIES = 15
TRANSFER_ID = "gbn-transfer"


def send_file(filename, host=HOST, port=PORT):
    with open(filename, "rb") as f:
        data = f.read()

    chunks = [
        data[i:i + CHUNK_SIZE]
        for i in range(0, len(data), CHUNK_SIZE)
    ]
    total = len(chunks)

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.bind(("0.0.0.0", 0))
    client.settimeout(TIMEOUT)

    base = 1
    next_seq = 1
    retries = 0
    retransmissions = 0
    start = time.monotonic()

    def send_packet(seq):
        packet = {
            "type": "DATA",
            "transfer_id": TRANSFER_ID,
            "seq_num": seq,
            "ack_num": None,
            "payload": chunks[seq - 1],
        }
        client.sendto(encode_packet(packet), (host, port))

    try:
        while base <= total:
            # Fill the sending window.
            while next_seq <= total and next_seq < base + WINDOW_SIZE:
                send_packet(next_seq)
                print(f"Sent packet {next_seq}")
                next_seq += 1

            try:
                raw, _ = client.recvfrom(65535)
                ack = decode_packet(raw)

                if (
                    ack.get("type") == "ACK"
                    and ack.get("transfer_id") == TRANSFER_ID
                ):
                    ack_num = ack.get("ack_num")

                    # GBN ACKs cumulatively acknowledge packets.
                    if isinstance(ack_num, int) and base <= ack_num < next_seq:
                        base = ack_num + 1
                        retries = 0

            except socket.timeout:
                # If the oldest outstanding packet times out,
                # retransmit all outstanding packets.
                if base < next_seq:
                    if retries >= MAX_RETRIES:
                        raise TimeoutError(
                            f"Retry limit reached at packet {base}"
                        )

                    for seq in range(base, next_seq):
                        send_packet(seq)
                        retransmissions += 1
                        print(f"Retransmitted packet {seq}")

                    retries += 1

        # Send END and wait for its ACK.
        end = {
            "type": "END",
            "transfer_id": TRANSFER_ID,
            "seq_num": total,
            "ack_num": None,
            "payload": b"",
        }
        encoded_end = encode_packet(end)

        for attempt in range(MAX_RETRIES + 1):
            client.sendto(encoded_end, (host, port))
            deadline = time.monotonic() + TIMEOUT

            while time.monotonic() < deadline:
                client.settimeout(max(0.01, deadline - time.monotonic()))
                try:
                    raw, _ = client.recvfrom(65535)
                    ack = decode_packet(raw)

                    if (
                        ack.get("type") == "ACK"
                        and ack.get("transfer_id") == TRANSFER_ID
                        and ack.get("seq_num") == total + 1
                    ):
                        elapsed = time.monotonic() - start
                        print("Protocol: GBN")
                        print(f"Transfer time: {elapsed:.3f} seconds")
                        print(f"Retransmissions: {retransmissions}")
                        return
                except socket.timeout:
                    break
                except (ValueError, OSError):
                    continue

        raise TimeoutError("Receiver did not acknowledge END")

    finally:
        client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", nargs="?", default="sample.txt")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()
    send_file(args.filename, args.host, args.port)
