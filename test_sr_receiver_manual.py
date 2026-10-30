
import hashlib
import os
import socket
import subprocess
import sys
import time

from packet import encode_packet, decode_packet

HOST = "127.0.0.1"
PORT = 5000
TRANSFER_ID = "receiver-test"
OUTPUT_FILE = "sr_test_output.txt"


def make_packet(packet_type, seq, payload=b""):
    return {
        "type": packet_type,
        "transfer_id": TRANSFER_ID,
        "seq_num": seq,
        "ack_num": None,
        "payload": payload,
    }


def send_and_receive(sock, packet, description):
    sock.sendto(encode_packet(packet), (HOST, PORT))
    raw, _ = sock.recvfrom(65535)
    ack = decode_packet(raw)
    print(f"{description}: ACK {ack['ack_num']}")
    return ack


def main():
    receiver = subprocess.Popen([
        sys.executable,
        "sr_receiver.py",
        "--host", HOST,
        "--port", str(PORT),
        "--output", OUTPUT_FILE,
    ])

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(3)

    try:
        time.sleep(1)

        chunk1 = b"FIRST-CHUNK-"
        chunk2 = b"SECOND-CHUNK"

        print("\nTEST 1: Out-of-order packet delivery")

        ack2 = send_and_receive(
            client,
            make_packet("DATA", 2, chunk2),
            "Sent packet 2 before packet 1",
        )

        assert ack2["ack_num"] == 2

        ack1 = send_and_receive(
            client,
            make_packet("DATA", 1, chunk1),
            "Sent packet 1",
        )

        assert ack1["ack_num"] == 1

        print("PASS: Out-of-order packets were acknowledged.")

        print("\nTEST 2: Duplicate packet handling")

        duplicate_ack = send_and_receive(
            client,
            make_packet("DATA", 2, chunk2),
            "Retransmitted duplicate packet 2",
        )

        assert duplicate_ack["ack_num"] == 2

        print("PASS: Duplicate packet was acknowledged again.")

        print("\nTEST 3: Lost final ACK recovery")

        end_packet = make_packet("END", 2)

        first_end_ack = send_and_receive(
            client,
            end_packet,
            "Sent END packet",
        )

        assert first_end_ack["seq_num"] == 3

        print("Simulating loss: ignoring the first END ACK.")

        time.sleep(0.2)

        second_end_ack = send_and_receive(
            client,
            end_packet,
            "Retransmitted END packet",
        )

        assert second_end_ack["seq_num"] == 3
        assert second_end_ack["ack_num"] == 2

        print("PASS: Receiver resent END ACK.")

        print("\nTEST 4: Verify reconstructed file")

        expected = chunk1 + chunk2

        with open(OUTPUT_FILE, "rb") as file:
            received = file.read()

        assert received == expected

        original_hash = hashlib.sha256(expected).hexdigest()
        received_hash = hashlib.sha256(received).hexdigest()

        assert original_hash == received_hash

        print("PASS: Received file contents match.")
        print("SHA256:", received_hash)

        print("\nALL 4 MANUAL TESTS PASSED!")

    except Exception as error:
        print("\nTEST FAILED:", error)
        raise

    finally:
        client.close()
        receiver.terminate()
        receiver.wait(timeout=5)

        if os.path.exists(OUTPUT_FILE):
            os.remove(OUTPUT_FILE)


if __name__ == "__main__":
    main()
