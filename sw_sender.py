
import argparse
import socket
import time

from packet import encode_packet, decode_packet

HOST = "127.0.0.1"
PORT = 5000
CHUNK_SIZE = 1024
MAX_RETRIES = 15
TRANSFER_ID = "sw-transfer"


def send_file(filename, host=HOST, port=PORT):
    with open(filename, "rb") as f:
        data = f.read()

    chunks = [
        data[i:i + CHUNK_SIZE]
        for i in range(0, len(data), CHUNK_SIZE)
    ]

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(0.5)
    client.bind(("0.0.0.0", 0))

    total = len(chunks)
    retransmissions = 0
    start = time.monotonic()

    try:
        for seq, chunk in enumerate(chunks, start=1):
            packet = {
                "type": "DATA",
                "transfer_id": TRANSFER_ID,
                "seq_num": seq,
                "ack_num": None,
                "payload": chunk,
            }
            encoded = encode_packet(packet)

            for attempt in range(MAX_RETRIES + 1):
                client.sendto(encoded, (host, port))

                try:
                    while True:
                        raw, _ = client.recvfrom(65535)
                        ack = decode_packet(raw)

                        if (
                            ack.get("type") == "ACK"
                            and ack.get("transfer_id") == TRANSFER_ID
                            and ack.get("ack_num") == seq
                        ):
                            break
                    break
                except socket.timeout:
                    if attempt == MAX_RETRIES:
                        raise TimeoutError(f"No ACK for packet {seq}")
                    retransmissions += 1

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
            try:
                while True:
                    raw, _ = client.recvfrom(65535)
                    ack = decode_packet(raw)
                    if (
                        ack.get("type") == "ACK"
                        and ack.get("transfer_id") == TRANSFER_ID
                        and ack.get("seq_num") == total + 1
                    ):
                        break
                break
            except socket.timeout:
                if attempt == MAX_RETRIES:
                    raise TimeoutError("No ACK for END")
                retransmissions += 1

        elapsed = time.monotonic() - start
        print(f"Protocol: SW")
        print(f"Transfer time: {elapsed:.3f} seconds")
        print(f"Retransmissions: {retransmissions}")

    finally:
        client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", nargs="?", default="sample.txt")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()
    send_file(args.filename, args.host, args.port)
