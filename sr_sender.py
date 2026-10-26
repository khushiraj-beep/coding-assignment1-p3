
import argparse
import os
import socket
import time

from packet import encode_packet, decode_packet
from rto import RTOEstimator

HOST = "127.0.0.1"
PORT = 5000
CHUNK_SIZE = 1024
WINDOW_SIZE = 4
MAX_RETRIES = 15
TRANSFER_ID = "transfer-1"


def send_file(filename, host=HOST, port=PORT):
    with open(filename, "rb") as file:
        data = file.read()

    chunks = [
        data[i:i + CHUNK_SIZE]
        for i in range(0, len(data), CHUNK_SIZE)
    ]
    total = len(chunks)

    estimator = RTOEstimator()
    outstanding = {}
    acknowledged = set()
    next_seq = 1
    base = 1

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.bind(("0.0.0.0", 0))
    client.settimeout(0.05)

    print(f"Sending {os.path.basename(filename)}: {total} chunks")

    try:
        # Selective Repeat: send packets within the sliding window.
        while base <= total:

            while (
                next_seq <= total
                and next_seq < base + WINDOW_SIZE
            ):
                packet = {
                    "type": "DATA",
                    "transfer_id": TRANSFER_ID,
                    "seq_num": next_seq,
                    "ack_num": None,
                    "payload": chunks[next_seq - 1],
                }

                encoded = encode_packet(packet)
                client.sendto(encoded, (host, port))

                outstanding[next_seq] = {
                    "encoded": encoded,
                    "sent_at": time.monotonic(),
                    "retries": 0,
                }

                print(f"Sent packet {next_seq}")
                next_seq += 1

            # Receive and process individual ACKs.
            try:
                raw, _ = client.recvfrom(65535)
                ack = decode_packet(raw)

                if ack["type"] != "ACK":
                    continue

                if ack["transfer_id"] != TRANSFER_ID:
                    continue

                seq = ack["ack_num"]

                if seq not in outstanding:
                    continue

                record = outstanding[seq]

                # Karn's algorithm: do not use retransmitted
                # packets to calculate RTT.
                if record["retries"] == 0:
                    rtt = time.monotonic() - record["sent_at"]
                    estimator.update(rtt)

                acknowledged.add(seq)
                del outstanding[seq]

                print(
                    f"ACK {seq}; RTO = "
                    f"{estimator.get_rto():.3f}s"
                )

                # Move the base past contiguous ACKs.
                while base in acknowledged:
                    base += 1

            except socket.timeout:
                pass
            except (ValueError, OSError) as error:
                print(f"Ignored invalid ACK: {error}")

            # Retransmit only packets whose timeout expired.
            now = time.monotonic()

            for seq, record in list(outstanding.items()):
                if now - record["sent_at"] >= estimator.get_rto():

                    if record["retries"] >= MAX_RETRIES:
                        raise TimeoutError(
                            f"Packet {seq} exceeded retry limit"
                        )

                    client.sendto(record["encoded"], (host, port))
                    record["sent_at"] = time.monotonic()
                    record["retries"] += 1

                    estimator.on_timeout()

                    print(
                        f"Timeout: retransmitted packet {seq}; "
                        f"RTO = {estimator.get_rto():.3f}s"
                    )

        # Send END and wait for its acknowledgement.
        end_packet = {
            "type": "END",
            "transfer_id": TRANSFER_ID,
            "seq_num": total,
            "ack_num": None,
            "payload": b"",
        }

        encoded_end = encode_packet(end_packet)
        end_ack_received = False
        deadline = time.monotonic() + 10.0

        while time.monotonic() < deadline:
            client.sendto(encoded_end, (host, port))

            end_wait = min(
                time.monotonic() + estimator.get_rto(),
                deadline,
            )

            while time.monotonic() < end_wait:
                client.settimeout(
                    max(0.01, end_wait - time.monotonic())
                )

                try:
                    raw, _ = client.recvfrom(65535)
                    ack = decode_packet(raw)

                    if (
                        ack["type"] == "ACK"
                        and ack["transfer_id"] == TRANSFER_ID
                        and ack["ack_num"] == total
                        and ack["seq_num"] == total + 1
                    ):
                        end_ack_received = True
                        break

                except socket.timeout:
                    break
                except (ValueError, OSError):
                    continue

            if end_ack_received:
                break

        if not end_ack_received:
            raise TimeoutError(
                "Receiver did not acknowledge END. "
                "Restart the receiver and try again."
            )

        print("File transfer completed successfully.")

    finally:
        client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Selective Repeat UDP sender"
    )
    parser.add_argument(
        "filename",
        nargs="?",
        default="sample.txt",
    )
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    if not os.path.isfile(args.filename):
        raise SystemExit(f"File not found: {args.filename}")

    send_file(args.filename, args.host, args.port)
