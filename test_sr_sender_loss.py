
import socket
import subprocess
import sys
import threading
import time

from packet import encode_packet, decode_packet

HOST = "127.0.0.1"
PORT = 5000
TRANSFER_ID = "transfer-1"

ack_dropped = False
test_passed = False


def simulated_receiver():
    global ack_dropped, test_passed

    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((HOST, PORT))
    server.settimeout(0.5)

    print("Simulated receiver listening...")

    try:
        while True:
            try:
                raw, sender_address = server.recvfrom(65535)
            except socket.timeout:
                continue

            packet = decode_packet(raw)

            if packet["transfer_id"] != TRANSFER_ID:
                continue

            if packet["type"] == "DATA":
                seq = packet["seq_num"]
                print(f"Received DATA packet {seq}")

                if seq == 2 and not ack_dropped:
                    ack_dropped = True
                    print("SIMULATED LOSS: Dropped ACK 2")
                    continue

                ack = {
                    "type": "ACK",
                    "transfer_id": TRANSFER_ID,
                    "seq_num": 0,
                    "ack_num": seq,
                    "payload": b"",
                }

                server.sendto(
                    encode_packet(ack),
                    sender_address
                )

                if seq == 2 and ack_dropped:
                    print("ACK 2 sent after retransmission")

            elif packet["type"] == "END":
                total = packet["seq_num"]

                ack = {
                    "type": "ACK",
                    "transfer_id": TRANSFER_ID,
                    "seq_num": total + 1,
                    "ack_num": total,
                    "payload": b"",
                }

                server.sendto(
                    encode_packet(ack),
                    sender_address
                )

                print("Final END ACK sent")
                test_passed = True
                break

    finally:
        server.close()


def main():
    receiver_thread = threading.Thread(
        target=simulated_receiver,
        daemon=True
    )

    receiver_thread.start()
    time.sleep(0.5)

    print("\nStarting actual Selective Repeat sender...\n")

    result = subprocess.run(
        [
            sys.executable,
            "sr_sender.py",
            "sample.txt",
            "--host",
            HOST,
            "--port",
            str(PORT),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    print("SENDER OUTPUT:")
    print(result.stdout)

    if result.stderr:
        print("ERROR OUTPUT:")
        print(result.stderr)

    receiver_thread.join(timeout=3)

    retransmitted = (
        "Timeout: retransmitted packet 2" in result.stdout
    )

    completed = (
        "File transfer completed successfully." in result.stdout
    )

    if result.returncode == 0 and ack_dropped and retransmitted and completed and test_passed:
        print("\nALL TESTS PASSED!")
        print("ACK 2 was deliberately dropped.")
        print("Sender retransmitted packet 2.")
        print("Transfer completed successfully.")
    else:
        print("\nTEST FAILED. Check the output above.")


if __name__ == "__main__":
    main()
