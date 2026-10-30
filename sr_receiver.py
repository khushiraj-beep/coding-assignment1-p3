
import argparse
import hashlib
import os
import socket
import time

from packet import encode_packet, decode_packet

HOST = "127.0.0.1"
PORT = 5000
OUTPUT_FILE = "received_sample.txt"

WINDOW_SIZE = 4
END_ACK_LINGER = 10.0


def receive_file(host=HOST, port=PORT, output_file=OUTPUT_FILE):
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((host, port))

    received_chunks = {}
    transfer_id = None
    total_chunks = None
    sender_address = None
    base = 1

    completed = False
    end_ack = None
    linger_deadline = None

    print(f"Selective Repeat receiver listening on {host}:{port}")

    try:
        while True:
            if completed:
                remaining = linger_deadline - time.monotonic()
                if remaining <= 0:
                    break
                server.settimeout(remaining)

            try:
                raw_data, address = server.recvfrom(65535)
            except socket.timeout:
                if completed:
                    break
                continue

            try:
                packet = decode_packet(raw_data)
            except (ValueError, KeyError, TypeError) as error:
                print(f"Ignored invalid packet: {error}")
                continue

            current_id = packet["transfer_id"]

            if transfer_id is None:
                transfer_id = current_id
                sender_address = address

            if current_id != transfer_id or address != sender_address:
                continue

            packet_type = packet["type"]
            seq = packet["seq_num"]

            # After completion, acknowledge repeated END packets.
            if completed:
                if packet_type == "END" and seq == total_chunks:
                    server.sendto(encode_packet(end_ack), address)
                    print("Repeated END received; END ACK resent.")
                continue

            if packet_type == "DATA":
                if not isinstance(seq, int) or seq < 1:
                    continue

                if total_chunks is not None and seq > total_chunks:
                    continue

                # Accept packets within the receiver window.
                # Old duplicates are ACKed again.
                if seq < base:
                    print(f"Duplicate old chunk {seq}")
                elif seq >= base + WINDOW_SIZE:
                    print(f"Chunk {seq} outside receiver window")
                    continue
                else:
                    if seq not in received_chunks:
                        received_chunks[seq] = packet["payload"]
                        print(f"Received chunk {seq}")
                    else:
                        print(f"Duplicate chunk {seq}")

                    # Advance receiver base over contiguous packets.
                    while base in received_chunks:
                        base += 1

                ack = {
                    "type": "ACK",
                    "transfer_id": transfer_id,
                    "seq_num": 0,
                    "ack_num": seq,
                    "payload": b"",
                }
                server.sendto(encode_packet(ack), address)

            elif packet_type == "END":
                if not isinstance(seq, int) or seq < 0:
                    continue

                if total_chunks is not None and seq != total_chunks:
                    continue

                if any(n > seq for n in received_chunks):
                    continue

                total_chunks = seq

                missing = [
                    n for n in range(1, total_chunks + 1)
                    if n not in received_chunks
                ]

                if missing:
                    print(f"Waiting for missing chunks: {missing}")
                    continue

                with open(output_file, "wb") as output:
                    for n in range(1, total_chunks + 1):
                        output.write(received_chunks[n])

                digest = hashlib.sha256()
                with open(output_file, "rb") as output:
                    for block in iter(lambda: output.read(8192), b""):
                        digest.update(block)

                print(f"File saved: {output_file}")
                print(f"Chunks received: {total_chunks}")
                print(
                    f"Received file size: "
                    f"{os.path.getsize(output_file)} bytes"
                )
                print(f"SHA-256: {digest.hexdigest()}")

                end_ack = {
                    "type": "ACK",
                    "transfer_id": transfer_id,
                    "seq_num": total_chunks + 1,
                    "ack_num": total_chunks,
                    "payload": b"",
                }

                server.sendto(encode_packet(end_ack), address)
                completed = True
                linger_deadline = time.monotonic() + END_ACK_LINGER

                print("END acknowledged. Waiting for possible retransmissions.")

    except KeyboardInterrupt:
        print("\nReceiver stopped.")
    finally:
        server.close()

    if completed:
        print("Transfer complete. Receiver stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Selective Repeat UDP receiver"
    )
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--output", default=OUTPUT_FILE)
    args = parser.parse_args()

    receive_file(args.host, args.port, args.output)
