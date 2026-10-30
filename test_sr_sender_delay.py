
import socket
import subprocess
import sys
import threading
import time

from packet import encode_packet, decode_packet

HOST = "127.0.0.1"
PORT = 5000
TRANSFER_ID = "transfer-1"
ACK_DELAY = 0.15

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))
server.settimeout(0.5)

def delayed_ack(packet, address):
    time.sleep(ACK_DELAY)

    ack = {
        "type": "ACK",
        "transfer_id": TRANSFER_ID,
        "seq_num": 0,
        "ack_num": packet["seq_num"],
        "payload": b"",
    }

    server.sendto(encode_packet(ack), address)
    print(f"Sent delayed ACK {packet['seq_num']}")

def receiver():
    print("Delayed-ACK receiver listening...")

    while True:
        try:
            raw, address = server.recvfrom(65535)
        except socket.timeout:
            continue

        packet = decode_packet(raw)

        if packet["transfer_id"] != TRANSFER_ID:
            continue

        if packet["type"] == "DATA":
            seq = packet["seq_num"]
            print(f"Received DATA {seq}")

            threading.Thread(
                target=delayed_ack,
                args=(packet, address),
                daemon=True,
            ).start()

        elif packet["type"] == "END":
            total = packet["seq_num"]

            ack = {
                "type": "ACK",
                "transfer_id": TRANSFER_ID,
                "seq_num": total + 1,
                "ack_num": total,
                "payload": b"",
            }

            server.sendto(encode_packet(ack), address)
            print("Final END ACK sent")
            break

def main():
    thread = threading.Thread(target=receiver, daemon=True)
    thread.start()

    time.sleep(0.5)

    print("\nStarting sender with delayed ACKs...\n")

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

    values = []

    for line in result.stdout.splitlines():
        if "RTO =" in line:
            try:
                values.append(
                    float(line.split("RTO = ")[1].replace("s", ""))
                )
            except ValueError:
                pass

    if result.returncode == 0 and values:
        print("\nEXPERIMENT PASSED!")
        print(f"Artificial ACK delay: {ACK_DELAY}s")
        print(f"First observed RTO: {values[0]:.3f}s")
        print(f"Last observed RTO: {values[-1]:.3f}s")
        print("Sender completed successfully.")
    else:
        print("\nEXPERIMENT FAILED. Check the output.")

    server.close()

if __name__ == "__main__":
    main()
