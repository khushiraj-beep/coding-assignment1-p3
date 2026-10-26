
import argparse
import hashlib
import os
import socket

from packet import encode_packet, decode_packet

HOST = "127.0.0.1"
PORT = 5000
OUTPUT_FILE = "received_sample.txt"


def receive_file(host=HOST, port=PORT, output_file=OUTPUT_FILE):
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((host, port))

    received_chunks = {}
    transfer_id = None
    total_chunks = None
    sender_address = None

    print(f"Selective Repeat receiver listening on {host}:{port}")

    try:
        while True:
            raw_data, address = server.recvfrom(65535)

            try:
                packet = decode_packet(raw_data)
            except ValueError as error:
                print(f"Ignored invalid packet: {error}")
                continue

            current_id = packet["transfer_id"]

            if transfer_id is None:
                transfer_id = current_id

            if current_id != transfer_id:
                continue

            if sender_address is None:
                sender_address = address

            if address != sender_address:
                continue

            packet_type = packet["type"]
            seq = packet["seq_num"]

            if packet_type == "DATA":
                if total_chunks is not None and seq > total_chunks:
                    continue

                if seq not in received_chunks:
                    received_chunks[seq] = packet["payload"]
                    print(f"Received chunk {seq}")
                else:
                    print(f"Duplicate chunk {seq}")

                ack = {
                    "type": "ACK",
                    "transfer_id": transfer_id,
                    "seq_num": 0,
                    "ack_num": seq,
                    "payload": b""
                }
                server.sendto(encode_packet(ack), address)

            elif packet_type == "END":
                total_chunks = seq

                if any(n > total_chunks for n in received_chunks):
                    total_chunks = None
                    continue

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
                print(f"Received file size: {os.path.getsize(output_file)} bytes")
                print(f"SHA-256: {digest.hexdigest()}")

                end_ack = {
                    "type": "ACK",
                    "transfer_id": transfer_id,
                    "seq_num": total_chunks + 1,
                    "ack_num": total_chunks,
                    "payload": b""
                }
                server.sendto(encode_packet(end_ack), address)
                print("END acknowledged. Transfer complete.")
                break

    except KeyboardInterrupt:
        print("\nReceiver stopped.")
    finally:
        server.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Selective Repeat UDP receiver"
    )
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--output", default=OUTPUT_FILE)
    args = parser.parse_args()

    receive_file(args.host, args.port, args.output)
