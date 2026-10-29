
import argparse
import os
import socket

from packet import encode_packet, decode_packet

HOST = "127.0.0.1"
PORT = 5000


def receive_file(host, port, protocol, output_file):
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((host, port))
    server.settimeout(10)

    expected = 1
    chunks = {}
    transfer_id = None
    sender_address = None

    print(f"{protocol} receiver listening on {host}:{port}")

    try:
        while True:
            try:
                raw, address = server.recvfrom(65535)
            except socket.timeout:
                print("Receiver timed out waiting for packets.")
                return

            try:
                packet = decode_packet(raw)
            except (ValueError, KeyError, TypeError):
                continue

            tid = packet.get("transfer_id")
            if not tid:
                continue

            if transfer_id is None:
                transfer_id = tid
                sender_address = address

            if tid != transfer_id or address != sender_address:
                continue

            kind = packet.get("type")
            seq = packet.get("seq_num")

            if kind == "DATA" and isinstance(seq, int):
                if protocol == "SW":
                    if seq == expected:
                        chunks[seq] = packet["payload"]
                        expected += 1
                    ack_num = seq if seq < expected else expected - 1

                else:  # GBN: accept only the next in-order packet
                    if seq == expected:
                        chunks[seq] = packet["payload"]
                        expected += 1
                    ack_num = expected - 1

                ack = {
                    "type": "ACK",
                    "transfer_id": transfer_id,
                    "seq_num": 0,
                    "ack_num": ack_num,
                    "payload": b"",
                }
                server.sendto(encode_packet(ack), address)

            elif kind == "END" and isinstance(seq, int):
                missing = [n for n in range(1, seq + 1) if n not in chunks]

                if missing:
                    # END is not acknowledged until every chunk is present.
                    continue

                with open(output_file, "wb") as f:
                    for n in range(1, seq + 1):
                        f.write(chunks[n])

                end_ack = {
                    "type": "ACK",
                    "transfer_id": transfer_id,
                    "seq_num": seq + 1,
                    "ack_num": seq,
                    "payload": b"",
                }
                server.sendto(encode_packet(end_ack), address)

                print(f"Saved {os.path.abspath(output_file)}")
                print(f"Chunks received: {seq}")
                print(f"Size: {os.path.getsize(output_file)} bytes")
                return

    finally:
        server.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--protocol", choices=["SW", "GBN"], required=True)
    parser.add_argument("--output", default="received_arq.txt")
    args = parser.parse_args()

    receive_file(args.host, args.port, args.protocol, args.output)
